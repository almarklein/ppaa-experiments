# On the synthetic.png
macos_m1 = {
    "fxaac": 115,
    "fxaa": 306,
    "ddaa1": 124,
    "ddaa2": 230,  # MAX_EDGE_ITERS =2
    "ddaa2+": 260,  # MAX_EDGE_ITERS = 3
}

win11_rtx_2070 = {
    "fxaac": 190,
    "fxaa": 280,
    "ddaa1": 200,
    "ddaa2": 240,
}

win11_radeon_780m = {
    "fxaac": 205,
    "fxaa": 305,
    "ddaa1": 210,
    "ddaa2": 310,  # with 5x4=15 samples along the edge (6 3 5)
}


"""

MacOS M1
2 x 14 -> 21: 310
2 x 12 -> 18: 290
2 x 10 -> 15: 255  3 x 10 -> 25: 285
2 x 08 -> 12: 245  3 x 08 -> 20: 270
2 x 06 -> 09: 235  3 x 06 -> 15: 240   4 x 06 -> 21: 270
2 x 04 -> 06: 200  3 x 04 -> 10: 230   4 x 04 -> 14: 240  5 x 04 -> 18: 255  6 x 04 -> 22: 260
2 x 02 -> 03: 175  3 x 02 -> 05: xxx   8 x 02 -> 15: 280  10 x 2 -> 19: 300


Win11 Intel 730 integrated graphics.
2 x 14 -> 21: xxxx
2 x 12 -> 18: xxxx
2 x 10 -> 15: xxxx  3 x 10 -> 25: xxxx
2 x 08 -> 12: 1190  3 x 08 -> 20: 1300
2 x 06 -> 09: 1100  3 x 06 -> 15: 1220   4 x 06 -> 21: 1290
2 x 04 -> 06: 1020  3 x 04 -> 10: 1150   4 x 04 -> 14: 1220  5 x 04 -> 18: 1280  6 x 04 -> 22: 1350:
2 x 02 -> 03: xxxx  3 x 02 -> 05: xxxx   8 x 02 -> 15: 1400  10 x 2 -> 19: 1500s

Win11 RTX 2070  (the measurements vary *a lot*)
2 x 14 -> 21: 320
2 x 12 -> 18: xxx
2 x 10 -> 15: xxx  3 x 10 -> 25: xxx
2 x 08 -> 12: 260  3 x 08 -> 20: ??
2 x 06 -> 09: 245  3 x 06 -> 15: 265   4 x 06 -> 21: 270
2 x 04 -> 06: 210  3 x 04 -> 10: 250   4 x 04 -> 14: 240  5 x 04 -> 18: 245  6 x 04 -> 22: xxx:
2 x 02 -> 03: xxx  3 x 02 -> 05: xxx   8 x 02 -> 15: xxx  10 x 2 -> 19: xxx

Win11 Radeon 780M integrated graphics.
2 x 14 -> 21: 480
2 x 12 -> 18: 445
2 x 10 -> 15: 430  3 x 10 -> 25: 450
2 x 08 -> 12: 370  3 x 08 -> 20: 405
2 x 06 -> 09: 345  3 x 06 -> 15: 385   4 x 06 -> 21: 405
2 x 04 -> 06: 300  3 x 04 -> 10: 320   4 x 04 -> 14: 335  5 x 04 -> 18: 345  6 x 04 -> 22: 355:
2 x 02 -> 03: xxx  3 x 02 -> 05: xxx   8 x 02 -> 15: 355  10 x 2 -> 19: 360

4x4 or 3x6, the 04 line seems to perform better on integrated graphics. and more or less the same on M1.
"""
