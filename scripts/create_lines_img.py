"""
Create an artificial image with line-like objects under different angles
and with different thicknesses.

Since I'm planning to use an AA filter in Pygfx, which is also used
for scientific plotting, the filter must behave well for e.g. high-contrast line data.
"""

import os
import math
import webbrowser  # noqa

from PIL import Image, ImageDraw
import aggdraw


SCALE_FACTOR = 1

# Image parameters
width, height = 600, 600
background_color = (255, 255, 255)
line_color = (0, 0, 0)

# Create a blank image
img = Image.new("RGB", (width * SCALE_FACTOR, height * SCALE_FACTOR), background_color)
draw = aggdraw.Draw(img)  # like ImageDraw.Draw(img), but with subpixel support
draw.setantialias(False)  # but disable aa!


def draw_star(draw, center, radius, count, line_width, circle_width):
    cx, cy = center[0] * SCALE_FACTOR, center[1] * SCALE_FACTOR
    radius = radius * SCALE_FACTOR
    angle_step = math.pi / count

    line_pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)
    circle_pen = aggdraw.Pen(line_color, circle_width * SCALE_FACTOR)

    for i in range(count):
        angle = i * angle_step
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        x1 = cx - dx
        y1 = cy - dy
        x2 = cx + dx
        y2 = cy + dy
        draw.line((x1, y1, x2, y2), line_pen)

    # Draw outer circle
    radius += 10 * SCALE_FACTOR
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, circle_pen)


def draw_cubes_and_circles(draw, x, y, line_width):
    x, y = x * SCALE_FACTOR, y * SCALE_FACTOR

    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)
    brush = aggdraw.Brush(line_color)

    d = 25 * SCALE_FACTOR
    for i in range(0, 20, 2):
        w = i * SCALE_FACTOR
        if line_width == 1:
            draw.rectangle([x, y, x + w, y + w], pen)
            draw.ellipse(
                (x, y+d, x + w, y + d + w),
                pen
            )
        else:
            draw.rectangle([x, y, x + w, y + w], pen, brush)
            draw.ellipse((x, y+d, x + w, y + d + w), pen, brush)
        x += d


def draw_fan(draw, x, y, line_width=1):

    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)

    for i, dy in enumerate((2, 5, 10)):
        x1 = x
        x2 = x + 250
        y1 = y + i * 10
        y2 = y1 + dy

        x1, x2, y1, y2 = (
            x1 * SCALE_FACTOR,
            x2 * SCALE_FACTOR,
            y1 * SCALE_FACTOR,
            y2 * SCALE_FACTOR,
        )
        draw.line((x1, y1, x2, y2), pen)


def draw_grid(draw, x, y, deg=0, cell_size=10, line_width=1):
    angle = deg * math.pi / 180
    d = cell_size * 3

    pen = aggdraw.Pen(line_color, line_width * SCALE_FACTOR)

    for ix in range(7):
        dx1 = -d + ix * cell_size
        dx2 = dx1
        dy1 = -d
        dy2 = d
        x1 = x + math.cos(angle) * dx1 + math.sin(angle) * dy1
        x2 = x + math.cos(angle) * dx2 + math.sin(angle) * dy2
        y1 = y + math.cos(angle) * dy1 - math.sin(angle) * dx1
        y2 = y + math.cos(angle) * dy2 - math.sin(angle) * dx2
        x1, x2, y1, y2 = (
            x1 * SCALE_FACTOR,
            x2 * SCALE_FACTOR,
            y1 * SCALE_FACTOR,
            y2 * SCALE_FACTOR,
        )
        draw.line((x1, y1, x2, y2), pen)

    for iy in range(7):
        dx1 = -d
        dx2 = d
        dy1 = -d + iy * cell_size
        dy2 = dy1
        x1 = x + math.cos(angle) * dx1 + math.sin(angle) * dy1
        x2 = x + math.cos(angle) * dx2 + math.sin(angle) * dy2
        y1 = y + math.cos(angle) * dy1 - math.sin(angle) * dx1
        y2 = y + math.cos(angle) * dy2 - math.sin(angle) * dx2
        x1, x2, y1, y2 = (
            x1 * SCALE_FACTOR,
            x2 * SCALE_FACTOR,
            y1 * SCALE_FACTOR,
            y2 * SCALE_FACTOR,
        )
        draw.line((x1, y1, x2, y2), pen)



# Left: 1px lines and circle
draw_star(draw, center=(150.3, 150.3), radius=120, count=32, line_width=1, circle_width=1)
draw_cubes_and_circles(draw, 20, 310, line_width=1)

# Right: 4px lines and circle
draw_star(draw, center=(450, 150), radius=120, count=16, line_width=4, circle_width=4)
draw_cubes_and_circles(draw, 320, 310, line_width=4)

# Fans
draw_fan(draw, 20, 380, 1)
draw_fan(draw, 320, 380, 4)

for i, deg in enumerate((0, 1, 5, 10, 20, 45)):
    draw_grid(draw, 50 + i * 100, 470, deg=deg, cell_size=10)
    draw_grid(draw, 50 + i * 100, 540, deg=deg, cell_size=5)
    draw_grid(draw, 50 + i * 100, 580, deg=deg, cell_size=2)



if SCALE_FACTOR == 1:
    fname = "lines.png"
else:
    fname = f"linesx{SCALE_FACTOR}.png"

# Save
draw.flush()
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images_src", fname))
img.save(filename)
print(f"Image saved as '{fname}'")

# webbrowser.open(f"file://{filename}")
