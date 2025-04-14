"""
Create an artificial image with various circles, in different colors
and on different backgrounds. This is to check the consistency under
different contrasts.
"""

import os
import webbrowser  # noqa

from PIL import Image, ImageDraw


# Image parameters
width, height = 480, 480
background_color = (255, 255, 255)

# Create a blank image
img = Image.new("RGB", (width, height), background_color)
draw = ImageDraw.Draw(img)


def draw_circle(center, line_color):
    draw.circle(center, outline=line_color, radius=30, width=4)
    draw.circle(center, outline=line_color, radius=20, width=1)
    draw.circle(center, fill=line_color, radius=10)


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


draw.rectangle((0, 0, 240, 240), fill=(255, 255, 255))
draw_circles((120, 120))

draw.rectangle((240, 0, 480, 240), fill=(0, 0, 0))
draw_circles((120 + 240, 120))

draw.rectangle((0, 240, 240, 480), fill=(170, 170, 170))
draw_circles((120, 120 + 240))

draw.rectangle((240, 240, 480, 480), fill=(85, 85, 85))
draw_circles((120 + 240, 120 + 240))


# Save
filename = os.path.abspath(os.path.join(__file__, "..", "..", "images", "circles.png"))
img.save(filename)
print("Image saved as 'circles.png'")

# webbrowser.open(f"file://{filename}")
