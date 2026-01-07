"""
Create screenshots of a typical line plot with markers.

This uses PyGfx to render the scene at a few resolutions.
"""

import os

import numpy as np
from rendercanvas.offscreen import RenderCanvas as OffscreenRenderCanvas
from rendercanvas.auto import RenderCanvas, loop
import pygfx as gfx
from pylinalg import vec_transform, vec_unproject
import imageio

scene = gfx.Scene()

background = gfx.Background.from_color("#fff")

grid = gfx.Grid(
    None,
    gfx.GridMaterial(
        major_step=1,
        minor_step=0,
        thickness_space="screen",
        major_thickness=1,
        major_color="#ddd",
        infinite=True,
    ),
    orientation="xy",
)
grid.local.z = -10

rulerx = gfx.Ruler(
    tick_side="right",
    tick_marker="tick_left",
    min_tick_distance=50,
    color="#000",
    alpha_mode="blend",
)
rulery = gfx.Ruler(
    tick_side="left",
    tick_marker="tick_right",
    min_tick_distance=40,
    color="#000",
    alpha_mode="blend",
)

x = np.linspace(20, 980, 50, dtype=np.float32)
y1 = np.sin(x / 40) * 4
y2 = np.cos(x / 50) * 3
positions1 = np.column_stack([x, y1, np.zeros_like(x)])
positions2 = np.column_stack([x, y2, np.zeros_like(x)])

line1 = gfx.Line(
    gfx.Geometry(positions=positions1),
    gfx.LineMaterial(thickness=4.0, color="#77f", alpha_mode="blend"),
)
markers1 = gfx.Points(
    gfx.Geometry(positions=positions1),
    gfx.PointsMarkerMaterial(
        size=10.0, marker="diamond", color="#77f", alpha_mode="blend"
    ),
)
line2 = gfx.Line(
    gfx.Geometry(positions=positions2),
    gfx.LineMaterial(thickness=4.0, color="#3c3", alpha_mode="blend"),
)
markers2 = gfx.Points(
    gfx.Geometry(positions=positions2),
    gfx.PointsMarkerMaterial(
        size=10.0, marker="circle", color="#3c3", alpha_mode="blend"
    ),
)
scene.add(background, grid, rulerx, rulery, line1, markers1, line2, markers2)

camera = gfx.OrthographicCamera(maintain_aspect=False)
camera.show_object(scene, match_aspect=True, scale=1.2)


def map_screen_to_world(pos, viewport_size):
    # first convert position to NDC
    x = pos[0] / viewport_size[0] * 2 - 1
    y = -(pos[1] / viewport_size[1] * 2 - 1)
    pos_ndc = (x, y, 0)

    pos_ndc += vec_transform(camera.world.position, camera.camera_matrix)
    # unproject to world space
    pos_world = vec_unproject(pos_ndc[:2], camera.camera_matrix)

    return pos_world


def animate(renderer):
    canvas = renderer.target

    # get range of screen space
    xmin, ymin = 0, renderer.logical_size[1]
    xmax, ymax = renderer.logical_size[0], 0

    world_xmin, world_ymin, _ = map_screen_to_world((xmin, ymin), renderer.logical_size)
    world_xmax, world_ymax, _ = map_screen_to_world((xmax, ymax), renderer.logical_size)

    # set start and end positions of rulers
    rulerx.start_pos = world_xmin, 0, 10
    rulerx.end_pos = world_xmax, 0, 10

    rulerx.start_value = rulerx.start_pos[0]

    statsx = rulerx.update(camera, canvas.get_logical_size())

    rulery.start_pos = 0, world_ymin, 10
    rulery.end_pos = 0, world_ymax, 10

    rulery.start_value = rulery.start_pos[1]
    statsy = rulery.update(camera, canvas.get_logical_size())

    major_step_x, major_step_y = statsx["tick_step"], statsy["tick_step"]
    grid.material.major_step = major_step_x, major_step_y
    grid.material.minor_step = 0.2 * major_step_x, 0.2 * major_step_y

    renderer.render(scene, camera)


# Create offscreen canvas and renderer, configured without ssaa or ppaa
ocan = OffscreenRenderCanvas(pixel_ratio=1)
oren = gfx.renderers.WgpuRenderer(ocan, pixel_scale=1, ppaa="none")
ocan.request_draw(lambda: animate(oren))

# Create screenshots
for scale_factor in (1, 2, 4):
    fname = "plot.png" if scale_factor == 1 else f"plotx{scale_factor}.png"
    filename = os.path.abspath(os.path.join(__file__, "..", "..", "images_src", fname))

    ocan.set_physical_size(640 * scale_factor, 480 * scale_factor)
    ocan.set_pixel_ratio(scale_factor)
    im = ocan.draw()
    imageio.imwrite(filename, im)


if __name__ == "__main__":
    canvas = RenderCanvas()
    renderer = gfx.WgpuRenderer(canvas)
    controller = gfx.PanZoomController(camera, register_events=renderer)
    canvas.request_draw(lambda: animate(renderer))
    loop.run()
