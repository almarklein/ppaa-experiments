import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


plt.ion()


def weight_for_filter_gaussian_1d(t, sigma=1.0):
    t2 = t / sigma
    return np.exp(-0.5 * t2 * t2)


##
def weight_for_filter_gaussian_on(t, sigma, order):
    sigma2 = sigma**2
    sqrt2 = np.sqrt(2)  # can be a const

    # Calculate the unnormalized base Gaussian
    basegauss = np.exp(-(t**2) / (2 * sigma2))

    # Scale the t-vector, what we actually do is H( t/(sigma*sqrt2) ), where H() is the Hermite polynomial.
    x = t / (sigma * sqrt2)

    # Depending on the order, calculate the Hermite polynomial (physicists notation).
    # We let Mathematica calculate these, and put the first 16 orders in here.
    if order == 0:
        part = 1
    elif order == 1:
        part = 2 * x
    elif order == 2:
        part = -2 + 4 * x**2
    elif order == 3:
        part = -12 * x + 8 * x**3
    elif order == 4:
        part = 12 - 48 * x**2 + 16 * x**4
    elif order == 5:
        part = 120 * x - 160 * x**3 + 32 * x**5
    elif order == 6:
        part = -120 + 720 * x**2 - 480 * x**4 + 64 * x**6
    elif order == 7:
        part = -1680 * x + 3360 * x**3 - 1344 * x**5 + 128 * x**7
    elif order == 8:
        part = 1680 - 13440 * x**2 + 13440 * x**4 - 3584 * x**6 + 256 * x**8
    elif order == 9:
        part = 30240 * x - 80640 * x**3 + 48384 * x**5 - 9216 * x**7 + 512 * x**9
    elif order == 10:
        part = (
            -30240
            + 302400 * x**2
            - 403200 * x**4
            + 161280 * x**6
            - 23040 * x**8
            + 1024 * x**10
        )
    elif order == 11:
        part = (
            -665280 * x
            + 2217600 * x**3
            - 1774080 * x**5
            + 506880 * x**7
            - 56320 * x**9
            + 2048 * x**11
        )
    elif order == 12:
        part = (
            665280
            - 7983360 * x**2
            + 13305600 * x**4
            - 7096320 * x**6
            + 1520640 * x**8
            - 135168 * x**10
            + 4096 * x**12
        )
    elif order == 13:
        part = (
            17297280 * x
            - 69189120 * x**3
            + 69189120 * x**5
            - 26357760 * x**7
            + 4392960 * x**9
            - 319488 * x**11
            + 8192 * x**13
        )
    elif order == 14:
        part = (
            -17297280
            + 242161920 * x**2
            - 484323840 * x**4
            + 322882560 * x**6
            - 92252160 * x**8
            + 12300288 * x**10
            - 745472 * x**12
            + 16384 * x**14
        )
    elif order == 15:
        part = (
            -518918400 * x
            + 2421619200 * x**3
            - 2905943040 * x**5
            + 1383782400 * x**7
            - 307507200 * x**9
            + 33546240 * x**11
            - 1720320 * x**13
            + 32768 * x**15
        )
    elif order == 16:
        part = (
            518918400
            - 8302694400 * x**2
            + 19372953600 * x**4
            - 15498362880 * x**6
            + 5535129600 * x**8
            - 984023040 * x**10
            + 89456640 * x**12
            - 3932160 * x**14
            + 65536 * x**16
        )
    else:
        raise Exception(f"Order {order} is not implemented!")

    # Apply Hermite polynomial to gauss
    k = (-1) ** order * part * basegauss

    # Normalization term that we need because we use the Hermite polynomials.
    norm_hermite = 1 / (sigma * sqrt2) ** order

    # A note on Gaussian derivatives: as sigma increases, the resulting
    # image (when smoothed) will have smaller intensities. To correct for
    # this (if this is necessary) a diffusion normalization term can be
    # applied: sigma**2

    # Normalize and return
    return basegauss, k * norm_hermite


def weight_for_filter_gaussian_o0(t, sigma):
    sigma2 = sigma**2
    sqrt2 = np.sqrt(2)  # can be a const
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


from pirt import gaussfun

tt = np.linspace(-4, 4, 20)
g1 = gaussfun._gaussiankernel(1, 2, tt)
b2, g2 = weight_for_filter_gaussian_o2(tt, 1)
g2 /= b2.sum()
for k1, k2 in zip(g1, g2):
    print(k1, k2)


##
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

##

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


##
import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


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
