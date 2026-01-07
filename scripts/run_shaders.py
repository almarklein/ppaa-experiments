"""
Script to generate the images using the shaders.
Run this after changing a shader.
Then use the viewer to inspect the result.
Also performs benchmark  (set ``exp_renderers``).
"""

import os
import json
import shutil

from PIL import Image
import numpy as np
import wgpu

from renderer_wgsl import WgslFullscreenRenderer


src_images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images_src"))
pre_images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images_pre"))
all_images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images_all"))

os.makedirs(all_images_dir, exist_ok=True)

images_text = """
Flat directory of all images. These are copied here from other locations, and
produced by running shaders. You can delete this dir and run run_shaders.py
to re-populate it.
"""

with open(os.path.join(all_images_dir, "README.md"), "bw") as f:
    f.write(images_text.encode())


# ---------------------------- Shaders classes


class SSAAFullScreenRenderer(WgslFullscreenRenderer):
    SHADER = "ssaa.wgsl"
    TEMPLATE_VARS = {
        "scaleFactor": 1,
        "filter": "mitchell",
        "extraKernelSupport": None,
        "optScale2": True,
        "optCorners": True,
    }


# SSAA


class Renderer_ssaax2(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {**SSAAFullScreenRenderer.TEMPLATE_VARS, "scaleFactor": 2}


class Renderer_ssaax4(SSAAFullScreenRenderer):
    # Note: 4 is the largest scale factor for which kernels are not truncated.
    TEMPLATE_VARS = {**SSAAFullScreenRenderer.TEMPLATE_VARS, "scaleFactor": 4}


# Upsampling


class Renderer_up_nearest(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {
        **SSAAFullScreenRenderer.TEMPLATE_VARS,
        "scaleFactor": 0.25,
        "filter": "nearest",
    }


class Renderer_up_triangle(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {
        **SSAAFullScreenRenderer.TEMPLATE_VARS,
        "scaleFactor": 0.25,
        "filter": "tent",
    }


class Renderer_up_bspline(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {
        **SSAAFullScreenRenderer.TEMPLATE_VARS,
        "scaleFactor": 0.25,
        "filter": "bspline",
    }


class Renderer_up_mitchell(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {
        **SSAAFullScreenRenderer.TEMPLATE_VARS,
        "scaleFactor": 0.25,
        "filter": "mitchell",
    }


class Renderer_up_catmull(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {
        **SSAAFullScreenRenderer.TEMPLATE_VARS,
        "scaleFactor": 0.25,
        "filter": "catmull",
    }


# PPAA filters


class Renderer_null(WgslFullscreenRenderer):
    SHADER = "noaa.wgsl"


class Renderer_blur(WgslFullscreenRenderer):
    SHADER = "blur.wgsl"


class Renderer_dlaa(WgslFullscreenRenderer):
    SHADER = "dlaa.wgsl"


class Renderer_fxaa2(WgslFullscreenRenderer):
    SHADER = "fxaa2.wgsl"


class Renderer_fxaa3c(WgslFullscreenRenderer):
    SHADER = "fxaa3c.wgsl"


class Renderer_fxaa3d(WgslFullscreenRenderer):
    SHADER = "fxaa3d.wgsl"


class Renderer_ddaa1(WgslFullscreenRenderer):
    SHADER = "ddaa1.wgsl"


class Renderer_ddaa2(WgslFullscreenRenderer):
    SHADER = "ddaa2.wgsl"

    TEMPLATE_VARS = {
        **WgslFullscreenRenderer.TEMPLATE_VARS,
        # "EDGE_STEP_LIST": [],
        "EDGE_STEP_LIST": [3, 3, 3, 3, 3],
    }


# SMAA: Subpixel Morphological Anti Aliasing
# Would be nice (is available as wgsl in Bevy) but is multi-pass, and we focus on single-pass for now.
# https://github.com/bevyengine/bevy/blob/main/crates/bevy_anti_aliasing/src/smaa/smaa.wgsl


# CMAA2: Conservative Morphological Anti-Aliasing version 2
# https://github.com/GameTechDev/CMAA2
# https://www.intel.com/content/www/us/en/developer/articles/technical/conservative-morphological-anti-aliasing-20.html


# ---------------------------- Copy source images

for fname in ["lines.png", "circles.png", "plot.png", "sponza.png", "synthetic.png"]:
    name = fname.rpartition(".")[0]

    input_fname = os.path.join(src_images_dir, fname)
    output_fname = os.path.join(all_images_dir, fname)
    shutil.copy(input_fname, output_fname)

    # Hirez versions
    if fname in ["lines.png", "circles.png"]:
        for times in [2, 4]:
            fname = f"{name}x{times}.png"
            input_fname = os.path.join(src_images_dir, fname)
            output_fname = os.path.join(all_images_dir, fname)
            shutil.copy(input_fname, output_fname)


# ----------------------------  Select experiment

# When using a subset of renderers, only these shaders are run, and they are many times and measure performance.
# Handy during development.

benchmarks = {}

# Default no subset
exp_renderers = None

exp_renderers = [
    # Renderer_null,
    Renderer_blur,
    Renderer_ssaax2,
    Renderer_ssaax4,
    Renderer_fxaa3c,
    Renderer_fxaa3d,
    Renderer_ddaa1,
    Renderer_ddaa2,
]


image_names = [
    "lines.png",
    "circles.png",
    "plot.png",
    "sponza.png",
    "synthetic.png",
]


# ---------------------------- Select adapter


adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")

# adapters = wgpu.gpu.enumerate_adapters_sync()
# for i, a in enumerate(adapters):
#     print(f"{i}: {a.summary}")
# adapter = adapters[1]

print("Running on", adapter.summary)
print()

##

# ----------------------------  AA filtering

for Renderer in [
    Renderer_null,
    Renderer_blur,
    # SSAA
    Renderer_ssaax2,
    Renderer_ssaax4,
    # PPAA
    Renderer_dlaa,
    Renderer_fxaa2,
    Renderer_fxaa3c,
    Renderer_fxaa3d,
    Renderer_ddaa1,
    Renderer_ddaa2,
]:
    if exp_renderers and Renderer not in exp_renderers:
        continue
    print(f"Rendering with {Renderer.__name__}")
    renderer = Renderer(adapter)
    hirez_flag = ""
    scale_factor = Renderer.TEMPLATE_VARS["scaleFactor"]
    if issubclass(Renderer, WgslFullscreenRenderer) and scale_factor > 1:
        hirez_flag = "x" + str(scale_factor).rstrip(".0")
    shadername = renderer.SHADER.split(".")[0] + hirez_flag

    for fname in image_names:
        name = fname.rpartition(".")[0]

        input_fname = os.path.join(all_images_dir, f"{name}{hirez_flag}.png")
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        if hirez_flag and not os.path.isfile(input_fname):
            continue

        info = f"    Generating {name} ({os.path.basename(output_fname)})"
        print(info, end="")

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if exp_renderers:
            renderer.render(im1, benchmark=True)
            print(" " * (50 - len(info)) + renderer.last_time)
            d = benchmarks.setdefault(Renderer.__name__.partition("_")[2], {})
            d[name] = min(d.get(name, 9999999), renderer._last_us)
        else:
            print("done")

        Image.fromarray(im2).convert("RGB").save(output_fname)


# ---------------------------- Upsampling

for Renderer in [
    Renderer_up_nearest,
    Renderer_up_triangle,
    Renderer_up_bspline,
    Renderer_up_mitchell,
    Renderer_up_catmull,
]:
    if exp_renderers and Renderer not in exp_renderers:
        continue
    print(f"Upsampling with {Renderer.__name__}")
    renderer = Renderer(adapter)

    for fname in image_names:
        name = fname.rpartition(".")[0]
        shadername = "up_" + Renderer.TEMPLATE_VARS["filter"]

        input_fname = os.path.join(all_images_dir, fname)
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        info = f"    Generating {name} (in {os.path.basename(output_fname)})"
        print(info, end="")

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if exp_renderers:
            renderer.render(im1, benchmark=True)
            print(" " * (50 - len(info)) + renderer.last_time)
            d = benchmarks.setdefault(Renderer.__name__.partition("_")[2], {})
            d[name] = min(d.get(name, 9999999), renderer.last_us)
        else:
            print("done")

        Image.fromarray(im2).convert("RGB").save(output_fname)


print("Done!")
if exp_renderers:
    alt_benchmarks = benchmarks

    ref = "blur"
    if ref in benchmarks:
        alt_benchmarks = {}
        null_alg = benchmarks[ref]
        for alg in benchmarks:
            alt_benchmarks[alg] = {}
            for name in benchmarks[alg]:
                alt_benchmarks[alg][name] = int(
                    100 * benchmarks[alg][name] / null_alg[name]
                )
    # print(json.dumps(benchmarks, indent=4))
    print(json.dumps(alt_benchmarks, indent=4))
