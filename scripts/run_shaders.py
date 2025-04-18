"""
Script to generate the images using the shaders.
Run this after changing a shader.
Then use the viewer to inspect the result.
"""

import os

from PIL import Image
import numpy as np

from renderer_glsl import GlslFullscreenRenderer
from renderer_wgsl import WgslFullscreenRenderer


images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images"))

# No aa


class Renderer_glsl_noaa(GlslFullscreenRenderer):
    SHADER = "noaa.glsl"


class Renderer_wgsl_noaa(WgslFullscreenRenderer):
    SHADER = "noaa.wgsl"


# Just smooth


class Renderer_glsl_smooth_aa(GlslFullscreenRenderer):
    SHADER = "smooth_aa.glsl"


class Renderer_wgsl_smooth_aa(WgslFullscreenRenderer):
    SHADER = "smooth_aa.wgsl"


# FXAA


class Renderer_wgsl_fxaa2(WgslFullscreenRenderer):
    SHADER = "fxaa2.wgsl"


class Renderer_glsl_fxaa2(GlslFullscreenRenderer):
    SHADER = "fxaa2.glsl"


class Renderer_wgsl_fxaa311(WgslFullscreenRenderer):
    SHADER = "fxaa311.wgsl"


class Renderer_glsl_axaa(GlslFullscreenRenderer):
    SHADER = "axaa.glsl"


# Other directional


class Renderer_wgsl_dlaa(WgslFullscreenRenderer):
    SHADER = "dlaa.wgsl"


# SMAA: Subpixel Morphological Anti Aliasing
# Would be nice (is available as wgsl in Bevy) but is multi-pass, and we focus on single-pass for now.
# https://github.com/bevyengine/bevy/blob/main/crates/bevy_anti_aliasing/src/smaa/smaa.wgsl


# CMAA2: Conservative Morphological Anti-Aliasing version 2
# https://github.com/GameTechDev/CMAA2
# https://www.intel.com/content/www/us/en/developer/articles/technical/conservative-morphological-anti-aliasing-20.html


# Almar's experiments


class Renderer_glsl_mcaa(GlslFullscreenRenderer):
    SHADER = "mcaa.glsl"


class Renderer_glsl_ddaa1(GlslFullscreenRenderer):
    SHADER = "ddaa1.glsl"


# ----------------------------

for Renderer in [
    # Stub
    Renderer_glsl_smooth_aa,
    Renderer_wgsl_smooth_aa,
    # FXAA
    Renderer_glsl_fxaa2,
    Renderer_wgsl_fxaa2,
    Renderer_wgsl_fxaa311,
    Renderer_glsl_axaa,
    # # Other directional
    Renderer_wgsl_dlaa,
    # # Almar's
    Renderer_glsl_mcaa,
    Renderer_glsl_ddaa1,
]:
    print(f"Rendering with {Renderer.__name__}")
    renderer = Renderer()
    hirez_flag = ""
    if issubclass(Renderer, WgslFullscreenRenderer) and Renderer.SCALE_FACTOR > 1:
        hirez_flag = "x" + str(Renderer.SCALE_FACTOR)

    for fname in ["lines.png", "circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]
        input_fname = os.path.join(images_dir, f"{name}{hirez_flag}.png")
        output_fname = os.path.join(images_dir, f"{name}_{renderer.SHADER}.png")

        if hirez_flag and not os.path.isfile(input_fname):
            continue

        im1 = Image.open(input_fname).convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)
        Image.fromarray(im2).convert("RGB").save(output_fname)
        print(f"    Wrote {output_fname}")

print("Done!")
