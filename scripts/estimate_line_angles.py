"""
Experiment that estimates the angle of a line using different kernels.
This shows that the method used by FXAA and other techniques is often pretty off,
and that the Scharr kernel does much better.
"""

import numpy as np
import matplotlib.pyplot as plt

# plt.ion()


def create_angle_im(deg):
    angle = deg * np.pi / 180
    im = np.zeros((110, 110), np.uint8)

    for t in np.linspace(-100, 100, 2000):
        x = 55 + int(np.round(np.cos(angle) * t))
        y = 55 + int(np.round(np.sin(angle) * t))
        if x < 0 or y < 0 or x > 109 or y > 109:
            continue
        im[y, x] = 255
    return im


def gaussiankernel(sigma, order, n):
    """ _gaussiankernel(sigma, order, t)
    Calculate a Gaussian kernel of the given sigma and with the given
    order, using the given t-values.
    """

    n = int(n)
    t = np.arange(-n/2.0+0.5, n/2.0, 1.0, dtype=float)

    # precalculate some stuff
    sigma2 = sigma**2
    sqrt2  = np.sqrt(2)

    # Calculate the gaussian, it is unnormalized. We'll normalize at the end.
    basegauss = np.exp(- t**2 / (2*sigma2) )

    # Scale the t-vector, what we actually do is H( t/(sigma*sqrt2) ),
    # where H() is the Hermite polynomial.
    x = t / (sigma*sqrt2)

    # Depending on the order, calculate the Hermite polynomial
    if order<0:
        raise Exception("The order should not be negative!")
    elif order==0:
        part = 1
    elif order==1:
        part = 2*x
    elif order==2:
        part = -2 + 4*x**2
    else:
        raise Exception("This order is not implemented!")

    # Apply Hermite polynomial to gauss
    k = (-1)**order * part * basegauss

    # Normalize
    norm_default = 1 / basegauss.sum()  # == 1 / ( sigma * sqrt(2*pi) )
    norm_hermite = 1/(sigma*sqrt2)**order
    return k * ( norm_default * norm_hermite )


def get_gaussian_kernels(sigma, n):

    k1 = gaussiankernel(sigma, 1, n)
    k2 = gaussiankernel(sigma, 0, n)
    gdx = k1.reshape(1, -1) * k2.reshape(-1, 1)

    k1 = gaussiankernel(sigma, 0, n)
    k2 = gaussiankernel(sigma, 1, n)
    gdy = k1.reshape(1, -1) * k2.reshape(-1, 1)

    return gdx, gdy


gdx9, gdy9 = get_gaussian_kernels(0.5, 3)
gdx25, gdy25 = get_gaussian_kernels(0.5, 5)


def get_scharr_kernels():

    k1 = 162.0 / 256.0;
    k2 = 47.0 / 256.0;
    scharr_y = np.array(
        [
        [k2, k1, k2],
        [0, 0, 0],
        [-k2, -k1, -k2],
    ], float)
    scharr_x = scharr_y.T.copy()
    return scharr_x, scharr_y


scharrx, scharry = get_scharr_kernels()


def get_diff_angle(angle, ref_angle):
    angle = angle - ref_angle
    while angle < -90:
        angle += 180
    while angle > +90:
        angle -= 180
    return angle


def angle_from_sobel(im, x, y):
    n = float(im[y + 1, x])
    e = float(im[y, x + 1])
    s = float(im[y - 1, x])
    w = float(im[y, x - 1])

    dirx = -(n - s)
    diry = w - e

    return np.atan2(diry, dirx) * 180 / np.pi


def angle_from_fxaa(im, x, y):
    nw = float(im[y + 1, x - 1])
    ne = float(im[y + 1, x + 1])
    sw = float(im[y - 1, x - 1])
    se = float(im[y - 1, x + 1])

    dirx = (sw-ne) + (se-nw)
    diry = (sw-ne) - (se-nw)

    return np.atan2(diry, dirx) * 180 / np.pi


def angle_from_gaussian9(im, x, y):
    patch = im[y - 1 : y + 2, x - 1 : x + 2]  # 3x3
    dirx = -(patch * gdx9).sum()
    diry = (patch * gdy9).sum()

    return np.atan2(dirx, diry) * 180 / np.pi


def angle_from_gaussian25(im, x, y):
    patch = im[y - 2 : y + 3, x - 2 : x + 3]  # 5x5
    dirx = -(patch * gdx25).sum()
    diry = (patch * gdy25).sum()

    return np.atan2(dirx, diry) * 180 / np.pi


def angle_from_scharr(im, x, y):
    patch = im[y - 1 : y + 2, x - 1 : x + 2]  # 3x3
    dirx = -(patch * scharrx).sum()
    diry = (patch * scharry).sum()

    return np.atan2(dirx, diry) * 180 / np.pi



angles_ref = []
angles_sobel = []
angles_fxaa = []
angles_gauss = []
angles_scharr = []

for i in range(36):
    angle_ref = i*5
    im = create_angle_im(angle_ref)

    for y in range(5, 105):
        for x in range(5, 105):
            patch = im[y - 1 : y + 2, x - 1 : x + 2]
            if 1 <= (patch > 0).sum() <= 8:
                angle_sobel = angle_from_sobel(im, x, y)
                angle_fxaa = angle_from_fxaa(im, x, y)
                angle_gauss = angle_from_gaussian9(im, x, y)
                angle_scharr = angle_from_scharr(im, x, y)

                angles_ref.append(angle_ref)
                angles_sobel.append(get_diff_angle(angle_sobel, angle_ref))
                angles_fxaa.append(get_diff_angle(angle_fxaa, angle_ref))
                angles_gauss.append(get_diff_angle(angle_gauss, angle_ref))
                angles_scharr.append(get_diff_angle(angle_scharr, angle_ref))


alpha = 0.002

fig = plt.figure(2)
plt.clf()

i = 0
for name, angles, color in [
    ("Sobel", angles_sobel, "#5AF"),
    ("FXAA", angles_fxaa, "#5AF"),
    ("Gaussian", angles_gauss, "#5AF"),
    ("Scharr", angles_scharr, "#5AF")
]:
    i += 1
    mean_error = np.abs(angles).mean()
    plt.subplot(2, 2, i)
    plt.title(f"{name}")
    plt.xlabel("real angle (deg)")
    plt.ylabel("angle error (deg)")
    plt.plot(angles_ref, angles, color=color, ls="", ms=10, marker=".", mew=0, alpha=alpha)
    plt.plot([0, 180], [mean_error, mean_error], color=color)
    plt.plot([0, 180], [-mean_error, -mean_error], color=color)
    plt.grid()
    plt.ylim(-90, 90)
    plt.text(-5, 60, f"mean: {mean_error:0.0f}")
    print(f"mean_error {name}: {mean_error}")

plt.tight_layout()
# fig.savefig("/Users/almar/dev/ddaa_paper/images/edge_angles.png", dpi=300)
plt.show()
