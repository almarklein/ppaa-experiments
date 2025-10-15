"""
Produce WGSL code to sample a kernel with fixed weights using a trick
that uses bilinear interpolation to drastically reduce the number of texture lookups.

This is used in e.g. ssaa.wgsl to produce a *much* more efficient kernel for a scale factor of 2.
"""

# %%%%% Functions

import numpy as np
import scipy


f32 = float


class vec2f:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def cubicWeights(t1: f32, B: f32, C: f32) -> f32:
    t = abs(t1)
    w = 0.0
    t2 = t * t
    t3 = t * t * t
    if t < 1.0:
        w = (
            (12.0 - 9.0 * B - 6.0 * C) * t3
            + (-18.0 + 12.0 * B + 6.0 * C) * t2
            + (6.0 - 2.0 * B)
        )
    elif t <= 2.0:
        w = (
            (-B - 6.0 * C) * t3
            + (6.0 * B + 30.0 * C) * t2
            + (-12.0 * B - 48.0 * C) * t
            + (8.0 * B + 24.0 * C)
        )
    return w / 6.0


def filterweightBspline(t: vec2f) -> f32:
    return cubicWeights(t.x, 1.0, 0.0) * cubicWeights(t.y, 1.0, 0.0)


def filterweightMitchell(t: vec2f) -> f32:
    b = 1 / 3.0
    return cubicWeights(t.x, b, b) * cubicWeights(t.y, b, b)


def filterweightCatmull(t: vec2f) -> f32:
    return cubicWeights(t.x, 0, 0.5) * cubicWeights(t.y, 0, 0.5)


def filterweightLinear(t: vec2f) -> f32:
    return cubicWeights(t.x, 0, 0) * cubicWeights(t.y, 0, 0)


def maximize_4tap(f):
    """
    Given a 2x2 kernel patch (Fortran order), returns (dx, dy, w), which can be used to
    construct something like:

        w * textureSample(..., uv + vec2f(dx, dy))

    The dx and dy are between 0 and 1, with 0.5 meaning right in between the elements.

    """

    # From https://bartwronski.com/2022/03/07/fast-gpu-friendly-antialiasing-downsampling-filter/
    def effective_c(x):
        dx, dy, w = np.clip(x[0], 0, 1), np.clip(x[1], 0, 1), x[2]
        return w * np.array(
            [[(1 - dx) * (1 - dy), (1 - dx) * dy], [dx * (1 - dy), dx * dy]]
        )

    def loss(x):
        return np.sum(np.square(effective_c(x) - f))

    res = scipy.optimize.minimize(loss, [0.5, 0.5, np.sum(f)])
    # print(f, effective_c(res['x']))
    tap_error = np.abs(f - effective_c(res["x"])).max()
    if tap_error > 0.001:
        print(f"tap error: {tap_error}")
    dx, dy, w = res["x"]
    dx, dy = np.clip(dx, 0, 1), np.clip(dy, 0, 1)
    return float(dx), float(dy), w


tap_rows_16_16 = [
    [(0, 0), (0, 2), (0, 4), (0, 6)],
    [(2, 0), (2, 2), (2, 4), (2, 6)],
    [(4, 0), (4, 2), (4, 4), (4, 6)],
    [(6, 0), (6, 2), (6, 4), (6, 6)],
]

tap_rows_16_12 = [
    [(0, 2), (0, 4)],
    [(2, 0), (2, 2), (2, 4), (2, 6)],
    [(4, 0), (4, 2), (4, 4), (4, 6)],
    [(6, 2), (6, 4)],
]

tap_rows_16_8 = [
    [(2, 2), (2, 4)],
    [(4, 2), (4, 4)],
    [(0, 3), (3, 0), (6, 3), (3, 6)],
]

tap_rows_16_4 = [
    [(2, 2), (2, 4)],
    [(4, 2), (4, 4)],
]


# %%%%% Define filter props

# Select the filter function
filterFunc = filterweightBspline

# Select tap rows
tap_rows = tap_rows_16_16


# %%%%% Do the work!

# Flatten taps
taps = []
for tap_row in tap_rows:
    taps.extend(tap_row)

# Create kernel
kernel = np.zeros((8, 8), float)
for iy, dy in enumerate([-3.5, -2.5, -1.5, -0.5, -0.5, 1.5, 2.5, 3.5]):
    for ix, dx in enumerate([-3.5, -2.5, -1.5, -0.5, -0.5, 1.5, 2.5, 3.5]):
        kernel[iy, ix] = filterFunc(vec2f(dx / 2, dy / 2))

# Mask unused elements
mask = np.zeros_like(kernel, dtype=bool)
for tap in taps:
    ix, iy = tap
    mask[iy : iy + 2, ix : ix + 2] = 1
kernel[~mask] = 0

# Normalize kernel
kernel *= 1.0 / kernel.sum()

# Show kernel
for iy in range(kernel.shape[0]):
    for ix in range(kernel.shape[1]):
        w = kernel[iy, ix]
        print(f"{w: 0.04f}", end=" ")
        if ix % 2 == 1 and ix < 7:
            print("|", end=" ")
    print()
    if iy % 2 == 1 and iy < 7:
        print(*["-" * i for i in (16, 17, 17, 16)], sep="+")
print()

# Produce texture sampling lines in wgsl
lines = []
for tap in taps:
    ix, iy = tap
    y0 = iy - 8 / 2 + 0.5
    x0 = ix - 8 / 2 + 0.5
    patch = kernel[iy : iy + 2, ix : ix + 2]
    dx, dy, w = maximize_4tap(patch.T)
    if w != 0:
        lines.append(
            f"color += {w: 0.6f} * textureSampleLevel(colorTex, texSampler, texCoordOrig + vec2f({x0 + dx: 0.6f}, {y0 + dy: 0.6f}) * invPixelSize, 0.0);"
        )

print(f"This filter (for {filterFunc.__name__}) has {len(lines)} texture lookups:\n")
for line in lines:
    print(line)
