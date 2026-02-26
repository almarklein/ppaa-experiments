## SSAA

*This is the main page for ssaa.wgsl.*


## Introduction

The `ssaa.wgsl` shader is a flexible filter for image down and upsampling, which
uses templating to select the optimal filter kernel. Tests for this filter are
added in Pygfx.

Great care is taken to get good performance without sacrifycing precision. When
the scale factor is 1, the filter simply copies the pixels. For upsampling
(scale factor < 1) the kernel size is fixed (4x4 for cubic kernels). For
downsampling (scale factor > 1), the filter size is determined as it scales with
the scale factor. A special optimization is applied when the scale factor is 2
(because in that case the kernel is the same for each fragment).


## Links

* Source code: [ssaa.wgsl](https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ssaa.wgsl)
* Compare ssaa levels: https://almarklein.github.io/ppaa-experiments/viewer.html#&algs=ori,ssaax2,ssaax4,ssaax8
* Compare upsampling filters: https://almarklein.github.io/ppaa-experiments/viewer.html#&algs=up_nearest,up_tent,up_bspline,up_mitchell,up_catmull
* Show interpolation filter kernels: https://almarklein.github.io/ppaa-experiments/interpolate.html
