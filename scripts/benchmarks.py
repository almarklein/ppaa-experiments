"""
Raw benchmark numbers, and processing them into a simple table.
"""

# Benchmarks with null shader as baseline
# benchmarks = {
#     "Intel UHD 630": {
#         "fxaa3d": {"lines": 707, "circles": 782, "synthetic": 1232, "egypt": 945},
#         "fxaa3c": {"lines": 323, "circles": 372, "synthetic": 420, "egypt": 413},
#         "ddaa1": {"lines": 319, "circles": 362, "synthetic": 439, "egypt": 435},
#         "ddaa2": {"lines": 535, "circles": 617, "synthetic": 916, "egypt": 1215},
#     },
#     "Intel UHD 730": {
#         "fxaa3d": {"lines": 1001, "circles": 996, "synthetic": 1916, "egypt": 1351},
#         "fxaa3c": {"lines": 399, "circles": 338, "synthetic": 440, "egypt": 390},
#         "ddaa1": {"lines": 400, "circles": 389, "synthetic": 561, "egypt": 478},
#         "ddaa2": {"lines": 725, "circles": 701, "synthetic": 1273, "egypt": 961},
#     },
#     "AMD Radeon 780M": {
#         "fxaa3d": {"lines": 447, "circles": 464, "synthetic": 319, "egypt": 462},
#         "fxaa3c": {"lines": 206, "circles": 216, "synthetic": 148, "egypt": 223},
#         "ddaa1": {"lines": 230, "circles": 240, "synthetic": 162, "egypt": 253},
#         "ddaa2": {"lines": 443, "circles": 474, "synthetic": 335, "egypt": 530},
#     },
#     "MacBook M1 Pro": {
#         "fxaa3d": {"lines": 415, "circles": 404, "synthetic": 996, "egypt": 552},
#         "fxaa3c": {"lines": 180, "circles": 172, "synthetic": 280, "egypt": 127},
#         "ddaa1": {"lines": 191, "circles": 187, "synthetic": 214, "egypt": 220},
#         "ddaa2": {"lines": 334, "circles": 316, "synthetic": 708, "egypt": 416},
#     },
#     "Nvidia RTX 2070": {
#         "fxaa3d": {"lines": 2690, "circles": 2695, "synthetic": 3589, "egypt": 1370},
#         "fxaa3c": {"lines": 303, "circles": 455, "synthetic": 755, "egypt": 514},
#         "ddaa1": {"lines": 625, "circles": 623, "synthetic": 1009, "egypt": 1198},
#         "ddaa2": {"lines": 2435, "circles": 2362, "synthetic": 4048, "egypt": 1215},
#     },
#     "Nvidia RTX 3050": {
#         "fxaa3d": {"lines": 415, "circles": 392, "synthetic": 450, "egypt": 405},
#         "fxaa3c": {"lines": 244, "circles": 236, "synthetic": 232, "egypt": 241},
#         "ddaa1": {"lines": 320, "circles": 308, "synthetic": 294, "egypt": 241},
#         "ddaa2": {"lines": 450, "circles": 422, "synthetic": 522, "egypt": 450},
#     },
#     "Nvidia RTX 5060 Ti": {
#         "fxaa3d": {"lines": 282, "circles": 289, "synthetic": 494, "egypt": 321},
#         "fxaa3c": {"lines": 255, "circles": 230, "synthetic": 273, "egypt": 221},
#         "ddaa1": {"lines": 203, "circles": 196, "synthetic": 322, "egypt": 218},
#         "ddaa2": {"lines": 282, "circles": 283, "synthetic": 560, "egypt": 346},
#     },
# }

# Benchmarks with blur shader as baseline
benchmarks = {
    "Intel UHD 630": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 144, "circles": 155},
        "ssaax4": {"lines": 8874, "circles": 9599},
        "fxaa3c": {"lines": 86, "circles": 90, "synthetic": 103, "egypt": 100},
        "fxaa3d": {"lines": 189, "circles": 190, "synthetic": 299, "egypt": 245},
        "ddaa1": {"lines": 92, "circles": 92, "synthetic": 109, "egypt": 102},
        "ddaa2": {"lines": 148, "circles": 144, "synthetic": 223, "egypt": 188},
    },
    "Intel UHD 730": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 144, "circles": 144},
        "ssaax4": {"lines": 7991, "circles": 7058},
        "fxaa3c": {"lines": 59, "circles": 74, "synthetic": 104, "egypt": 101},
        "fxaa3d": {"lines": 290, "circles": 287, "synthetic": 472, "egypt": 362},
        "ddaa1": {"lines": 118, "circles": 114, "synthetic": 141, "egypt": 130},
        "ddaa2": {"lines": 211, "circles": 203, "synthetic": 318, "egypt": 258},
    },
    "AMD Radeon 780M": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 173, "circles": 175},
        "ssaax4": {"lines": 65848, "circles": 65855},
        "fxaa3c": {"lines": 83, "circles": 78, "synthetic": 78, "egypt": 88},
        "fxaa3d": {"lines": 182, "circles": 180, "synthetic": 188, "egypt": 195},
        "ddaa1": {"lines": 91, "circles": 89, "synthetic": 98, "egypt": 98},
        "ddaa2": {"lines": 176, "circles": 165, "synthetic": 187, "egypt": 208},
    },
    "MacBook M1 Pro": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 194, "circles": 185},
        "ssaax4": {"lines": 3864, "circles": 4082},
        "fxaa3c": {"lines": 94, "circles": 90, "synthetic": 97, "egypt": 99},
        "fxaa3d": {"lines": 131, "circles": 129, "synthetic": 348, "egypt": 271},
        "ddaa1": {"lines": 101, "circles": 98, "synthetic": 110, "egypt": 110},
        "ddaa2": {"lines": 173, "circles": 165, "synthetic": 246, "egypt": 206},
    },
    "Nvidia RTX 2070": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 142, "circles": 144},
        "ssaax4": {"lines": 4758, "circles": 4859},
        "fxaa3c": {"lines": 102, "circles": 103, "synthetic": 108, "egypt": 107},
        "fxaa3d": {"lines": 255, "circles": 259, "synthetic": 330, "egypt": 284},
        "ddaa1": {"lines": 134, "circles": 135, "synthetic": 151, "egypt": 138},
        "ddaa2": {"lines": 231, "circles": 229, "synthetic": 309, "egypt": 251},
    },
    "Nvidia RTX 3050": {
        # Does not produce very stable results, need to run per-alg to get sensible results
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 161, "circles": 160},
        "ssaax4": {"lines": 4497, "circles": 4174},
        "fxaa3c": {"lines": 102, "circles": 101, "synthetic": 94, "egypt": 95},
        "fxaa3d": {"lines": 150, "circles": 146, "synthetic": 185, "egypt": 160},
        "ddaa1": {"lines": 124, "circles": 122, "synthetic": 128, "egypt": 127},
        "ddaa2": {"lines": 152, "circles": 155, "synthetic": 224, "egypt": 189},
    },
    "Nvidia RTX 5060 Ti": {
        "blur": {"lines": 100, "circles": 100, "synthetic": 100, "egypt": 100},
        "ssaax2": {"lines": 154, "circles": 174},
        "ssaax4": {"lines": 4264, "circles": 4030},
        "fxaa3c": {"lines": 105, "circles": 99, "synthetic": 103, "egypt": 103},
        "fxaa3d": {"lines": 189, "circles": 203, "synthetic": 204, "egypt": 214},
        "ddaa1": {"lines": 170, "circles": 117, "synthetic": 156, "egypt": 159},
        "ddaa2": {"lines": 197, "circles": 187, "synthetic": 232, "egypt": 199},
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
