"""
Raw benchmark numbers, and processing them into a simple table.
"""

# Benchmarks with blur shader as baseline
benchmarks = {
    "Intel UHD 630": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 160, "circles": 160, "plot": 157, "sponza": 155},
        "ssaax4": {"lines": 8874, "circles": 9599, "plot": 100, "sponza": 100},
        "fxaa3c": {"lines": 86, "circles": 90, "plot": 103, "sponza": 100},
        "fxaa3d": {"lines": 189, "circles": 190, "plot": 299, "sponza": 245},
        "ddaa1": {"lines": 92, "circles": 92, "plot": 109, "sponza": 102},
        "ddaa2": {"lines": 148, "circles": 144, "plot": 223, "sponza": 188},
    },
    "Intel UHD 730": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 107, "circles": 144, "plot": 155, "sponza": 201},
        "ssaax4": {"lines": 7283, "circles": 7059, "plot": 7321, "sponza": 7153},
        "fxaa3c": {"lines": 74, "circles": 103, "plot": 89, "sponza": 138},
        "fxaa3d": {"lines": 222, "circles": 308, "plot": 213, "sponza": 529},
        "ddaa1": {"lines": 95, "circles": 117, "plot": 94, "sponza": 164},
        "ddaa2": {"lines": 153, "circles": 215, "plot": 154, "sponza": 367},
    },
    "AMD Radeon 780M": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 169, "circles": 166, "plot": 167, "sponza": 169},
        "ssaax4": {"lines": 57037, "circles": 56059, "plot": 57586, "sponza": 56382},
        "fxaa3c": {"lines": 91, "circles": 90, "plot": 80, "sponza": 114},
        "fxaa3d": {"lines": 179, "circles": 179, "plot": 146, "sponza": 251},
        "ddaa1": {"lines": 97, "circles": 98, "plot": 84, "sponza": 128},
        "ddaa2": {"lines": 186, "circles": 180, "plot": 147, "sponza": 280},
    },
    "MacBook M1 Pro": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 205, "circles": 186, "plot": 206, "sponza": 183},
        "ssaax4": {"lines": 2735, "circles": 3966, "plot": 3963, "sponza": 3340},
        "fxaa3c": {"lines": 94, "circles": 101, "plot": 90, "sponza": 98},
        "fxaa3d": {"lines": 229, "circles": 228, "plot": 175, "sponza": 331},
        "ddaa1": {"lines": 100, "circles": 98, "plot": 91, "sponza": 118},
        "ddaa2": {"lines": 178, "circles": 175, "plot": 138, "sponza": 246},
    },
    "Nvidia RTX 2070": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 135, "circles": 123, "plot": 160, "sponza": 146},
        "ssaax4": {"lines": 9177, "circles": 4142, "plot": 4285, "sponza": 3740},
        "fxaa3c": {"lines": 100, "circles": 104, "plot": 94, "sponza": 115},
        "fxaa3d": {"lines": 275, "circles": 272, "plot": 239, "sponza": 316},
        "ddaa1": {"lines": 137, "circles": 136, "plot": 135, "sponza": 142},
        "ddaa2": {"lines": 246, "circles": 234, "plot": 223, "sponza": 288},
    },
    "Nvidia RTX 3050": {
        # Does not produce very stable results, need to run per-alg to get sensible results
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 150, "circles": 154, "plot": 150, "sponza": 150},
        "ssaax4": {"lines": 4489, "circles": 3249, "plot": 3328, "sponza": 3206},
        "fxaa3c": {"lines": 93, "circles": 92, "plot": 88, "sponza": 110},
        "fxaa3d": {"lines": 162, "circles": 185, "plot": 139, "sponza": 213},
        "ddaa1": {"lines": 122, "circles": 120, "plot": 119, "sponza": 130},
        "ddaa2": {"lines": 179, "circles": 172, "plot": 147, "sponza": 243},
    },
    "Nvidia RTX 5060 Ti": {
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 176, "circles": 138, "plot": 152, "sponza": 101},
        "ssaax4": {"lines": 4742, "circles": 4045, "plot": 4308, "sponza": 2986},
        "fxaa3c": {"lines": 106, "circles": 98, "plot": 92, "sponza": 80},
        "fxaa3d": {"lines": 180, "circles": 172, "plot": 150, "sponza": 153},
        "ddaa1": {"lines": 123, "circles": 115, "plot": 125, "sponza": 87},
        "ddaa2": {"lines": 195, "circles": 172, "plot": 169, "sponza": 171},
    },
}


method_names = ["blur", "ssaax2", "fxaa3c", "ddaa1", "fxaa3d", "ddaa2"]

# Init tables, For Latex only render the content.
table = []
latex_table = []

# Header row
table += ["Device".rjust(24)]
latex_table += [r"\textbf{Device}"]
for method_name in method_names:
    table[-1] += method_name.rjust(8)
    latex_table[-1] += f" & \\textbf{{{method_name}}}"
latex_table[-1] += r" \\"
latex_table += [r"\hline"]

# Main rows
for device, methods in benchmarks.items():
    numbers = [sum(methods[x].values()) // 4 for x in method_names]
    table.append(device.rjust(24) + "".join([str(x).rjust(8) for x in numbers]))
    latex_table.append(device + " & " + " & ".join([str(x) for x in numbers]) + r" \\")

print("\n".join(table))
# print()
# print("\n".join(latex_table))


##

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MultipleLocator  # noqa: E402

plt.ion()


colors = ["#BBB", "#888", "#F88", "#88E", "#D66", "#66C"]

fig = plt.figure(1)
fig.clear()
for i, device_name in enumerate(benchmarks):
    bench_dict = benchmarks[device_name]
    ax = plt.subplot(4, 2, i + 1)
    for j, alg_name in enumerate(method_names):
        y = list(bench_dict[alg_name].values())
        x = [j - 0.3 + 0.2 * k for k in range(len(y))]
        plt.bar(x, y, width=0.15, color=colors[j])
    ax.set_xticks([j for j in range(len(method_names))], method_names)
    ax.tick_params(axis="x", which="both", length=0)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.grid(axis="y", which="major")
    ax.set_axisbelow(True)
    ax.set_title(device_name)

plt.tight_layout()
# fig.savefig("/Users/almar/dev/ddaa_paper/ddaa_paper/images/performance_benchmark_results.png", dpi=300)
plt.show()
