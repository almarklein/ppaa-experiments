"""
Create screenshots for the Sponza scene, to represent game-like images.

This uses PyGfx to render the scene at a few resolutions.
"""

import os

import numpy as np
from rendercanvas.auto import RenderCanvas, loop
from rendercanvas.offscreen import RenderCanvas as OffscreenRenderCanvas
import pygfx as gfx
from PIL import Image


# Create camera with predetermined state/position
camera = gfx.PerspectiveCamera(45, 1)
camera.set_state(
    {
        "position": (-5.67603933, 5.01692729, -1.94434201),
        "rotation": (-0.01978477, -0.80559809, -0.02388968, 0.59164987),
        "reference_up": (0.0, 1.0, 0.0),
        "fov": 45.0,
        "width": 10.0,
        "height": 10.0,
        "depth": 10.0,
        "maintain_aspect": True,
        "depth_range": None,
    }
)


def configure_scene_object(obj):
    obj.receive_shadow = True
    obj.cast_shadow = True


# Load scene
scene = gfx.Scene()
gltf_path = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Sponza/glTF/Sponza.gltf"
scene.add(*gfx.load_mesh(gltf_path, remote_ok=True))
scene.traverse(configure_scene_object)

# Add ambient light
scene.add(gfx.AmbientLight(intensity=0.15))

# Add the sun, midday direction
sunlight = gfx.DirectionalLight(intensity=4)
sunlight.local.position = -14.5, 31, 4.5
sunlight.target.local.position = 5.3, -1.4, -2.5
sunlight.cast_shadow = True
sunlight.shadow.camera.depth_range = (0, 250)
scene.add(sunlight)

# Add torches
for pos in [
    [-5.0, 1.12, -1.75],
    [-5.0, 1.12, 1.15],
    [3.8, 1.12, -1.75],
    [3.8, 1.12, 1.15],
]:
    torch = gfx.PointLight("#ff7700", decay=2.5)
    torch.local.position = pos
    torch.cast_shadow = True
    torch.shadow.camera.depth_range = (0.01, 200)
    torch.shadow.cull_mode = "none"
    torch.shadow.bias = 0.001
    scene.add(torch)

# Create offscreen canvas and renderer, configured without ssaa or ppaa
ocan = OffscreenRenderCanvas(pixel_ratio=1)
oren = gfx.renderers.WgpuRenderer(ocan, pixel_scale=1, ppaa="none")
ocan.request_draw(lambda: oren.render(scene, camera))

# Create screenshots
for scale_factor in (1, 2, 4):
    fname = "sponza.png" if scale_factor == 1 else f"sponzax{scale_factor}.png"
    filename = os.path.abspath(os.path.join(__file__, "..", "..", "images_src", fname))

    ocan.set_physical_size(512 * scale_factor, 512 * scale_factor)
    ocan.set_pixel_ratio(scale_factor)
    im = ocan.draw()
    im = np.asarray(im)
    im[:, :, 3] = 255
    Image.fromarray(im).convert("RGB").save(filename)


# Enter loop to show the scene interactively
if False:  # __name__ == "__main__":
    canvas = RenderCanvas(size=(800, 800), title="Sponza")
    renderer = gfx.renderers.WgpuRenderer(canvas)
    controller = gfx.FlyController(camera, register_events=renderer, speed=2)
    canvas.request_draw(lambda: renderer.render(scene, camera))
    loop.run()
