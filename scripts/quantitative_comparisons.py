import os

import wgpu
from PIL import Image
import numpy as np

from renderer_wgsl import WgslFullscreenRenderer


upscale = 8


class UpscaleRenderer(WgslFullscreenRenderer):
    SHADER = "ssaa.wgsl"
    TEMPLATE_VARS = {
        "scaleFactor": 1 / upscale,
        "filter": "mitchell",
        "extraKernelSupport": None,
        "optScale2": True,
        "optCorners": True,
    }


adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
renderer = UpscaleRenderer(adapter)


all_images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images_all"))
err_images_dir = os.path.abspath(os.path.join(__file__, "..", "..", "images_err"))

ref_alg = f"x{upscale}"


def load_image(fname, upscale=True):
    filename = os.path.join(all_images_dir, fname)
    im = Image.open(filename).convert("RGBA")
    im = np.asarray(im)
    if upscale:
        im = renderer.render(im)
    assert im.dtype == np.uint8
    return im.astype("f4")[:, :, :3] / 255


def ssim_on_patch(patch1, patch2, dyn_range=1):
    u1 = patch1.mean()
    u2 = patch2.mean()
    s1 = patch1.std()
    s2 = patch2.std()
    # s12 = np.cov(patch1.ravel(), patch2.ravel(), ddof=1)[0, 1]
    s12 = ((patch1 - u1) * (patch2 - u2)).mean()

    k1, k2 = 0.01, 0.03
    c1, c2 = (k1 * dyn_range) ** 2, (k2 * dyn_range) ** 2

    nom = (2 * u1 * u2 + c1) * (2 * s12 + c2)
    denom = (u1**2 + u2**2 + c1) * (s1**2 + s2**2 + c2)
    return nom / denom


def calculate_ssim(im1, im2):
    m = 8 * upscale
    vv = []
    for y in range(im1.shape[0] // m):
        for x in range(im1.shape[1] // m):
            v = 0.0
            for c in (0, 1, 2):
                v += ssim_on_patch(
                    im1[y * m : (y + 1) * m, x * m : (x + 1) * m, c],
                    im2[y * m : (y + 1) * m, x * m : (x + 1) * m, c],
                )
            vv.append(v / 3)
    return np.mean(vv)


def gradient(im):
    dy = im[:-1, :-1] - im[1:, :-1]
    dx = im[:-1, :-1] - im[:-1, 1:]
    return (dx**2 + dy**2) ** 0.5


data = {}

method_names = [
    "ssaax4",
    "ssaax2",
    "blur",
    # "dlaa",
    "fxaa3c",
    "fxaa3d",
    "ddaa1",
    "ddaa2",
]


for img_name in ["lines", "circles", "plot", "sponza"]:
    data[img_name] = {}
    img_name_t = img_name + "_X.png"
    ori_im = load_image(img_name_t.replace("_X", ""))
    ref_im = load_image(img_name_t.replace("_X", ref_alg), upscale=False)

    assert ori_im.shape == ref_im.shape

    pixels_of_interest = (ref_im != ori_im).sum(2).astype(bool)
    npixels = pixels_of_interest.size

    print(img_name)

    for alg in method_names:
        im = load_image(img_name_t.replace("X", alg))

        assert im.shape == (im.shape[0], im.shape[1], 3)
        assert im.shape == ref_im.shape

        dist_from_ref = np.linalg.norm(im - ref_im, axis=2)

        pixels_of_interest = ((ref_im != ori_im) | (ori_im != im)).sum(2).astype(bool)
        assert npixels == pixels_of_interest.size

        mse = (dist_from_ref**2).sum() / im.size
        # mse = (dist_from_ref[pixels_of_interest]**2).sum() / npixels
        psnr = 10 * np.log10(1 / mse)
        ssim = 0  # calculate_ssim(im, ref_im)

        print(f"{alg.rjust(10)}:  mse {mse:0.3f}  psnr {psnr:0.1f}  ssim {ssim:0.2f}")
        data[img_name][alg] = psnr, ssim


##

data.pop("total", None)

total = {alg: np.array([0.0, 0.0]) for alg in method_names}
for image_name in data.keys():
    for alg, values in data[image_name].items():
        total[alg] += data[image_name][alg]

data["total"] = {alg: tuple(x / len(data.keys())) for alg, x in total.items()}

##

# Init tables, For Latex only render the content.
table = []
latex_table = []
rjust = 8

# Header row
table += ["Image".rjust(14)]
latex_table += [r"\textbf{Image}"]
for method_name in method_names:
    table[-1] += method_name.rjust(rjust)
    latex_table[-1] += f" & \\textbf{{{method_name}}}"
latex_table[-1] += r" \\"
latex_table += [r"\hline"]

# Main rows
for image_name, methods in data.items():
    numbers = [methods[x] for x in method_names]
    # numbers = [f"{x[0]:0.1f} {x[1]:0.3f}" for x in numbers]
    numbers = [f"{x[0]:0.1f}" for x in numbers]
    table.append(image_name.rjust(14) + "".join([str(x).rjust(rjust) for x in numbers]))
    latex_table.append(
        image_name + " & " + " & ".join([str(x) for x in numbers]) + r" \\"
    )

print("\n".join(table))
# print("\n".join(latex_table))


##

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
plt.ion()


bench_dict = {}
for method_name in method_names:
    bench_dict[method_name] = {}
for image_name, d in data.items():
    if image_name == "total":
        continue
    for method_name, v in d.items():
        bench_dict[method_name][image_name] = float(v[0])

colors = ["#888", "#AAA", "#444", "#F88",  "#D66", "#88E", "#66C"]

fig = plt.figure(1)
fig.clear()
ax = plt.subplot(111)
for j, alg_name in enumerate(method_names):
    y = list(bench_dict[alg_name].values())
    x = [j -0.3 + 0.2 * k for k in range(len(y))]
    plt.bar(x, y, width=0.15, color=colors[j])
ax.set_xticks([j for j in range(len(method_names))], method_names)
ax.tick_params(axis='x', which='both', length=0)
ax.yaxis.set_major_locator(MultipleLocator(1))
ax.set_ylim(15, 31)
ax.grid(axis='y', which='major')
ax.set_axisbelow(True)
ax.set_ylabel("PSNR (db)")

plt.tight_layout()
fig.savefig("/Users/almar/dev/ddaa_paper/ddaa_paper/images/psnr_results.png", dpi=300)
plt.show()
