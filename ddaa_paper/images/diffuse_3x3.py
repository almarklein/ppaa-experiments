"""
Create image for in the paper.
"""

import os
import math

from PIL import Image, ImageDraw


# Image parameters
width, height = 600, 600
background_color = (255, 255, 255)


# Create a blank image
img = Image.new("RGB", (width, height), background_color)
draw = ImageDraw.Draw(img)

# Draw the sample region
region_radius = 100
bbox = [
    300 - region_radius,
    300 - region_radius,
    300 + region_radius,
    300 + region_radius,
]
draw.ellipse(bbox, fill=(220, 220, 220), width=2)

# Draw circles representing pixels
pixel_radius = 20
for x in [100, 300, 500]:
    for y in [100, 300, 500]:
        bbox = [x - pixel_radius, y - pixel_radius, x + pixel_radius, y + pixel_radius]
        color = (100, 100, 100)
        draw.ellipse(bbox, fill=color, width=2)

# Draw lines
draw.line((150, 450, 450, 150), fill=(50, 50, 255), width=6)
# draw.line((50, 300, 550, 300), fill=(255, 100, 100), width=4)

# Dots
dot_radius = 10
sqrt2 = math.sqrt(2)
for x, y in [
    # (200, 300),
    # (400, 300),
    (300 + sqrt2 * 50, 300 - sqrt2 * 50),
    (300 - sqrt2 * 50, 300 + sqrt2 * 50),
]:
    bbox = [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius]
    color = (50, 50, 255)
    draw.ellipse(bbox, fill=color, width=2)


# Save
fname = "diffuse_3x3.png"
filename = os.path.abspath(os.path.join(__file__, "..", fname))
img.save(filename)
print(f"Image saved as '{fname}'")
