const sqrt2  = sqrt(2.0);

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

fn filterweightMitchell1D(t: f32) -> f32 {
    // TODO: if we will in B and C, we can simplify the formula!
    return filterweightCubic1D(t, 1 / 3.0f, 1 / 3.0f);
}
fn filterweightMitchell2D(t: vec2f) -> f32 {
    return filterweightMitchell1D(length(t));
}

fn filterweightGauss_o0(t: f32, sigma_: f32) -> vec2f {
    let sigma = max(sigma_, 1e-9);
    let sigma2 = sigma * sigma;
    let basegauss = exp( - 0.5 * (t*t) / sigma2 );
    let k = basegauss;
    return vec2f(basegauss, k);
}

fn filterweightGauss_o1(t: f32, sigma_: f32) -> vec2f  {
    let sigma = max(sigma_, 1e-9);
    let sigma2 = sigma * sigma;
    let basegauss = exp( - 0.5 * (t*t) / sigma2 );
    let x = t / (sigma * sqrt2);
    let k = - (2 * x) * basegauss;
    let norm_hermite = 1 / (sigma * sqrt2);
    return vec2f(basegauss, k * norm_hermite);
}

fn filterweightGaussDx(t: vec2f, sigma: f32) -> vec2f  {
    let kx = filterweightGauss_o1(t.x, sigma);
    let ky = filterweightGauss_o0(t.y, sigma);
    return kx * ky;
}

fn filterweightGaussDy(t: vec2f, sigma: f32) -> vec2f  {
    let kx = filterweightGauss_o0(t.x, sigma);
    let ky = filterweightGauss_o1(t.y, sigma);
    return kx * ky;
}

struct TexelSample {
    color: vec4<f32>,
    dpos: vec2<f32>,
    value: f32,
};



// TODO: what kernel size?
const kernelSupportFactor = i32(theScaleFactor * 0.5);
// const delta1 = -1 - kernelSupportFactor;
// const delta2 = 3 + kernelSupportFactor;
// const sample_count = (delta2 - delta1) * (delta2 - delta1);
const delta1 = -2 - kernelSupportFactor;
const delta2 = 3 + kernelSupportFactor;
// const delta1 = -3 - kernelSupportFactor;
// const delta2 = 4 + kernelSupportFactor;
const sample_count = (delta2 - delta1) * (delta2 - delta1);

fn aaShader(
    tex: texture_2d<f32>,
    smp: sampler,
    texCoord: vec2<f32>,
    scaleFactor: f32,
) -> vec4<f32> {

    // The size of the source texture
    let resolution = vec2<f32>(textureDimensions(tex).xy);

    // Get the coord expressed in pixels (for the source texture)
    let fpos: vec2f = texCoord * resolution - 0.5;  // the pos for this fragment in the source texture: 0..n-1
    var ipos: vec2i = vec2i(round(fpos));  // flooring can cause the wrong index due to roundoff errors
    var tpos: vec2f = fpos - vec2f(ipos);  // the t offset for the current pos

    // If the scaleFactor is 1, the tpos will always be zero. Otherwise, we generally want the ipos to be smaller than fpos
    //ipos = select(ipos, ipos - 1, tpos < vec2f(-0.1));
    //tpos = fpos - vec2f(ipos);

    //if (scaleFactor != 1.0) {  return vec4f(1.0, 1.0, 0.0, 1.0); }
    //if (abs(tpos.x) > 1e-3) {  return vec4f(1.0, 1.0, 0.0, 1.0); }

    //  X-----X---o-X----X   with X the source pixels
    //        |   |
    //      ipos  fpos

    // Get the size of the patch to sample, i.e. the support for the kernel.
    // Ideally the kernelSupportFactor would be i32((scaleFactor * 1.99)) so that a cubic spline can be fully sampled,
    // but that would result in a lot of samples to be made (100 samples for fsaax2 (scaleFactor 2). With the below it'd be 36.
    // It does mean that the tails of the filter are not used, but since that more or less means more smoothing, this is allright, because
    // we're already downsampling; it's a good compromise.
    // What's important is that for scaleFactor of 1 and lower, the kernel support is [-1 0 1 2].
    // let kernelSupportFactor = i32(scaleFactor * 0.5);
    // let delta1 = -1 - kernelSupportFactor;
    // let delta2 = 3 + kernelSupportFactor;

    // The sigma (scale) of the filter scales with the scaleFactor, because it defines
    // the cut-off frequency of the filter. But when we up-sample, we don't need a filter,
    // and we go in pure interpolation mode, and the filter must match the resolution (== sample rate)
    // of the source image.
    const DDAA_RELATIVE_SIGMA = 1.0;
    let sigma = max(scaleFactor, 1.0) * DDAA_RELATIVE_SIGMA;

    // Create array of samples
    // TODO: would be great if we can make this a const
    // let sample_count = (delta2 - delta1) * (delta2 - delta1);
    var samples: array<TexelSample, sample_count>;

    // Fill the array of samples
    var si = -1;
    for (var yi = delta1; yi < delta2; yi += 1) {
        for (var xi = delta1; xi < delta2; xi += 1) {
            si += 1;

            let idelta = vec2i(xi, yi);
            let t = vec2f(idelta) - tpos;

            // Get index into the image, texture wrap
            // TODO: texture wrap?
            var index = ipos + idelta;
            //index = select(index, -index, index < 0);
            //index = select(index, resolution - index, index >= resolution);

            var sample: TexelSample;
            sample.color = textureLoad(tex, index, 0);
            sample.dpos = t;
            //sample.value = dot(sample.color.rgb, vec3f(0.212, 0.716, 0.072));
            sample.value = sqrt(dot(sample.color.rgb, vec3f(0.299, 0.587, 0.114)));
            samples[si] = sample;
        }
    }

    // if (si != sample_count - 1 ) { return vec4f(1.0, 0.0, 0.0, 1.0);  }

    var weight = 0.0;

    // Calculate mean
    var mean = 0.0;
    weight = 0.0;
    for (var si = 0; si < sample_count; si = si + 1) {
        let sample = samples[si];
        let w = filterweightGauss_o0(length(sample.dpos), sigma); // calculate just once
        mean += sample.value * w[1];
        weight = weight + w[0];
    }
    mean = mean / weight;

    // Calculate variance
    var variance = 0.0;
    for (var si = 0; si < sample_count; si = si + 1) {
        let sample = samples[si];
        let w = filterweightGauss_o0(length(sample.dpos), sigma);
        let d = sample.value - mean;
        variance += d * d;
    }
    variance = variance / weight;
    if (variance < 1e-9) { variance = 1.0; }

    // Calculate Gaussian derivative in x
    var dx = 0.0;
    weight = 0.0;
    for (var si = 0; si < sample_count; si = si + 1) {
        let sample = samples[si];
        let w = filterweightGaussDx(sample.dpos, sigma);
        dx = dx + sample.value * w[1];
        weight = weight + w[0];
    }
    if (weight == 0.0) { weight = 1.0; }
    dx = dx / weight;

    // Calculate Gaussian derivative in y
    var dy = 0.0;
    weight = 0.0;
    for (var si = 0; si < sample_count; si = si + 1) {
        let sample = samples[si];
        let w = filterweightGaussDy(sample.dpos, sigma);
        dy = dy + sample.value * w[1];
        weight = weight + w[0];
    }
    if (weight == 0.0) { weight = 1.0; }
    dy = dy / weight;


    // if (dx < 0) {
    //     dx = -dx;
    //     dy = -dy;
    // }
    // var ang = atan2(dy, dx) * 180 / 3.14159;
    // ang = select(ang, ang+180, ang < 0);
    // //ang = ang + 180;
    // //return vec4(0.0, ang / 180, strength * 2.0, 1.0);
    // return vec4(dx, dy, 0.0, 1.0);

    // Get the direction to smooth in
    let diffuse_vector = vec2f(-dy, dx);
    //let diffuse_vector = normalize(vec2f(dx, dy));
    //let diffuse_vector = vec2f(0.0, 0.5);
    const DDAA_STRENGTH = 5.0;
    //let diffuse_stength = length(diffuse_vector) * DDAA_STRENGTH / sqrt(variance);
    let diffuse_stength = sqrt(length(diffuse_vector)) * DDAA_STRENGTH;

    //if (true) { return vec4f(vec3f(sqrt(length(diffuse_vector))), 1.0); }

    let diffuse_direction = normalize(diffuse_vector);

    // Apply Mitchell filter
    var color = vec4<f32>(0.0, 0.0, 0.0, 0.0);
    weight = 0.0;
    for (var si = 0; si < sample_count; si = si + 1) {
        let sample = samples[si];
        let dpos_n = normalize(sample.dpos);
        //let sigma_scale = abs(sample.dpos.x * diffuse_vector.x) * abs(sample.dpos.y * diffuse_vector.y);
        //let sigma_scale = length(sample.dpos * diffuse_vector);
        //let sigma_scale = abs(sample.dpos.y * diffuse_vector.y);
        var factor = pow(abs(dot(dpos_n, diffuse_direction)), 4.0);
        if (length(sample.dpos) < 1e-3) { factor = 0.0; }

        let t = sample.dpos * ((1.0 - factor) + factor / (1.0 + diffuse_stength));
        let w = filterweightMitchell2D(t);
        color = color + sample.color * w;
        weight = weight + w;
    }
    if (weight == 0.0) { weight = 1.0; }
    return color * (1.0 / weight);
}
