# ppaa-experiments
Compare post-processing aa methods (and ssaa)

A simple viewer is provided:

* [Compare ppaa methods](https://almarklein.github.io/ppaa-experiments/viewer.html#&algs=ori,ssaax4,dlaa,fxaa3,axaa,ddaa2)
* [Compare ssaa levels](https://almarklein.github.io/ppaa-experiments/viewer.html#&algs=ori,ssaax4,ssaax2)
* [Compare upsampling methods](https://almarklein.github.io/ppaa-experiments/viewer.html#&algs=up_nearest,up_tent,up_bspline,up_mitchell,up_catmull)


## Goals

* Compare existing techniques, focussing on pure-post-processing techniques (and only single-pass for now).
* Compare on game-like as well as plot-like images.
* Provide wgsl implemenentations for a few of these algorithms.
* Experiment with the algorithms.


## SSAA

I developed a flexible filter for image down and upsampling, which uses
templating to select teh optimal filter kernel without sacrificying precision.
Tests for this filter are added in Pygfx.


## DDAA

I developed a new PPAA method called Directional Diffusion anti-aliasing (DDAA).

This project started in 2013, in the early days of the Vispy project ([wiki post](https://github.com/vispy/vispy/wiki/Tech.-Antialiasing), [code](https://github.com/vispy/experimental/tree/master/fsaa)).
I revived this in 2025, in search for a post-aa filter for [Pygfx](https://github.com/pygfx/pygfx).

The main idea is that I found that many ppaa algorithms use a very simple way to
estimate the orientation of the line, which makes no sense from a scale-space perspective;
these algorithms are very much *not* rotationally invariant, which is probably why the early
versions of FXAA still looked jaggy and were also too blurry. The idea: what if we use proper
scale-space theory (i.e. Gaussian kernels)?

This turns out to work really well, especially for near-diagnoal lines. However,
for near-horizontal and near-vertical lines, the algorithm *must* look further
along the line to realize a smooth transition. For this, ddaa uses a similar
algorithm as FXAA 3.11


## Viewer

This repo contains an HTML file to compare different ppaa methods. You can see it online at https://almarklein.github.io/ppaa-experiments/viewer.html

When you've checked out the repo, you can simply open the local html-file in your browser. This is a great tool if you want to e.g. tweak existing methods, add another method, or develop your own method.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/f96eacb9-aecf-45a4-a8ac-0f2d78be33a3" />


## Experiments
This repo contains a script `estimate_line_angles.py` that shows that a Gaussian derivative kernel
has an error in its angle estinate that is more than 2 times smaller than other kernels.

<img width="633" alt="image" src="https://github.com/user-attachments/assets/0f4c808e-97ba-4153-a879-bcfe8bb6b7b4" />

