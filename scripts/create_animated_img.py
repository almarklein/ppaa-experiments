"""
Create an artificial animated image to study temporal effects.
"""

import os
import math
import webbrowser  # noqa

from PIL import Image  # , ImageDraw
import aggdraw


SCALE_FACTOR = 1

# Image parameters
width, height = 600, 600
background_color = (255, 255, 255)
line_color = (0, 0, 0)


def draw_star(draw, center, radius, count, line_width, angle=0):
    cx, cy = center[0] * SCALE_FACTOR, center[1] * SCALE_FACTOR
    radius = radius * SCALE_FACTOR

    angle_offset = angle
    angle_step = math.pi / count

    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)

    for i in range(count):
        angle = angle_offset + i * angle_step
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        x1 = cx - dx
        y1 = cy - dy
        x2 = cx + dx
        y2 = cy + dy
        draw.line((x1, y1, x2, y2), pen)


def draw_circles(draw, center, radius, line_width, angle=0):
    cx, cy = center[0] * SCALE_FACTOR, center[1] * SCALE_FACTOR
    radius = radius * SCALE_FACTOR

    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)

    cx += 10 * SCALE_FACTOR * math.cos(angle)
    cy += 10 * SCALE_FACTOR * math.sin(angle)

    radius += 10 * SCALE_FACTOR
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, pen)


def draw_fan(draw, x, y, line_width=1, distance=10, slant=0):
    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)

    for i, factor in enumerate((0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9)):
        x1 = x + i * distance
        x2 = x1 + factor * slant
        y1 = y
        y2 = y1 + 220

        x1, x2, y1, y2 = (
            x1 * SCALE_FACTOR,
            x2 * SCALE_FACTOR,
            y1 * SCALE_FACTOR,
            y2 * SCALE_FACTOR,
        )
        draw.line((x1, y1, x2, y2), pen)


def draw_frame(draw, t):
    angle1 = t * math.pi / 2
    draw_star(draw, center=(150, 150), radius=120, count=2, line_width=4, angle=angle1)
    draw_star(
        draw,
        center=(150, 150),
        radius=120,
        count=2,
        line_width=1,
        angle=angle1 + math.pi / 4,
    )

    angle2 = t * math.pi * 2
    draw_circles(draw, center=(450, 150), radius=80, line_width=4, angle=angle2)
    draw_circles(draw, center=(450, 150), radius=40, line_width=1, angle=angle2)

    offset = (t * 2 if t < 0.5 else (1.0 - t) * 2) * 10
    draw_fan(draw, 280, 350, 1, distance=-35, slant=-offset)
    draw_fan(draw, 320, 350, 4, distance=35, slant=offset)


# Draw all frames
images = []
N = 32
for i in range(N):
    img = Image.new(
        "RGB", (width * SCALE_FACTOR, height * SCALE_FACTOR), background_color
    )
    images.append(img)
    draw = aggdraw.Draw(img)
    draw.setantialias(False)
    draw_frame(draw, i / N)
    draw.flush()


if SCALE_FACTOR == 1:
    fname = "animated.png"
else:
    fname = f"animatedx{SCALE_FACTOR}.png"

# Save
main_image = images[0]
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images_src", fname))
main_image.save(filename, append_images=images[1:], loop=0, duration=0.04)
print(f"Image saved as '{fname}'")

# webbrowser.open(f"file://{filename}")
