"""
Script to generate the images using the shaders.
Run this after changing a shader.
Then use the viewer to inspect the result.
"""

import os
import shutil

from PIL import Image
import numpy as np

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
    TEMPLATE_VARS = {**SSAAFullScreenRenderer.TEMPLATE_VARS, "scaleFactor": 4}


class Renderer_ssaax8(SSAAFullScreenRenderer):
    TEMPLATE_VARS = {**SSAAFullScreenRenderer.TEMPLATE_VARS, "scaleFactor": 8}


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


class Renderer_dlaa(WgslFullscreenRenderer):
    SHADER = "dlaa.wgsl"


class Renderer_fxaa2(WgslFullscreenRenderer):
    SHADER = "fxaa2.wgsl"


class Renderer_fxaa3(WgslFullscreenRenderer):
    SHADER = "fxaa3.wgsl"


class Renderer_ddaa1(WgslFullscreenRenderer):
    SHADER = "ddaa1.wgsl"


class Renderer_ddaa2(WgslFullscreenRenderer):
    SHADER = "ddaa2.wgsl"


# SMAA: Subpixel Morphological Anti Aliasing
# Would be nice (is available as wgsl in Bevy) but is multi-pass, and we focus on single-pass for now.
# https://github.com/bevyengine/bevy/blob/main/crates/bevy_anti_aliasing/src/smaa/smaa.wgsl


# CMAA2: Conservative Morphological Anti-Aliasing version 2
# https://github.com/GameTechDev/CMAA2
# https://www.intel.com/content/www/us/en/developer/articles/technical/conservative-morphological-anti-aliasing-20.html


# ---------------------------- Copy source images

for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
    name = fname.rpartition(".")[0]

    input_fname = os.path.join(src_images_dir, fname)
    output_fname = os.path.join(all_images_dir, fname)
    shutil.copy(input_fname, output_fname)

    # Hirez versions
    if fname in ["lines.png", "circles.png"]:
        for times in [2, 4, 8]:
            fname = f"{name}x{times}.png"
            input_fname = os.path.join(src_images_dir, fname)
            output_fname = os.path.join(all_images_dir, fname)
            shutil.copy(input_fname, output_fname)


# ---------------------------- Copy pre-obtained images

for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
    name = fname.rpartition(".")[0]
    fname = f"{name}_axaa.png"
    input_fname = os.path.join(pre_images_dir, fname)
    output_fname = os.path.join(all_images_dir, fname)

    shutil.copy(input_fname, output_fname)


# ----------------------------  Select experiment

# When using a subset of renderers, only these shaders are run, and they are many times and measure performance.
# Handy during development.

# Default no subset
exp_renderers = None

exp_renderers = [Renderer_fxaa3, Renderer_ddaa1, Renderer_ddaa2]


# ----------------------------  AA filtering

for Renderer in [
    # SSAA
    Renderer_ssaax2,
    Renderer_ssaax4,
    Renderer_ssaax8,
    # PPAA
    Renderer_dlaa,
    Renderer_fxaa2,
    Renderer_fxaa3,
    Renderer_ddaa1,
    Renderer_ddaa2,
]:
    if exp_renderers and Renderer not in exp_renderers:
        continue
    print(f"Rendering with {Renderer.__name__}")
    renderer = Renderer()
    hirez_flag = ""
    scale_factor = Renderer.TEMPLATE_VARS["scaleFactor"]
    if issubclass(Renderer, WgslFullscreenRenderer) and scale_factor > 1:
        hirez_flag = "x" + str(scale_factor).rstrip(".0")
    shadername = renderer.SHADER.split(".")[0] + hirez_flag

    for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]

        input_fname = os.path.join(all_images_dir, f"{name}{hirez_flag}.png")
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        if hirez_flag and not os.path.isfile(input_fname):
            continue

        print(f"    Generating {name} (in {output_fname})")

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if exp_renderers:
            renderer.render(im1, benchmark=True)
            print(f"    {renderer.last_time * 1000000:0.0f} us")
            renderer.render(im1, benchmark=True)
            print(f"    {renderer.last_time * 1000000:0.0f} us")

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
    renderer = Renderer()

    for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]
        shadername = "up_" + Renderer.TEMPLATE_VARS["filter"]

        input_fname = os.path.join(all_images_dir, fname)
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        print(f"    Generating {name} (in {output_fname})")

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if exp_renderers:
            renderer.render(im1, benchmark=True)
            print(f"    {renderer.last_time * 1000000:0.0f} us")
            renderer.render(im1, benchmark=True)
            print(f"    {renderer.last_time * 1000000:0.0f} us")

        Image.fromarray(im2).convert("RGB").save(output_fname)

print("Done!")
