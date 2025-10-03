// ddaa2.wgsl version 2.2
//
// Directional Diffusion Anti Aliasing (DDAA) version 2: smooth along the edges based on Scharr kernel, and perform edge-search to better support horizontal/vertical edges.
//
// v0 (2013): original: https://github.com/vispy/experimental/blob/master/fsaa/ddaa.glsl
// v1 (2025): ported to wgsl and tweaked: https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa1.wgsl
// v2.1 (2025): added edge search (2025): https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa2.wgsl
// v2.2 (2025): made SAMPLES_PER_STEP configurable, and fixed a little sampling bug causing an asymetry.

// ========== CONFIG ==========


// The number of samples per step, i.e. per batch of samples.
// Combining samples in a batch helps performance because the texture queries can be
// performed in parallel, to a certain degree. The SAMPLES_PER_STEP should be an even number
// and no larger than 14, because the int pixel offset in textureSampleLevel should be [-8..7]
// and the hardware does not do the right thing for larger values, and may or may not issue a warning.
// Some benchmarking on a few different systems shows that 4 is a good number.
const SAMPLES_PER_STEP : i32 = 3;

// The number of iterations to walk along the edge.
// Setting this to zero disables the edge search, effectively ddaa1.
// The first iter takes SAMPLES_PER_STEP / 2 samples in each direction.
// Each next iters takes SAMPLES_PER_STEP samples in the direction for which the end has not yet been found.
// So the "reach" of the algorithm is (SAMPLES_PER_STEP - 0.5) * MAX_EDGE_ITERS,
// and you want to set it to go to about 10-20 pixels.
const MAX_EDGE_ITERS : i32 = 5;

// The strength of the diffusion. A value of 3 seems to work well.
const DDAA_STRENGTH : f32 = 3.0;

// Trims the algorithm from processing darks.
// low: 0.0833, medium: 0.0625, high: 0.0312, ultra: 0.0156, extreme: 0.0078
const EDGE_THRESHOLD_MIN : f32 = 0.0625;

// The minimum amount of local contrast required to apply algorithm.
// low: 0.250, medium: 0.166, high: 0.125, ultra: 0.063, extreme: 0.031
const EDGE_THRESHOLD_MAX : f32 = 0.166;


// ========== Constants and helper functions ==========

const sqrt2  = sqrt(2.0);

fn rgb2luma(rgb: vec3f) -> f32 {
    return sqrt(dot(rgb, vec3f(0.299, 0.587, 0.114)));  // trick for perceived lightness, used in Bevy
    // return dot(rgb, vec3f(0.299, 0.587, 0.114));  // real luma
}


@fragment
fn fs_main(varyings: Varyings) -> @location(0) vec4<f32> {

    let tex: texture_2d<f32> = colorTex;
    let smp: sampler = texSampler;
    let texCoord: vec2f = varyings.texCoord;

    let resolution = vec2f(textureDimensions(tex));
    let pixelStep = 1.0 / resolution.xy;

    // Sample the center pixel
    let centerSample = textureSampleLevel(tex, smp, texCoord, 0.0);
    let lumaCenter = rgb2luma(centerSample.rgb);

    // Luma at the four direct neighbors of the current fragment.
    let lumaN = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(0, 1)).rgb);
    let lumaE = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, 0)).rgb);
    let lumaS = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(0, -1)).rgb);
    let lumaW = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, 0)).rgb);

    // Query the 4 remaining corners lumas.
    let lumaNW = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, 1)).rgb);
    let lumaNE = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, 1)).rgb);
    let lumaSW = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, -1)).rgb);
    let lumaSE = rgb2luma(textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, -1)).rgb);

    // Compute the range
    let lumaMin = min(lumaCenter, min(min(lumaS, lumaN), min(lumaW, lumaE)));
    let lumaMax = max(lumaCenter, max(max(lumaS, lumaN), max(lumaW, lumaE)));
    let lumaRange = lumaMax - lumaMin;

    // If the luma variation is lower that a threshold (or if we are in a really dark area), we are not on an edge, don't perform any AA.
    if (lumaRange < max(EDGE_THRESHOLD_MIN, lumaMax * EDGE_THRESHOLD_MAX)) {
        return centerSample;
    }

    // Combine the four edges lumas (using intermediary variables for future computations with the same values).
    let lumaSUp = lumaS + lumaN;
    let lumaWRight = lumaW + lumaE;
    let lumaWCorners = lumaSW + lumaNW;

    // Same for corners
    let lumaSCorners = lumaSW + lumaSE;
    let lumaECorners = lumaSE + lumaNE;
    let lumaNCorners = lumaNE + lumaNW;

    // Calculate the image gradient using the Schar kernel, which is (relatively) rotationally invariant.
    const k1 = 162.0 / 256.0; // 61
    const k2 = 47.0 / 256.0; // 17
    let imDx = (lumaW * k1 + lumaSW * k2 + lumaNW * k2) - (lumaE * k1 + lumaSE * k2 + lumaNE * k2);
    let imDy = (lumaS * k1 + lumaSW * k2 + lumaSE * k2) - (lumaN * k1 + lumaNW * k2 + lumaNE * k2);

    // Get the edge vector (orthogonal to the gradient), and calculate strength and direction.
    let edgeVector = vec2f(-imDy, imDx);
    var diffuseStrength = sqrt(length(edgeVector)) * DDAA_STRENGTH;
    var diffuseDirection = normalize(edgeVector);
    if diffuseStrength < 1e-6 {
        diffuseDirection = vec2f(0.0, 0.0);
        diffuseStrength = 0.0;
    }
    diffuseStrength = min(1.0, diffuseStrength);

    // Is the local edge horizontal or vertical ?
    let edgeHorizontal = abs(-2.0 * lumaW + lumaWCorners) + abs(-2.0 * lumaCenter + lumaSUp) * 2.0 + abs(-2.0 * lumaE + lumaECorners);
    let edgeVertical = abs(-2.0 * lumaN + lumaNCorners) + abs(-2.0 * lumaCenter + lumaWRight) * 2.0 + abs(-2.0 * lumaS + lumaSCorners);
    let isHorizontal = (edgeHorizontal >= edgeVertical);
    //let isHorizontal = (abs(diffuseDirection.x) >= abs(diffuseDirection.y)); -> different, resulting in wrong ridge detection

    // Calculate gradient on both sides of the current pixel
    var luma1 = select(lumaW, lumaS, isHorizontal);
    var luma2 = select(lumaE, lumaN, isHorizontal);    // Compute gradients in this direction.
    let gradient1 = luma1 - lumaCenter;
    let gradient2 = luma2 - lumaCenter;

    // Maintain ridges and thin lines. This is inspired by AXAA's 2nd enhancement, except we also apply it to negative edges and do a smooth transition instead of a threshold.
    // Note that we can diminish quite hard, because the neighbouring pixels likely get diffused in the direction of the edge (this is one of our advantages over fxaa).
    if sign(gradient1) == sign(gradient2) {
        // This is a ridge or a valley, e.g. a thin line. We want to presereve these.
        let ridgeness = min(abs(gradient1), abs(gradient2));
        let diminish_factor = 1.0 - (min(1.0, 10 * ridgeness));
        diffuseStrength *= diminish_factor;
    }

    // For long edges, the diffusion has to be huge to remove the jaggies. What algorithms like FXAA do instead, is detect
    // the length of the edge segment (successive horizontal/vertical pixels), and the use that to calculate the subpixel
    // texture coordinate offset, perpendicular to the edge. So technically this is diffusion perpendicular to the edge,
    // but in a controlled manner to smooth the step/jaggy.
    var subpixelEdgeOffset = vec2f(0.0);
    if (MAX_EDGE_ITERS > 0) {

        // Choose the step size (one pixel) accordingly.
        var stepLength = select(pixelStep.x, pixelStep.y, isHorizontal);

        // Gradient in the corresponding direction, normalized.
        let gradientScaled = 0.25 * max(abs(gradient1), abs(gradient2));

        // Average luma in the current direction.
        var lumaLocalAverage = 0.0;
        let gradient2IsHigher = abs(gradient2) > abs(gradient1);
        if  gradient2IsHigher {
            lumaLocalAverage = 0.5 * (luma2 + lumaCenter);
        } else {
            stepLength = -stepLength;  // switch the direction
            lumaLocalAverage = 0.5 * (luma1 + lumaCenter);
        }

        // Shift UV in the correct direction by half a pixel (orthogonal to the edge)
        var currentUv = texCoord;
        if isHorizontal {
            currentUv.y += stepLength * 0.5;
        } else {
            currentUv.x += stepLength * 0.5;
        }

        // We'll sample values from the texture in groups of 4

        var distance1 = 999.0;
        var distance2 = 999.0;

        var lumaEnd1: f32;
        var lumaEnd2: f32;

        // Declare variables for samples
        var lumaEnd_0: f32;
        var lumaEnd_1: f32;
        var lumaEnd_2: f32;
        var lumaEnd_3: f32;
        var lumaEnd_4: f32;
        var lumaEnd_5: f32;
        // Read the lumas at both current extremities of the exploration segment, and compute the delta wrt to the local average luma.
        // TODO: can I use the lumaSE+NE etc. to create the first two samples?
        if isHorizontal {
            lumaEnd_0 = 0.5 * (lumaW + select(lumaSW, lumaNW, gradient2IsHigher)) - lumaLocalAverage;
            lumaEnd_3 = 0.5 * (lumaE + select(lumaSE, lumaNE, gradient2IsHigher)) - lumaLocalAverage;
            lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, -vec2i(2, 0)).rgb) - lumaLocalAverage;
            lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, -vec2i(3, 0)).rgb) - lumaLocalAverage;
            lumaEnd_4 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, vec2i(2, 0)).rgb) - lumaLocalAverage;
            lumaEnd_5 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, vec2i(3, 0)).rgb) - lumaLocalAverage;
        } else {
            lumaEnd_0 = 0.5 * (lumaS + select(lumaSW, lumaSE, gradient2IsHigher)) - lumaLocalAverage;
            lumaEnd_3 = 0.5 * (lumaN + select(lumaNW, lumaNE, gradient2IsHigher)) - lumaLocalAverage;
            lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, -vec2i(0, 2)).rgb) - lumaLocalAverage;
            lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, -vec2i(0, 3)).rgb) - lumaLocalAverage;
            lumaEnd_4 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, vec2i(0, 2)).rgb) - lumaLocalAverage;
            lumaEnd_5 = rgb2luma(textureSampleLevel(tex, smp, currentUv, 0.0, vec2i(0, 3)).rgb) - lumaLocalAverage;
        }

        // The lumaEnd is at least that of the furthest pixel
        // lumaEnd1 = lumaEnd_2;
        // lumaEnd2 = lumaEnd_5;

        // Search for left endpoint in the current 4 samples
        if (abs(lumaEnd_2) >= gradientScaled) { distance1 = 3.0; lumaEnd1 = lumaEnd_2; }
        if (abs(lumaEnd_1) >= gradientScaled) { distance1 = 2.0; lumaEnd1 = lumaEnd_1; }
        if (abs(lumaEnd_0) >= gradientScaled) { distance1 = 1.0; lumaEnd1 = lumaEnd_0; }
        // Same for the right endpoint
        if (abs(lumaEnd_5) >= gradientScaled) { distance2 = 3.0; lumaEnd2 = lumaEnd_5; }
        if (abs(lumaEnd_4) >= gradientScaled) { distance2 = 2.0; lumaEnd2 = lumaEnd_4; }
        if (abs(lumaEnd_3) >= gradientScaled) { distance2 = 1.0; lumaEnd2 = lumaEnd_3; }
        // Now search for endpoints in a series of rounds, using a templated (i.e. unrolled) loop.
        // This is much faster (in WGSL) than a normal loop, probably due to optimization related to the texture lookups.
        // I found it also helps performance to use the same uv coordinate and use the offset parameter.

        var max_distance = 3.0;

            // Iteration 1
            max_distance = 6.0;
            if (distance1 > 900.0) {
                if isHorizontal {
                    let currentUv1 = currentUv - vec2f(5.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv1 = currentUv - vec2f(0.0, 5.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd1 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance1 = 6.0; lumaEnd1 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance1 = 5.0; lumaEnd1 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance1 = 4.0; lumaEnd1 = lumaEnd_0; }
            }
            if (distance2 > 900.0) {
                if isHorizontal {
                    let currentUv2 = currentUv + vec2f(5.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv2 = currentUv + vec2f(0.0, 5.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd2 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance2 = 6.0; lumaEnd2 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance2 = 5.0; lumaEnd2 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance2 = 4.0; lumaEnd2 = lumaEnd_0; }
            }
            // Iteration 2
            max_distance = 9.0;
            if (distance1 > 900.0) {
                if isHorizontal {
                    let currentUv1 = currentUv - vec2f(8.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv1 = currentUv - vec2f(0.0, 8.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd1 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance1 = 9.0; lumaEnd1 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance1 = 8.0; lumaEnd1 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance1 = 7.0; lumaEnd1 = lumaEnd_0; }
            }
            if (distance2 > 900.0) {
                if isHorizontal {
                    let currentUv2 = currentUv + vec2f(8.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv2 = currentUv + vec2f(0.0, 8.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd2 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance2 = 9.0; lumaEnd2 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance2 = 8.0; lumaEnd2 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance2 = 7.0; lumaEnd2 = lumaEnd_0; }
            }
            // Iteration 3
            max_distance = 12.0;
            if (distance1 > 900.0) {
                if isHorizontal {
                    let currentUv1 = currentUv - vec2f(11.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv1 = currentUv - vec2f(0.0, 11.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd1 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance1 = 12.0; lumaEnd1 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance1 = 11.0; lumaEnd1 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance1 = 10.0; lumaEnd1 = lumaEnd_0; }
            }
            if (distance2 > 900.0) {
                if isHorizontal {
                    let currentUv2 = currentUv + vec2f(11.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv2 = currentUv + vec2f(0.0, 11.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd2 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance2 = 12.0; lumaEnd2 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance2 = 11.0; lumaEnd2 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance2 = 10.0; lumaEnd2 = lumaEnd_0; }
            }
            // Iteration 4
            max_distance = 15.0;
            if (distance1 > 900.0) {
                if isHorizontal {
                    let currentUv1 = currentUv - vec2f(14.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv1 = currentUv - vec2f(0.0, 14.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv1, 0.0, -vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd1 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance1 = 15.0; lumaEnd1 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance1 = 14.0; lumaEnd1 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance1 = 13.0; lumaEnd1 = lumaEnd_0; }
            }
            if (distance2 > 900.0) {
                if isHorizontal {
                    let currentUv2 = currentUv + vec2f(14.0, 0.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( -1, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 0, 0)).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i( 1, 0)).rgb) - lumaLocalAverage;
                } else {
                    let currentUv2 = currentUv + vec2f(0.0, 14.0) * pixelStep;
                    lumaEnd_0 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, -1 )).rgb) - lumaLocalAverage;
                    lumaEnd_1 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 0 )).rgb) - lumaLocalAverage;
                    lumaEnd_2 = rgb2luma(textureSampleLevel(tex, smp, currentUv2, 0.0, vec2i(0, 1 )).rgb) - lumaLocalAverage;
                }
                lumaEnd2 = lumaEnd_2;
                if (abs(lumaEnd_2) >= gradientScaled) { distance2 = 15.0; lumaEnd2 = lumaEnd_2; }
                if (abs(lumaEnd_1) >= gradientScaled) { distance2 = 14.0; lumaEnd2 = lumaEnd_1; }
                if (abs(lumaEnd_0) >= gradientScaled) { distance2 = 13.0; lumaEnd2 = lumaEnd_0; }
            }
        // Clip the distance (if we did not find the end, we assume it's one pixel further)
        distance1 = min(distance1, max_distance + 1.0);
        distance2 = min(distance2, max_distance + 1.0);

        // UV offset: read in the direction of the closest side of the edge.
        let pixelOffset = - min(distance1, distance2) / (distance1 + distance2) + 0.5;

        // If the luma at center is smaller than at its neighbor, the delta luma at each end should be positive (same variation).
        let isLumaCenterSmaller = lumaCenter < lumaLocalAverage;
        var correctVariation: bool;
        if (distance1 < distance2) {
            correctVariation = (lumaEnd1 < 0.0) != isLumaCenterSmaller;
        } else {
            correctVariation = (lumaEnd2 < 0.0) != isLumaCenterSmaller;
        }

        // Set subpixel texCoord offset
        if (!correctVariation) {
            subpixelEdgeOffset = vec2f(0.0);
        } else if isHorizontal {
            subpixelEdgeOffset = vec2f(0.0, pixelOffset * stepLength);
        } else {
            subpixelEdgeOffset = vec2f(pixelOffset * stepLength, 0.0);
        }

        // For debugging
        // subpixelEdgeOffset = vec2f(distance1, distance2);
    }

    // We mix the effects of the edge-search with the directional diffusion.
    // Basically, we allow more diffusion if the edge-effect is smaller.
    let edgeStrength = (min(1.0, length(2.0 * subpixelEdgeOffset / pixelStep)));
    diffuseStrength = diffuseStrength * (1.0 - edgeStrength);

    // The step to take for the diffusion effect (blur in the direction of the
    // edge). Note that for diagonal-ish lines, the most blur is obtained when
    // stepping halfway to the next pixel, i.e. 0.707, because then the neighbour
    // pixels are taken into account more. Let's use no more than 0.6 because then
    // for horizontal lines, the max diffusion kernel is effectively [0.6, 2 * 0.5,
    // 0.6] which is still somewhat bell-shaped. Actually, if we use 0.5, we trade a
    // bit more smoothness for perceived sharpness. Make its 0.51 so it does not
    // look like some sort of offset.
    let max_step_size = 0.51;
    let diffuseStep = diffuseDirection * pixelStep * (max_step_size * diffuseStrength);

    // Compose the three texture coordinates, combining the ede-offset with the diffusion componennt, depending on the steepness of the edge.
    let texCoord1 = texCoord - diffuseStep + subpixelEdgeOffset;
    let texCoord2 = texCoord + diffuseStep + subpixelEdgeOffset;

    // Sample the final color
    var finalColor = vec3f(0.0);
    finalColor += 0.5 * textureSampleLevel(tex, smp, texCoord1, 0.0).rgb;
    finalColor += 0.5 * textureSampleLevel(tex, smp, texCoord2, 0.0).rgb;

    // For debugging
    // if (subpixelEdgeOffset.x == 0.0 && subpixelEdgeOffset.y == 0.0) {
    //     finalColor = vec3f(0.0, 0.0, 0.0);
    // } else if (subpixelEdgeOffset.x <= 12.0 && subpixelEdgeOffset.y <= 12.0) {
    //     finalColor = vec3f(0.0, 0.0, 1.0);
    // } else {
    //     finalColor = vec3f(1.0, 0.0, 0.0);
    // }

    return vec4f(finalColor, centerSample.a);

}