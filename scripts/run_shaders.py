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

# SSAA


class SSAAFullScreenRenderer(WgslFullscreenRenderer):
    SHADER = "ssaa.wgsl"
    FILTER = "Mitchell"

    def _format_wgsl(self, wgsl):
        self._template_vars["filter"] = self.FILTER.lower()
        return super()._format_wgsl(wgsl)


class Renderer_wgsl_ssaax2(SSAAFullScreenRenderer):
    SCALE_FACTOR = 2


class Renderer_wgsl_ssaax4(SSAAFullScreenRenderer):
    SCALE_FACTOR = 4


class Renderer_wgsl_ssaax8(SSAAFullScreenRenderer):
    SCALE_FACTOR = 8


# Upsampling


class Renderer_wgsl_up_nearest(SSAAFullScreenRenderer):
    SCALE_FACTOR = 0.25
    FILTER = "nearest"


class Renderer_wgsl_up_triangle(SSAAFullScreenRenderer):
    SCALE_FACTOR = 0.25
    FILTER = "triangle"


class Renderer_wgsl_up_bspline(SSAAFullScreenRenderer):
    SCALE_FACTOR = 0.25
    FILTER = "bspline"


class Renderer_wgsl_up_mitchell(SSAAFullScreenRenderer):
    SCALE_FACTOR = 0.25
    FILTER = "mitchell"


class Renderer_wgsl_up_catmull(SSAAFullScreenRenderer):
    SCALE_FACTOR = 0.25
    FILTER = "catmull"


# PPAA filters


class Renderer_wgsl_fxaa2(WgslFullscreenRenderer):
    SHADER = "fxaa2.wgsl"


class Renderer_wgsl_fxaa311(WgslFullscreenRenderer):
    SHADER = "fxaa311.wgsl"


class Renderer_wgsl_ddaa2(WgslFullscreenRenderer):
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


# ----------------------------  AA filtering

for Renderer in [
    # # SSAA
    Renderer_wgsl_ssaax2,
    Renderer_wgsl_ssaax4,
    Renderer_wgsl_ssaax8,
    # # FXAA
    Renderer_wgsl_fxaa2,
    Renderer_wgsl_fxaa311,
    Renderer_wgsl_ddaa2,
]:
    print(f"Rendering with {Renderer.__name__}")
    renderer = Renderer()
    hirez_flag = ""
    if issubclass(Renderer, WgslFullscreenRenderer) and Renderer.SCALE_FACTOR > 1:
        hirez_flag = "x" + str(Renderer.SCALE_FACTOR)
    shadername = renderer.SHADER.split(".")[0] + hirez_flag

    for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]

        input_fname = os.path.join(all_images_dir, f"{name}{hirez_flag}.png")
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        if hirez_flag and not os.path.isfile(input_fname):
            continue

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if hasattr(renderer, "last_time"):
            renderer.render(im1)
            print(f"    {renderer.last_time * 1000:0.02f} ms")
            renderer.render(im1)
            print(f"    {renderer.last_time * 1000:0.02f} ms")

        Image.fromarray(im2).convert("RGB").save(output_fname)
        print(f"    Generated {output_fname}")


# ---------------------------- Upsampling

for Renderer in [
    # Renderer_wgsl_up_nearest,
    Renderer_wgsl_up_triangle,
    Renderer_wgsl_up_bspline,
    Renderer_wgsl_up_mitchell,
    Renderer_wgsl_up_catmull,
]:
    print(f"Upsampling with {Renderer.__name__}")
    renderer = Renderer()

    for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]
        shadername = f"up_{Renderer.FILTER}"

        input_fname = os.path.join(all_images_dir, fname)
        output_fname = os.path.join(all_images_dir, f"{name}_{shadername}.png")

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)

        if hasattr(renderer, "last_time"):
            renderer.render(im1)
            print(f"    {renderer.last_time * 1000:0.02f} ms")
            renderer.render(im1)
            print(f"    {renderer.last_time * 1000:0.02f} ms")

        Image.fromarray(im2).convert("RGB").save(output_fname)
        print(f"    Generated {output_fname}")

print("Done!")
