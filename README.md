# post-processing-aa-research
Compare post-processing aa methods like FXAA

This project started in 2013, in the early days of the Vispy project:
* wiki post: https://github.com/vispy/vispy/wiki/Tech.-Antialiasing
* code: https://github.com/vispy/experimental/tree/master/fsaa

I revived this in 2025, in search for a post-aa filter for [Pygfx](https://github.com/pygfx/pygfx).

The goals of this project:

* Compare existing techniques, focussing on pure-post-processing techniques (and only single-pass for now).
* Compare on game-like as well as plot-like images.
* Provide wgsl implemenentations for a few of these algorithms.
* Experiment with algorithms myself.

As for that last point, I observed that most these algorithm use a very simple way to
estimate the orientation of the line, which makes no sense from a scale-space perspective;
these algorithms are very much *not* rotationally invariant, which is probably why the early
versions of FXAA still looked jaggy and were also too blurry. My idea: what if we use proper
scale-space theory (i.e. Gaussian kernels)? I call this Directional Diffusion Anti Aliasing (DDAA).

This repo contains a script `estimate_line_angles.py` that shows that a Gaussian derivative kernel
has an error in its angle estinate that is more than 2 times smaller than other kernels.
