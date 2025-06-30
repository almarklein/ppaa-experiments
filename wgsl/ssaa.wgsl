// SSAA filter

fn filterweightBox1D(t: f32) -> f32 {
    return f32(abs(t) < 0.5);
}
fn filterweightBox2D(t: vec2f) -> f32 {
    return filterweightBox1D(t.x) * filterweightBox1D(t.y);
}
fn filterweightCircle2D(t: vec2f) -> f32 {
    return filterweightBox1D(length(t));
}

fn filterweightTriangle1D(t: f32) -> f32 {
    return max(0.0, f32(1.0 - abs(t)));
}
fn filterweightTriangle2D(t: vec2f) -> f32 {
    return filterweightTriangle1D(t.x) * filterweightTriangle1D(t.y);
}
fn filterweightCone2D(t: vec2f) -> f32 {
    return filterweightTriangle1D(length(t));
}

fn filterweightGaussian1D(t: f32) -> f32 {
    return exp(-0.5 * t * t);
}
fn filterweightGaussian2D(t: vec2f) -> f32 {
    return filterweightGaussian1D(length(t));
    // Note: the below produces the same result except for some float errors
    // return filterweightGaussian1D(t.x) * filterweightGaussian1D(t.y);
}

fn filterweightCubic1D(t1: f32, B: f32, C: f32) -> f32 {
    let t = abs(t1);
    var w = 0.0f;
    let t2 = t * t;
    let t3 = t * t * t;
    if t < 1.0 {
        w = (12.0 - 9.0 * B - 6.0 * C) * t3 + (-18.0 + 12.0 * B + 6.0 * C) * t2 + (6.0 - 2.0 * B);
    } else if t <= 2.0 {
        w = (-B - 6.0 * C) * t3 + (6.0 * B + 30.0 * C) * t2 + (-12.0 * B - 48.0 * C) * t + (8.0 * B + 24.0 * C);
    }
    return w / 6.0;
}

fn filterweightBspline1D(t: f32) -> f32 {
    return filterweightCubic1D(t, 1.0f, 0.0f);
}
fn filterweightBspline2D(t: vec2f) -> f32 {
    return filterweightBspline1D(length(t));
}

fn filterweightCatmull1D(t: f32) -> f32 {
    return filterweightCubic1D(t, 0.0f, 0.5f);
}
fn filterweightCatmull2D(t: vec2f) -> f32 {
    return filterweightCatmull1D(length(t));
}

fn filterweightMitchell1D(t1: f32) -> f32 {
    // Note: writing out the formula for this specific B and C does not seem to help performance.
    return filterweightCubic1D(t1, 1 / 3.0f, 1 / 3.0f);

}
fn filterweightMitchell2D(t: vec2f) -> f32 {
    return filterweightMitchell1D(length(t));
    // Note: the below does *not* produce the same result. The diagonals won't have the negative lobes.
    // return filterweightMitchell1D(t.x) *  filterweightMitchell1D(t.y);
}


fn aaShader(
    tex: texture_2d<f32>,
    smp: sampler,
    texCoord: vec2<f32>,
    scaleFactor: f32,
) -> vec4<f32> {

    // The size of the source texture
    let resolution = vec2<f32>(textureDimensions(tex).xy);

    // Get the coord expressed in float pixels (for the source texture). The pixel centers are at 0.5, 1.5, 2.5, etc.
    let fpos1: vec2f = texCoord * resolution;
    // Get the integer pixel index into the source texture (floor, not round!)
    let ipos: vec2i = vec2i(fpos1);
    // Project the rounded pixel location back to float, representing the center of that pixel
    let fpos2 = vec2f(ipos) + 0.5;
    // Get the offset for the current sample
    let tpos = fpos1 - fpos2;
    // The texcoord, snapped to the whole pixel in the source texture
    let texCoordSnapped = fpos2 / resolution;

    //  0.   1.   2.   3.   4.   position
    //   ____ ____ ____ ____
    //  |    |    | x  |    |
    //  |____|____|____|____|
    //     0    1    2    3      pixel index
    //
    //  Image the sample at x:
    //
    //  fpos1 = 2.4
    //  ipos  = 2
    //  fpos2 = 2.5
    //  tpos  = -0.1

    // To determine the size of the patch to sample, i.e. the support for the
    // kernel. we need the scale factor between the source and target texture.
    // Ideally the kernelSupportFactor would be int((scaleFactor * 1.99)) so that a
    // cubic spline can be fully sampled, but that would result in a lot of samples
    // to be made (100 samples for fsaax2 (scaleFactor 2). With the below it'd be
    // 36. It does mean that the tails of the filter are not used, but since that
    // more or less means more smoothing, this is allright, because we're already
    // downsampling; it's a good compromise. What's important is that for
    // scaleFactor of 1 and lower, the kernel support is [-1 0 1 2].
    $$ set kernelSupportFactor = (scaleFactor * 0.5) | int
    $$ set delta1 = -1 - kernelSupportFactor
    $$ set delta2 = 3 + kernelSupportFactor

    // The sigma (scale) of the filter scales with the scaleFactor, because it
    // defines the cut-off frequency of the filter. But when we up-sample, we don't
    // need a filter, and we go in pure interpolation mode, and the filter must
    // match the resolution (== sample rate) of the source image, i.e. one.
    let sigma = max({{scaleFactor}}, 1.0);

    // Prepare output
    var color = vec4<f32>(0.0, 0.0, 0.0, 0.0);
    var weight = 0.0;

    // Here's a loop in the shader. This works, but is much slower than a templated (unrolled) loop.
    //
    // for (var dy = delta1; dy < delta2; dy = dy + 1) {
    //     for (var dx = delta1; dx < delta2; dx = dx + 1) {
    //         let idelta = vec2i(dx, dy);
    //         let t = vec2f(idelta) - tpos;
    //         let w = filterweightMitchell2D(t / sigma);
    //         // Get index into the image
    //         var index = ipos + idelta;
    //         let sample = textureLoad(tex, index, 0);
    //         color = color + sample * w;
    //         weight = weight + w;
    //     }
    // }

    // Templated loop
    var t: vec2f;
    var w: f32;
    $$ for dy in range(delta1, delta2)
    $$ for dx in range(delta1, delta2)
        t = vec2f({{dx}}, {{dy}}) - tpos;
        w = filterweight{{filter.lower().capitalize()}}2D(t / sigma);
        //color += w * textureLoad(tex, ipos + idelta, 0);  no sampling, and slower!
        color += w * textureSampleLevel(tex, smp, texCoordSnapped, 0.0, vec2i({{dx}}, {{dy}}));
        weight += w;
    $$ endfor
    $$ endfor

    if weight == 0.0 { weight = 1.0; }
    return color * (1.0 / weight);
}
