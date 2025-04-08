"""
Script to generate the images using the shaders.
Run this after changing a shader.
Then use the viewer to inspect the result.
"""

from PIL import Image
import numpy as np

from scripts.renderer_glsl import GlslFullscreenRenderer
from scripts.renderer_wgsl import WgslFullscreenRenderer


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


# Other directional


class Renderer_wgsl_dlaa(WgslFullscreenRenderer):
    SHADER = "dlaa.wgsl"


# SMAA: Subpixel Morphological Anti Aliasing
# Would be nice (is available as wgsl in Bevy) but is multi-pass, and we focus on single-pass for now.
# https://github.com/bevyengine/bevy/blob/main/crates/bevy_anti_aliasing/src/smaa/smaa.wgsl


# CMAA2: Conservative Morphological Anti-Aliasing version 2
# https://github.com/GameTechDev/CMAA2
# https://www.intel.com/content/www/us/en/developer/articles/technical/conservative-morphological-anti-aliasing-20.html


# DDAA


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
    # Other directional
    Renderer_wgsl_dlaa,
    # DDAA
    Renderer_glsl_ddaa1,
]:
    print(f"Rendering with {Renderer.__name__}")
    renderer = Renderer()

    for fname in ["circles.png", "synthetic.png", "egypt.png"]:
        name = fname.rpartition(".")[0]
        output_fname = f"../images/{name}_{renderer.SHADER}.png"

        im1 = Image.open(f"images/{fname}").convert("RGBA")
        im1 = np.asarray(im1).copy()
        assert im1.dtype == np.uint8
        im1[:, :, 3] = 255  # set opaque, just in case

        im2 = renderer.render(im1)
        Image.fromarray(im2).convert("RGB").save(output_fname)
        print(f"    Wrote {output_fname}")

print("Done!")
