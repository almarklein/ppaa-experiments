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


SCALE_FACTOR = 1
FSAA_FACTOR = SCALE_FACTOR**2

# Image parameters
width, height = 600, 360
background_color = (255, 255, 255)
line_color = (0, 0, 0)

# Create a blank image
img = Image.new("RGB", (width * SCALE_FACTOR, height * SCALE_FACTOR), background_color)
draw = ImageDraw.Draw(img)


def draw_star(draw, center, radius, count, line_width, circle_width):
    cx, cy = center[0] * SCALE_FACTOR, center[1] * SCALE_FACTOR
    radius = radius * SCALE_FACTOR
    line_width = line_width * SCALE_FACTOR
    circle_width = circle_width * SCALE_FACTOR

    angle_step = math.pi / count

    for i in range(count):
        angle = i * angle_step
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)
        x1 = cx - dx
        y1 = cy - dy
        x2 = cx + dx
        y2 = cy + dy
        draw.line((x1, y1, x2, y2), fill=line_color, width=line_width)

    # Draw outer circle
    radius += 10 * SCALE_FACTOR
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    draw.ellipse(bbox, outline=line_color, width=circle_width)

    x, y = cx - radius, cy + radius + 20 * SCALE_FACTOR
    d = 25 * SCALE_FACTOR
    for i in range(0, 20, 2):
        w = i * SCALE_FACTOR
        if line_width == 1 * SCALE_FACTOR:
            draw.rectangle([x, y, x + w, y + w], outline=line_color, width=SCALE_FACTOR)
            draw.circle(
                (x + w / 2, y + d + w / 2),
                w / 2,
                outline=line_color,
                width=SCALE_FACTOR,
            )
        else:
            draw.rectangle([x, y, x + w, y + w], fill=line_color)
            draw.circle((x + w / 2, y + d + w / 2), w / 2, fill=line_color)
        x += d


# Left: 1px lines and circle
draw_star(draw, center=(150, 150), radius=120, count=32, line_width=1, circle_width=1)

# Right: 4px lines and circle
draw_star(draw, center=(450, 150), radius=120, count=16, line_width=4, circle_width=4)

if SCALE_FACTOR == 1:
    fname = "lines.png"
else:
    fname = f"linesx{FSAA_FACTOR}.png"

# Save
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images", fname))
img.save(filename)
print(f"Image saved as '{fname}'")

# webbrowser.open(f"file://{filename}")
