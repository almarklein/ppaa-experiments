"""Utility to do a full-screen pass using a WGSL shader."""

import os
import time

import wgpu
import numpy as np


shader_dir = os.path.abspath(os.path.join(__file__, "..", "..", "wgsl"))

SHADER_TEMPLATE = """

struct VertexInput {
    @builtin(vertex_index) index: u32,
};

struct Varyings {
    @location(0) texcoord: vec2<f32>,
    @builtin(position) position: vec4<f32>,
};

struct FragmentOutput {
    @location(0) color: vec4<f32>,
};

@group(0) @binding(0)
var theScreenTexture: texture_2d<f32>;
@group(0) @binding(1)
var theScreenSampler: sampler;

@vertex
fn vsMmain(in: VertexInput) -> Varyings {
    var positions = array<vec2<f32>,4>(
        vec2<f32>(0.0, 1.0), vec2<f32>(0.0, 0.0), vec2<f32>(1.0, 1.0), vec2<f32>(1.0, 0.0)
    );
    let pos = positions[in.index];
    var varyings: Varyings;
    varyings.position = vec4<f32>(pos * 2.0 - 1.0, 0.0, 1.0);
    varyings.texcoord = vec2<f32>(pos.x, 1.0 - pos.y);
    return varyings;
}

AA_SHADER

const theScaleFactor : f32 = SCALE_FACTOR;

@fragment
fn fsMain(varyings: Varyings) -> FragmentOutput {
    var out : FragmentOutput;
    out.color = aaShader(theScreenTexture, theScreenSampler, varyings.texcoord, theScaleFactor);
    return out;
}
"""


class WgslFullscreenRenderer:
    SHADER = "noaa.wgsl"  # filename of the shader to invoke
    SCALE_FACTOR = 1

    def __init__(self):
        self._shader = open(os.path.join(shader_dir, self.SHADER), "rb").read().decode()

        self._device = None
        self._pipeline = None
        self._bind_group = None

    def _format_wgsl(self, wgsl):
        return wgsl.replace("SCALE_FACTOR", str(float(self.SCALE_FACTOR)))

    def render(self, image):
        assert image.ndim == 3 and image.shape[2] == 4, "Image must be rgba"
        h, w = image.shape[:2]

        if self._device is None:
            adapter = wgpu.gpu.request_adapter_sync()
            self._device = adapter.request_device_sync()
        device = self._device

        if self._pipeline is None:
            self._pipeline = self._create_pipeline()

        # Prepare textures

        tex1 = self._create_texture(
            w, h, wgpu.TextureUsage.COPY_DST | wgpu.TextureUsage.TEXTURE_BINDING
        )
        tex2 = self._create_texture(
            int(w / self.SCALE_FACTOR),
            int(h / self.SCALE_FACTOR),
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

        # Render!
        t0 = time.perf_counter()
        command_encoder = self._device.create_command_encoder()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[attachment],
            depth_stencil_attachment=None,
        )
        render_pass.set_pipeline(self._pipeline)
        render_pass.set_bind_group(0, bind_group, [], 0, 99)
        for i in range(100):
            render_pass.draw(4, 1)
        render_pass.end()
        device.queue.submit([command_encoder.finish()])

        device._poll_wait()  # wait
        t1 = time.perf_counter()
        self.last_time = t1 - t0

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
        wgsl = SHADER_TEMPLATE.replace("AA_SHADER", self._shader)
        wgsl = self._format_wgsl(wgsl)

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
