"""
Some experimental code related to different kernel shapes.
A bit messy.
"""

import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


plt.ion()


def weight_for_filter_gaussian_1d(t, sigma=1.0):
    t2 = t / sigma
    return np.exp(-0.5 * t2 * t2)


def weight_for_filter_gaussian_o0(t, sigma):
    sigma2 = sigma**2
    basegauss = np.exp(-(t**2) / (2 * sigma2))
    k = basegauss
    return basegauss, k


def weight_for_filter_gaussian_o1(t, sigma):
    sigma2 = sigma**2
    sqrt2 = np.sqrt(2)  # can be a const
    basegauss = np.exp(-(t**2) / (2 * sigma2))
    x = t / (sigma * sqrt2)
    k = -(2 * x) * basegauss
    norm_hermite = 1 / (sigma * sqrt2)
    return basegauss, k * norm_hermite


def weight_for_filter_gaussian_o2(t, sigma):
    sigma2 = sigma**2
    sqrt2 = np.sqrt(2)  # can be a const
    basegauss = np.exp(-(t**2) / (2 * sigma2))
    x = t / (sigma * sqrt2)
    k = (-2 + 4 * x**2) * basegauss
    norm_hermite = 1 / (sigma * sqrt2) ** 2
    return basegauss, k * norm_hermite


def weight_for_filter_cubic_1d(t, B, C):
    t = abs(t)
    w = 0.0
    t2 = t * t
    t3 = t * t * t
    if t < 1.0:
        w = (
            (12.0 - 9.0 * B - 6 * C) * t3
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


def weight_for_filter_mitchell_1d(t):
    return weight_for_filter_cubic_1d(t, 1 / 3.0, 1 / 3.0)


def weight_for_filter_mitchell_1d_short(t):
    return weight_for_filter_mitchell_1d(t)


# %%%%%%%%%%%%%%%%%%%% Figure showing kernel as 2D surface


size = 20
im = np.zeros((size, size), np.float32)


for iy in range(size):
    for ix in range(size):
        x = ix - 0.5 * size
        y = iy - 0.5 * size
        dist = (x**2 + y**2) ** 0.5
        w1 = weight_for_filter_mitchell_1d(x / 3) * weight_for_filter_mitchell_1d(y / 3)
        w2 = weight_for_filter_mitchell_1d(dist / 3)
        im[iy, ix] = 10 * w2

        # print(abs(w1 - w2))


f = plt.figure(1)
f.clear()
ax = f.add_subplot(111, projection="3d")

surfx, surfy = np.meshgrid(np.arange(size), np.arange(size))
ax.plot_surface(surfx, surfy, im)


# %%%%%%%%%%%%%%%%%%%% Figure showing kernels in 1D


span = 20
factor = 1
g1 = np.array(
    [
        weight_for_filter_gaussian_1d(t, 1)
        for t in np.linspace(-span / 2, span / 2, span * factor)
    ]
)
m1 = np.array([weight_for_filter_mitchell_1d(t) for t in [-1.5, -0.5, 0.5, 1.5]])
# m1 = np.array([weight_for_filter_mitchell_1d(t) for t in [-1, 0, 1, 2]])

g2 = scipy.signal.convolve(g1, m1, "same")

f = plt.figure(2)
f.clear()

plt.plot(m1, lw=3, color="red")
plt.plot(g1, lw=3, color="blue")
plt.plot(g2, lw=3, color="cyan")


# %%%%%%%%%%%%%%%%%%%% Interactive figures comparing different kernelss


data0 = np.zeros(100)
data0[40:60] = 1
data0[80:82] = 0.5


def resample(n, offset, weight_func):
    factor = len(data0) / n
    if weight_func is weight_for_filter_mitchell_1d_short:
        kernel_support_factor = int((factor * 0.5))
        delta1, delta2 = -1 - kernel_support_factor, 3 + kernel_support_factor
        print(factor, list(range(delta1, delta2)))
    else:
        kernel_support_factor = int((factor * 1.99))
        delta1, delta2 = -1 - kernel_support_factor, 3 + kernel_support_factor
    sigma = max(1.0, factor)
    samples = np.linspace(offset, len(data0) + offset, n, endpoint=False)
    sampled_data = []
    for fpos in samples:
        ipos = int(fpos)
        tpos = fpos - ipos
        val = weight = 0
        for idelta in range(delta1, delta2):
            index = ipos + idelta
            if index < 0 or index >= len(data0):
                continue
            w = weight_func((idelta - tpos) / sigma)
            val += w * data0[index]
            weight += w
        weight = weight or 1
        sampled_data.append(val / weight)
    return samples, sampled_data


data1 = resample(20, 0, weight_for_filter_gaussian_1d)
data2 = resample(20, 0, weight_for_filter_mitchell_1d)
data3 = resample(20, 0, weight_for_filter_mitchell_1d_short)

fig = plt.figure(3)
fig.clear()
ax = plt.axes([0.1, 0.2, 0.8, 0.7])

ax.plot(range(len(data0)), data0, lw=3, color="black", marker=".", markersize=8)
(line1,) = plt.plot(data1[0], data1[1], lw=3, color="blue", marker=".", markersize=10)
(line2,) = plt.plot(data2[0], data2[1], lw=3, color="green", marker=".", markersize=10)
(line3,) = plt.plot(data3[0], data3[1], lw=3, color="cyan", marker=".", markersize=10)

slider_ax1 = plt.axes([0.1, 0.10, 0.8, 0.05])
sample_slider = Slider(slider_ax1, "Samples", 10, 200, valinit=20, valstep=1)

slider_ax2 = plt.axes([0.1, 0.05, 0.8, 0.05])
offset_slider = Slider(slider_ax2, "Offset", 0, 10, valinit=0)


def update(val):
    n = int(sample_slider.val)
    offset = float(offset_slider.val)
    data1 = resample(n, offset, weight_for_filter_gaussian_1d)
    data2 = resample(n, offset, weight_for_filter_mitchell_1d)
    data3 = resample(n, offset, weight_for_filter_mitchell_1d_short)
    line1.set_data(*data1)
    line2.set_data(*data2)
    line3.set_data(*data3)
    fig.canvas.draw_idle()


sample_slider.on_changed(update)
offset_slider.on_changed(update)
