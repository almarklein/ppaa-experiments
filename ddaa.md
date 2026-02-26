# DDAA

*This is the main page for DDAA.*


## Introduction

Directional Diffusion Anti Aliasing is an anti-aliasing algorithm that smooths
along the edges based on Scharr kernel, and perform edge-search to better
support horizontal/vertical edges. It combines the best of diffusion and
edge search strategies.

It improves on the popular FXAA by:

* Better appearance of near-diagonal lines (due to the diffusion component).
* Better result for scientific and artificial data, because it does not skip steps.
* Improved performance (depending on the hardware) by using modern API calls.


## Links

* The (templated) source code: [ddaa2.wgsl](https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa2.wgsl)
* The source with default config: [ddaa2_default.wgsl](https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa2_default.wgsl)
* Comparison against other AA methods: https://almarklein.github.io/ppaa-experiments/viewer.html#image=lines.png&algs=ori,fxaa3c,fxaa3d,ddaa1,ddaa2,ddaa2p


## History

This project started in 2013, in the early days of the Vispy project ([wiki post](https://github.com/vispy/vispy/wiki/Tech.-Antialiasing), [code](https://github.com/vispy/experimental/tree/master/fsaa)).
I revived this in 2025, in search for a post-aa filter for [Pygfx](https://github.com/pygfx/pygfx).

The main idea is that I found that many ppaa algorithms use a very simple way to
estimate the orientation of the line, which makes no sense from a scale-space perspective;
these algorithms are very much *not* rotationally invariant, which is probably why the early
versions of FXAA still looked jaggy and were also too blurry. The idea: what if we use proper
scale-space theory (i.e. Gaussian kernels)?

This turns out to work really well, especially for near-diagnoal lines. However,
for near-horizontal and near-vertical lines, the algorithm *must* look further
along the line to realize a smooth transition. For this, ddaa uses a similar algorithm as FXAA 3.11,
but improved upon it to reduce certain artifacts.


## Experiments

This repo contains a script `estimate_line_angles.py` that shows that a Gaussian derivative kernel
has an error in its angle estinate that is more than 2 times smaller than other kernels.

<img width="633" alt="image" src="https://github.com/user-attachments/assets/0f4c808e-97ba-4153-a879-bcfe8bb6b7b4" />
