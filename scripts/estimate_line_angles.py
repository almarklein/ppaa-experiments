"""
Experiment that estimates the angle of a line using different kernels.
This shows that the method used by FXAA and other techniques is often pretty off,
and that a proper Gaussian derivative kernel does *much* better.
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


def diffusionkernel(sigma, N=4, returnt=False):
    """diffusionkernel(sigma, N=4, returnt=False)

    A discrete analog to the continuous Gaussian kernel,
    as proposed by Toni Lindeberg.

    N is the tail length factor (relative to sigma).

    """

    # Make sure sigma is float
    sigma = float(sigma)

    # Often refered to as the scale parameter, or t
    sigma2 = sigma * sigma

    # Where we start, from which we go backwards
    # This is also the tail length
    if N > 0:
        nstart = int(np.ceil(N * sigma)) + 1
    else:
        nstart = abs(N) + 1

    # Allocate kernel and times
    t = np.arange(-nstart, nstart + 1, dtype="float64")
    k = np.zeros_like(t)

    # Make a start
    n = nstart  # center (t[nstart]==0)
    k[n + nstart] = 0
    n = n - 1
    k[n + nstart] = 0.01

    # Iterate!
    for n in range(nstart - 1, 0, -1):
        # Calculate previous
        k[(n - 1) + nstart] = 2 * n / sigma2 * k[n + nstart] + k[(n + 1) + nstart]

    # The part at the left can be erroneous, so let's use the right part only
    k[:nstart] = np.flipud(k[-nstart:])

    # Remove the tail, which is zero
    k = k[1:-1]
    t = t[1:-1]

    # Normalize
    k = k / k.sum()

    # the function T that we look for is T = e^(-sigma2) * I(n,sigma2)
    # We found I(n,sigma2) and because we normalized it, the normalization term
    # e^(-sigma2) is no longer necesary.

    # Done
    if returnt:
        return k, t
    else:
        return k


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


def angle_from_fxaa_armin(im, x, y):
    nw = float(im[y + 1, x - 1])
    ne = float(im[y + 1, x + 1])
    sw = float(im[y - 1, x - 1])
    se = float(im[y - 1, x + 1])

    dirx = -((nw + ne) - (sw + se))
    diry = (nw + sw) - (ne + se)

    return np.atan2(diry, dirx) * 180 / np.pi


def get_gaussian_kernels(sigma):
    from pirt import gaussfun

    k1 = gaussfun.gaussiankernel(sigma, 1, 3)
    k2 = gaussfun.gaussiankernel(sigma, 0, 3)
    gdx = k1.reshape(1, -1) * k2.reshape(-1, 1)

    k1 = gaussfun.gaussiankernel(sigma, 0, 3)
    k2 = gaussfun.gaussiankernel(sigma, 1, 3)
    gdy = k1.reshape(1, -1) * k2.reshape(-1, 1)

    return gdx, gdy


def get_diffusion_kernels(sigma):
    from pirt import gaussfun

    k1 = gaussfun.diffusionkernel(sigma, 1)
    k = k1.reshape(1, -1) * k1.reshape(-1, 1)

    ldx = k.copy() * 0.5
    ldx[:, 1] = 0
    ldx[:, 2] *= -1

    ldy = k.copy() * 0.5
    ldy[1, :] = 0
    ldy[2, :] *= -1

    return ldx, ldy


gdx, gdy = get_gaussian_kernels(1)
ldx, ldy = get_diffusion_kernels(1)


##
def angle_from_gaussian(im, x, y):
    patch = im[y - 1 : y + 2, x - 1 : x + 2]  # 3x3
    dirx = -(patch * gdx).sum()
    diry = (patch * gdy).sum()

    return np.atan2(dirx, diry) * 180 / np.pi


def angle_from_lindeberg(im, x, y):
    patch = im[y - 1 : y + 2, x - 1 : x + 2]  # 3x3
    dirx = -(patch * ldx).sum()
    diry = (patch * ldy).sum()

    return np.atan2(dirx, diry) * 180 / np.pi


angles_ref = []
angles_sobel = []
angles_fxaa = []
angles_gauss = []
angles_lindeberg = []

for i in range(36):
    angle_ref = i * 5
    im = create_angle_im(angle_ref)

    for y in range(5, 105):
        for x in range(5, 105):
            patch = im[y - 1 : y + 2, x - 1 : x + 2]
            if 1 <= (patch > 0).sum() <= 8:
                angle_sobel = angle_from_fxaa_armin(im, x, y)
                angle_fxaa = angle_from_fxaa_armin(im, x, y)
                angle_gauss = angle_from_gaussian(im, x, y)
                angle_lindeberg = angle_from_lindeberg(im, x, y)

                angles_ref.append(angle_ref)
                angles_sobel.append(get_diff_angle(angle_sobel, angle_ref))
                angles_fxaa.append(get_diff_angle(angle_fxaa, angle_ref))
                angles_gauss.append(get_diff_angle(angle_gauss, angle_ref))
                angles_lindeberg.append(get_diff_angle(angle_lindeberg, angle_ref))


# plt.figure(1)
# plt.clf()
#
# for i in range(16):
#     plt.subplot(4, 4, i + 1)
#     im = create_angle_im(i * 5)
#     plt.imshow(im)
##

alpha = 0.002

plt.figure(2)
plt.clf()

i = 0
for name, angles, color in [
    ("Sobel", angles_sobel, "blue"),
    ("FXAA", angles_fxaa, "red"),
    ("Gauss", angles_gauss, "green"),
    ("Lindeberg", angles_lindeberg, "purple"),
]:
    i += 1
    mean_error = np.abs(angles).mean()
    plt.subplot(2, 2, i)
    plt.title(name)
    plt.xlabel("line angle (deg)")
    plt.ylabel("error of estimated error")
    plt.plot(angles_ref, angles, color=color, ls="", ms=10, marker=".", alpha=alpha)
    plt.plot([0, 180], [mean_error, mean_error], color=color)
    plt.plot([0, 180], [-mean_error, -mean_error], color=color)
    plt.grid()
    plt.ylim(-90, 90)
    print(f"mean_error {name}: {mean_error}")

plt.tight_layout()
plt.show()
