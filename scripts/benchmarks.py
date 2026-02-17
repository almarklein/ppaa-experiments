"""
Raw benchmark numbers, and processing them into a simple table.
"""

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
    "Intel UHD 730":{
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 107, "circles": 144, "plot": 155, "sponza": 201},
        "ssaax4": {"lines": 7283, "circles": 7059, "plot": 7321, "sponza": 7153},
        "fxaa3c": {"lines": 74, "circles": 103, "plot": 89, "sponza": 138},
        "fxaa3d": {"lines": 222, "circles": 308, "plot": 213, "sponza": 529},
        "ddaa1": {"lines": 95, "circles": 117, "plot": 94, "sponza": 164},
        "ddaa2": {"lines": 153, "circles": 215, "plot": 154, "sponza": 367}
        }
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
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 205, "circles": 186, "plot": 206, "sponza": 183},
        "ssaax4": {"lines": 2735, "circles": 3966, "plot": 3963, "sponza": 3340},
        "fxaa3c": {"lines": 94, "circles": 101, "plot": 90, "sponza": 98},
        "fxaa3d": {"lines": 229, "circles": 228, "plot": 175, "sponza": 331},
        "ddaa1": {"lines": 100, "circles": 98, "plot": 91, "sponza": 118},
        "ddaa2": {"lines": 178, "circles": 175, "plot": 138, "sponza": 246},
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
        "blur": {"lines": 100, "circles": 100, "plot": 100, "sponza": 100},
        "ssaax2": {"lines": 150, "circles": 154, "plot": 150, "sponza": 150},
        "ssaax4": {"lines": 4489, "circles": 3249, "plot": 3328, "sponza": 3206},
        "fxaa3c": {"lines": 93, "circles": 92, "plot": 88, "sponza": 110},
        "fxaa3d": {"lines": 162, "circles": 185, "plot": 139, "sponza": 213},
        "ddaa1": {"lines": 122, "circles": 120, "plot": 119, "sponza": 130},
        "ddaa2": {"lines": 179, "circles": 172, "plot": 147, "sponza": 243},
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
