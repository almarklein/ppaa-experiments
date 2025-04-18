// FSAA filter

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
    // The below produces the same result except for some float errors
    // return filterweightGaussian1D(t.x) * filterweightGaussian1D(t.y);
}

fn filterweightCubic1D(t1: f32, B: f32, C: f32) -> f32 {
    let t = abs(t1);
    var w = 0.0f;
    let t2 = t * t;
    let t3 = t * t * t;
    if (t < 1.0) {
        w = (12.0 - 9.0 * B - 6 * C) * t3 + (-18.0 + 12.0 * B + 6.0 * C) * t2 + (6.0 - 2.0 * B);
    } else if (t <= 2.0) {
        w = (-B - 6.0 * C) * t3 + (6.0 * B + 30.0 * C) * t2 + (-12.0 * B - 48.0 * C) * t + (8.0 * B + 24.0 * C);
    }
    return w / 6.0;
}

fn filterweightBSpline1D(t: f32) -> f32 {
    return filterweightCubic1D(t, 1.0f, 0.0f);
}
fn filterweightBSpline2D(t: vec2f) -> f32 {
    return filterweightBSpline1D(length(t));
}

fn filterweightCatmullRom1D(t: f32) -> f32 {
    return filterweightCubic1D(t, 0.0f, 0.5f);
}
fn filterweightCatmullRom2D(t: vec2f) -> f32 {
    return filterweightCatmullRom1D(length(t));
}

fn filterweightMitchell1D(t: f32) -> f32 {
    // TODO: if we will in B and C, we can simplify the formula!
    return filterweightCubic1D(t, 1 / 3.0f, 1 / 3.0f);
}
fn filterweightMitchell2D(t: vec2f) -> f32 {
    return filterweightMitchell1D(length(t));
    // The below does *not* produce the same result. The diagonals won't have the negative lobes.
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

    // Get the coord expressed in pixels (for the source texture)
    let fpos: vec2f = texCoord * resolution;  // the pos for this fragment in the source texture
    let ipos: vec2i = vec2i(fpos);  // floored
    let tpos: vec2f = fpos - vec2f(ipos);  // the t offset for the current pos

    //  X-----X---o-X----X   with X the source pixels
    //        |   |
    //      ipos  fpos

    // Get the size of the patch to sample, i.e. the support for the kernel.
    // Ideally the kernelSupportFactor would be i32((scaleFactor * 1.99)) so that a cubic spline can be fully sampled,
    // but that would result in a lot of samples to be made (100 samples for fsaax2 (scaleFactor 2). With the below it'd be 36.
    // It does mean that the tails of the filter are not used, but since that more or less means more smoothing, this is allright, because
    // we're already downsampling; it's a good compromise.
    // What's important is that for scaleFactor of 1 and lower, the kernel support is [-1 0 1 2].
    let kernelSupportFactor = i32(scaleFactor * 0.5);
    let delta1 = -1 - kernelSupportFactor;
    let dalta2 = 3 + kernelSupportFactor;

    // The sigma (scale) of the filter scales with the scaleFactor, because it defines
    // the cut-off frequency of the filter. But when we up-sample, we don't need a filter,
    // and we go in pure interpolation mode, and the filter must match the resolution (== sample rate)
    // of the source image.
    let sigma = max(scaleFactor, 1.0);

    var color = vec4<f32>(0.0, 0.0, 0.0, 0.0);
    var weight = 0.0;
    for (var dy = delta1; dy < dalta2; dy = dy + 1) {
        for (var dx = delta1; dx < dalta2; dx = dx + 1) {
            let idelta = vec2i(dx, dy);
            let t = vec2f(idelta) - tpos;

            //let w = filterweightBox2D(t / sigma);
            //let w = filterweightTriangle2D(t / sigma);
            //let w = filterweightGaussian2D(t / sigma);
            let w = filterweightMitchell2D(t / sigma);

            // Get index into the image, texture wrap
            // TODO: texture wrap?
            var index = ipos + idelta;
            //index = select(index, -index, index < 0);
            //index = select(index, resolution - index, index >= resolution);

            let sample = textureLoad(tex, index, 0);
            color = color + sample * w;
            weight = weight + w;
        }
    }
    if (weight == 0.0) { weight = 1.0; }
    return color * (1.0 / weight);
}
