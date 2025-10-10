benchmarks = {
    "Intel UHD 630": {
        "fxaa3": {"lines": 707, "circles": 782, "synthetic": 1232, "egypt": 945},
        "fxaa3c": {"lines": 323, "circles": 372, "synthetic": 420, "egypt": 413},
        "ddaa1": {"lines": 319, "circles": 362, "synthetic": 439, "egypt": 435},
        "ddaa2": {"lines": 535, "circles": 617, "synthetic": 916, "egypt": 1215},
    },
    "Intel UHD 730": {
        "fxaa3": {"lines": 1001, "circles": 996, "synthetic": 1916, "egypt": 1351},
        "fxaa3c": {"lines": 399, "circles": 338, "synthetic": 440, "egypt": 390},
        "ddaa1": {"lines": 400, "circles": 389, "synthetic": 561, "egypt": 478},
        "ddaa2": {"lines": 725, "circles": 701, "synthetic": 1273, "egypt": 961},
    },
    "AMD Radeon 780M": {
        "fxaa3": {"lines": 447, "circles": 464, "synthetic": 319, "egypt": 462},
        "fxaa3c": {"lines": 206, "circles": 216, "synthetic": 148, "egypt": 223},
        "ddaa1": {"lines": 230, "circles": 240, "synthetic": 162, "egypt": 253},
        "ddaa2": {"lines": 443, "circles": 474, "synthetic": 335, "egypt": 530},
    },
    "MacBook M1 Pro": {
        "fxaa3": {"lines": 415, "circles": 404, "synthetic": 996, "egypt": 552},
        "fxaa3c": {"lines": 180, "circles": 172, "synthetic": 280, "egypt": 127},
        "ddaa1": {"lines": 191, "circles": 187, "synthetic": 214, "egypt": 220},
        "ddaa2": {"lines": 334, "circles": 316, "synthetic": 708, "egypt": 416},
    },
    "Nvidia RTX 2070": {
        "fxaa3": {"lines": 2690, "circles": 2695, "synthetic": 3589, "egypt": 1370},
        "fxaa3c": {"lines": 303, "circles": 455, "synthetic": 755, "egypt": 514},
        "ddaa1": {"lines": 625, "circles": 623, "synthetic": 1009, "egypt": 1198},
        "ddaa2": {"lines": 2435, "circles": 2362, "synthetic": 4048, "egypt": 1215},
    },
    "Nvidia RTX 3050": {
        "fxaa3": {"lines": 415, "circles": 392, "synthetic": 450, "egypt": 405},
        "fxaa3c": {"lines": 244, "circles": 236, "synthetic": 232, "egypt": 241},
        "ddaa1": {"lines": 320, "circles": 308, "synthetic": 294, "egypt": 241},
        "ddaa2": {"lines": 450, "circles": 422, "synthetic": 522, "egypt": 450},
    },
    "Nvidia RTX 5060 Ti": {
        "fxaa3": {"lines": 282, "circles": 289, "synthetic": 494, "egypt": 321},
        "fxaa3c": {"lines": 255, "circles": 230, "synthetic": 273, "egypt": 221},
        "ddaa1": {"lines": 203, "circles": 196, "synthetic": 322, "egypt": 218},
        "ddaa2": {"lines": 282, "circles": 283, "synthetic": 560, "egypt": 346},
    },
}


method_names = ["fxaa3c", "ddaa1", "fxaa3", "ddaa2"]

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
