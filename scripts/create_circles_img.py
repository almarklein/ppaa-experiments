"""
Create an artificial image with various circles, in different colors
and on different backgrounds. This is to check the consistency under
different contrasts.
"""

import os
import webbrowser  # noqa

from PIL import Image, ImageDraw


SCALE_FACTOR = 1

# Image parameters
width, height = 480, 480
background_color = (255, 255, 255)

# Create a blank image
img = Image.new("RGB", (width * SCALE_FACTOR, height * SCALE_FACTOR), background_color)
draw = ImageDraw.Draw(img)


def draw_rectangle(xyxy, fill):
    xyxy = tuple(i * SCALE_FACTOR for i in xyxy)
    draw.rectangle(xyxy, fill=fill)


def draw_circle(center, line_color):
    center = SCALE_FACTOR * center[0], SCALE_FACTOR * center[1]
    radius1, width1 = 30 * SCALE_FACTOR, 4 * SCALE_FACTOR
    radius2, width2 = 20 * SCALE_FACTOR, 1 * SCALE_FACTOR
    radius3 = 10 * SCALE_FACTOR
    draw.circle(center, outline=line_color, radius=radius1, width=width1)
    draw.circle(center, outline=line_color, radius=radius2, width=width2)
    draw.circle(center, fill=line_color, radius=radius3)


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
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images", fname))
img.save(filename)
print(f"Image saved as '{fname}'")

# webbrowser.open(f"file://{filename}")
