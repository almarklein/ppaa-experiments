"""Utility to do a full-screen pass using a WGSL shader."""

import os
import time

import jinja2
import wgpu
import numpy as np


shader_dir = os.path.abspath(os.path.join(__file__, "..", "..", "wgsl"))


jinja_env = jinja2.Environment(
    block_start_string="{$",
    block_end_string="$}",
    variable_start_string="{{",
    variable_end_string="}}",
    line_statement_prefix="$$",
    undefined=jinja2.StrictUndefined,
)


def apply_templating(code, **kwargs):
    t = jinja_env.from_string(code)
    try:
        return t.render(**kwargs)
    except jinja2.UndefinedError as err:
        raise ValueError(f"Cannot compose shader: {err.args[0]}") from None


SHADER_TEMPLATE = """

struct VertexInput {
    @builtin(vertex_index) index: u32,
};
struct Varyings {
    @location(0) texCoord: vec2<f32>,
    @builtin(position) position: vec4<f32>,
};

@vertex
fn vs_main(in: VertexInput) -> Varyings {
    var positions = array<vec2<f32>,4>(
        vec2<f32>(0.0, 1.0), vec2<f32>(0.0, 0.0), vec2<f32>(1.0, 1.0), vec2<f32>(1.0, 0.0)
    );
    let pos = positions[in.index];
    var varyings: Varyings;
    varyings.texCoord = vec2<f32>(pos.x, 1.0 - pos.y);
    varyings.position = vec4<f32>(pos * 2.0 - 1.0, 0.0, 1.0);
    return varyings;
}

@group(0) @binding(0)
var colorTex: texture_2d<f32>;
@group(0) @binding(1)
var texSampler: sampler;

"""


class WgslFullscreenRenderer:
    SHADER = "noaa.wgsl"  # filename of the shader to invoke

    TEMPLATE_VARS = {"scaleFactor": 1}

    def __init__(self, **template_vars):
        self._shader = open(os.path.join(shader_dir, self.SHADER), "rb").read().decode()

        self._device = None
        self._pipeline = None
        self._bind_group = None
        self._template_vars = template_vars

    def _format_wgsl(self, wgsl):
        template_vars = {}
        template_vars.update(self.TEMPLATE_VARS)
        template_vars.update(self._template_vars)
        return apply_templating(wgsl, **template_vars)

    def render(self, image, benchmark=None):
        assert image.ndim == 3 and image.shape[2] == 4, "Image must be rgba"
        h, w = image.shape[:2]
        scale_factor = self.TEMPLATE_VARS["scaleFactor"]

        if self._device is None:
            adapter = wgpu.gpu.request_adapter_sync()
            self._device = adapter.request_device_sync(
                required_features=[wgpu.FeatureName.timestamp_query]
            )
            self._query_set = self._device.create_query_set(
                type=wgpu.QueryType.timestamp, count=2
            )
            self._query_buf = self._device.create_buffer(
                size=8 * self._query_set.count,
                usage=wgpu.BufferUsage.QUERY_RESOLVE | wgpu.BufferUsage.COPY_SRC,
            )

        device = self._device

        if self._pipeline is None:
            self._pipeline = self._create_pipeline()

        # Prepare textures

        tex1 = self._create_texture(
            w, h, wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING
        )
        tex2 = self._create_texture(
            int(w / scale_factor),
            int(h / scale_factor),
            wgpu.TextureUsage.COPY_SRC | wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        sampler = device.create_sampler(
            address_mode_u=wgpu.AddressMode.clamp_to_edge,
            address_mode_v=wgpu.AddressMode.clamp_to_edge,
            address_mode_w=wgpu.AddressMode.clamp_to_edge,
            mag_filter=wgpu.FilterMode.linear,
            min_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.linear,
        )

        # Prepare bind group
        bind_group_entries = [
            {"binding": 0, "resource": tex1.create_view()},
            {"binding": 1, "resource": sampler},
        ]
        bind_group = self._device.create_bind_group(
            layout=self._pipeline.get_bind_group_layout(0), entries=bind_group_entries
        )

        # Prepare target
        attachment = {
            "view": tex2.create_view(),
            "resolve_target": None,
            "clear_value": (0, 0, 0, 0),
            "load_op": wgpu.LoadOp.clear,
            "store_op": wgpu.StoreOp.store,
        }

        # Upload
        self._write_texture(tex1, image)

        niters = 100 if benchmark else 1

        # Allow the GPU to breath, resulting in lower stds
        if benchmark:
            time.sleep(0.1)

        # Render!
        times = []
        for i in range(niters):
            command_encoder = self._device.create_command_encoder()

            render_pass = command_encoder.begin_render_pass(
                color_attachments=[attachment],
                depth_stencil_attachment=None,
                timestamp_writes={
                    "query_set": self._query_set,
                    "beginning_of_pass_write_index": 0,
                    "end_of_pass_write_index": 1,
                },
            )
            render_pass.set_pipeline(self._pipeline)
            render_pass.set_bind_group(0, bind_group, [], 0, 99)
            render_pass.draw(4, 1)
            render_pass.end()

            command_encoder.resolve_query_set(
                query_set=self._query_set,
                first_query=0,
                query_count=2,
                destination=self._query_buf,
                destination_offset=0,
            )

            device.queue.submit([command_encoder.finish()])

            timestamps = device.queue.read_buffer(self._query_buf).cast("Q").tolist()
            times.append(timestamps[1] - timestamps[0])  # in ns

        if benchmark:
            times.sort()
            times = [int(t / 1000) for t in times]  # turn to us and make int

            times = times[niters // 4 : -niters // 4]

            # self.last_time = f"mean: {np.mean(times):0.0f},  median: {times[len(times) // 2]} us,  std: {np.std(times):0.0f}, range: [{times[0]}, {times[-1]}]"
            self.last_time = f"{np.mean(times):0.0f} ± {np.std(times):0.0f} us"

        return self._read_texture(tex2)

    def _create_pipeline(self):
        binding_layout = [
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                    "multisampled": False,
                },
            },
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {},
            },
        ]

        targets = [
            {
                "format": "rgba8unorm",
                "blend": {
                    "color": {
                        "operation": wgpu.BlendOperation.add,
                        "src_factor": wgpu.BlendFactor.src_alpha,
                        "dst_factor": wgpu.BlendFactor.one_minus_src_alpha,
                    },
                    "alpha": {
                        "operation": wgpu.BlendOperation.add,
                        "src_factor": wgpu.BlendFactor.src_alpha,
                        "dst_factor": wgpu.BlendFactor.one_minus_src_alpha,
                    },
                },
            },
        ]

        return self._create_full_quad_pipeline(targets, binding_layout)

    def _create_full_quad_pipeline(self, targets, binding_layout):
        device = self._device

        # Get bind group layout
        bind_group_layout = device.create_bind_group_layout(entries=binding_layout)

        # Get render pipeline
        wgsl = SHADER_TEMPLATE + self._shader
        wgsl = self._format_wgsl(wgsl)

        with open(os.path.join(shader_dir, "tmp.wgsl"), "wb") as f:
            f.write(wgsl.encode())

        shader_module = device.create_shader_module(code=wgsl)

        pipeline_layout = device.create_pipeline_layout(
            bind_group_layouts=[bind_group_layout]
        )

        render_pipeline = device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={
                "module": shader_module,
                "entry_point": None,
                "buffers": [],
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_strip,
                "strip_index_format": wgpu.IndexFormat.uint32,
            },
            depth_stencil=None,
            multisample=None,
            fragment={
                "module": shader_module,
                "entry_point": None,
                "targets": targets,
            },
        )

        return render_pipeline

    def _create_texture(self, w, h, usage):
        return self._device.create_texture(
            **{
                "size": (w, h, 1),
                "mip_level_count": 1,
                "sample_count": 1,
                "dimension": "2d",
                "format": "rgba8unorm",
                "usage": usage,
            }
        )

    def _write_texture(self, texture, image):
        h, w = image.shape[:2]
        self._device.queue.write_texture(
            {
                "texture": texture,
                "mip_level": 0,
                "origin": (0, 0, 0),
            },
            image,
            {
                "offset": 0,
                "bytes_per_row": w * 4,
                "rows_per_image": h,
            },
            (w, h, 1),
        )

    def _read_texture(self, texture):
        w, h = texture.size[:2]
        data = self._device.queue.read_texture(
            {
                "texture": texture,
                "mip_level": 0,
                "origin": (0, 0, 0),
            },
            {
                "offset": 0,
                "bytes_per_row": 4 * w,
                "rows_per_image": h,
            },
            (w, h, 1),
        )
        return np.frombuffer(data, np.uint8).reshape(h, w, 4)
