"""
Create an artificial image with various circles, in different colors
and on different backgrounds. This is to check the consistency under
different contrasts.
"""

import os
import webbrowser  # noqa

from PIL import Image, ImageDraw
import aggdraw


SCALE_FACTOR = 1

# Image parameters
width, height = 480, 480
background_color = (255, 255, 255)

# Create a blank image
img = Image.new("RGB", (width * SCALE_FACTOR, height * SCALE_FACTOR), background_color)
draw = aggdraw.Draw(img)  # like ImageDraw.Draw(img), but with subpixel support
draw.setantialias(False)  # but disable aa!


def draw_rectangle(xyxy, fill):
    xyxy = tuple(i * SCALE_FACTOR for i in xyxy)
    draw.rectangle(xyxy, None, aggdraw.Brush(fill))


def draw_circle(center, line_color):
    center = SCALE_FACTOR * center[0], SCALE_FACTOR * center[1]
    r1, width1 = 30 * SCALE_FACTOR, 4 * SCALE_FACTOR
    r2, width2 = 20 * SCALE_FACTOR, 1 * SCALE_FACTOR
    r3 = 10 * SCALE_FACTOR

    coords1 = center[0] - r1, center[1] - r1, center[0]+r1, center[1]+r1
    coords2 = center[0] - r2, center[1] - r2, center[0]+r2, center[1]+r2
    coords3 = center[0] - r3, center[1] - r3, center[0]+r3, center[1]+r3

    draw.ellipse(coords1, aggdraw.Pen(line_color, width1))
    draw.ellipse(coords2, aggdraw.Pen(line_color, width2))
    draw.ellipse(coords3, None, aggdraw.Brush(line_color))


def draw_circles(center):
    cx, cy = center
    d = 75
    draw_circle((cx - d, cy - d), (0, 0, 0))
    draw_circle((cx, cy - d), (127, 127, 127))
    draw_circle((cx + d, cy - d), (255, 255, 255))
    draw_circle((cx - d, cy), (255, 0, 0))
    draw_circle((cx, cy), (0, 255, 0))
    draw_circle((cx + d, cy), (0, 0, 255))
    draw_circle((cx - d, cy + d), (0, 255, 255))
    draw_circle((cx, cy + d), (255, 0, 255))
    draw_circle((cx + d, cy + d), (255, 255, 0))


draw_rectangle((0, 0, 240, 240), (255, 255, 255))
draw_circles((120, 120))

draw_rectangle((240, 0, 480, 240), (0, 0, 0))
draw_circles((120 + 240, 120))

draw_rectangle((0, 240, 240, 480), (170, 170, 170))
draw_circles((120, 120 + 240))

draw_rectangle((240, 240, 480, 480), (85, 85, 85))
draw_circles((120 + 240, 120 + 240))

if SCALE_FACTOR == 1:
    fname = "circles.png"
else:
    fname = f"circlesx{SCALE_FACTOR}.png"

# Save
draw.flush()
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images_src", fname))
img.save(filename)
print(f"Image saved as '{fname}'")

# webbrowser.open(f"file://{filename}")
