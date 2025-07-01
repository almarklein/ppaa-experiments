// ddaa2.wgsl version 2.1
//
// Directional Diffusion Anti Aliasinng (DDAA) version 2: smooth along the edges based on Scharr kernel, and perform edge-search to better support horizontal/vertical edges.
//
// v0: original (2013): https://github.com/vispy/experimental/blob/master/fsaa/ddaa.glsl
// v1: ported to wgsl and tweaked (2025): https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa1.wgsl
// v2: added edge search (2025): https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa2.wgsl

// ========== DDAA CONFIG ==========

// The strength of the diffusion.
const DDAA_STRENGTH = 3.0;

// If false, use only diffusion which is much lighter, and the speed independent on the image content.
// If true, the smoothing of near-horizontal and near-vertical edges is much better.
const USE_EDGE_SEARCH = true;


// ========== FXAA CONFIG ==========

// Trims the algorithm from processing darks.
// const EDGE_THRESHOLD_MIN: f32 = 0.0833;  // low
const EDGE_THRESHOLD_MIN: f32 = 0.0625;  // medium
// const EDGE_THRESHOLD_MIN: f32 = 0.0312;  // hight
// const EDGE_THRESHOLD_MIN: f32 = 0.0156;  // ultra
// const EDGE_THRESHOLD_MIN: f32 = 0.0078;  // extreme

// The minimum amount of local contrast required to apply algorithm.
// const EDGE_THRESHOLD_MAX: f32 = 0.250;  // low
const EDGE_THRESHOLD_MAX: f32 = 0.166;  // medium
// const EDGE_THRESHOLD_MAX: f32 = 0.125;  // high
// const EDGE_THRESHOLD_MAX: f32 = 0.063;  // ultra
// const EDGE_THRESHOLD_MAX: f32 = 0.031;  // extreme

const ITERATIONS: i32 = 12; //default is 12
const SUBPIXEL_QUALITY: f32 = 0.75;
// #define QUALITY(q) ((q) < 5 ? 1.0 : ((q) > 5 ? ((q) < 10 ? 2.0 : ((q) < 11 ? 4.0 : 8.0)) : 1.5))
fn QUALITY(q: i32) -> f32 {
    switch (q) {
        //case 0, 1, 2, 3, 4: { return 1.0; }
        default:              { return 1.0; }
        case 5:               { return 1.5; }
        case 6, 7, 8, 9:      { return 2.0; }
        case 10:              { return 4.0; }
        case 11:              { return 8.0; }
    }
}

// ========== Constants and helper functions ==========

const sqrt2  = sqrt(2.0);

fn rgb2luma(rgb: vec3f) -> f32 {
    return sqrt(dot(rgb, vec3f(0.299, 0.587, 0.114)));  // trick for perceived lightness, used in Bevy
    // return dot(rgb, vec3f(0.299, 0.587, 0.114));  // real luma
}


fn get_subpixel_offset_for_long_edge(tex: texture_2d<f32>, samp: sampler, texCoord: vec2f, pixelStep: vec2f, isHorizontal: bool, lumaCenter: f32, luma1: f32, luma2: f32) -> vec2f {

    // Choose the step size (one pixel) accordingly.
    var stepLength = select(pixelStep.x, pixelStep.y, isHorizontal);

    // Gradient in the corresponding direction, normalized.
    let gradient1 = luma1 - lumaCenter;
    let gradient2 = luma2 - lumaCenter;
    let gradientScaled = 0.25 * max(abs(gradient1), abs(gradient2));

    // Average luma in the current direction.
    var lumaLocalAverage = 0.0;
    if abs(gradient1) >= abs(gradient2) {
        stepLength = -stepLength;  // switch the direction
        lumaLocalAverage = 0.5 * (luma1 + lumaCenter);
    } else {
        lumaLocalAverage = 0.5 * (luma2 + lumaCenter);
    }

    // Shift UV in the correct direction by half a pixel.
    // Compute offset (for each iteration step) in the right direction.
    var currentUv = texCoord;
    var offset = vec2f(0.0, 0.0);
    if isHorizontal {
        currentUv.y = currentUv.y + stepLength * 0.5;
        offset.x = pixelStep.x;
    } else {
        currentUv.x = currentUv.x + stepLength * 0.5;
        offset.y = pixelStep.y;
    }

    // Compute UVs to explore on each side of the edge, orthogonally. The QUALITY allows us to step faster.
    var uv1 = currentUv - offset; // * QUALITY(0); // (quality 0 is 1.0)
    var uv2 = currentUv + offset; // * QUALITY(0); // (quality 0 is 1.0)

    // Read the lumas at both current extremities of the exploration segment, and compute the delta wrt to the local average luma.
    var lumaEnd1 = rgb2luma(textureSampleLevel(tex, samp, uv1, 0.0).rgb);
    var lumaEnd2 = rgb2luma(textureSampleLevel(tex, samp, uv2, 0.0).rgb);
    lumaEnd1 = lumaEnd1 - lumaLocalAverage;
    lumaEnd2 = lumaEnd2 - lumaLocalAverage;

    // If the luma deltas at the current extremities is larger than the local gradient, we have reached the side of the edge.
    var reached1 = abs(lumaEnd1) >= gradientScaled;
    var reached2 = abs(lumaEnd2) >= gradientScaled;
    var reachedBoth = reached1 && reached2;

    // If the side is not reached, we continue to explore in this direction.
    uv1 = select(uv1 - offset, uv1, reached1); // * QUALITY(1); // (quality 1 is 1.0)
    uv2 = select(uv2 - offset, uv2, reached2); // * QUALITY(1); // (quality 1 is 1.0)

    // If both sides have not been reached, continue to explore.
    if !reachedBoth {
        for (var i: i32 = 2; i < ITERATIONS; i = i + 1) {
            // If needed, read luma in 1st direction, compute delta.
            if !reached1 {
                lumaEnd1 = rgb2luma(textureSampleLevel(tex, samp, uv1, 0.0).rgb);
                lumaEnd1 = lumaEnd1 - lumaLocalAverage;
            }
            // If needed, read luma in oposite direction, compute delta.
            if !reached2 {
                lumaEnd2 = rgb2luma(textureSampleLevel(tex, samp, uv2, 0.0).rgb);
                lumaEnd2 = lumaEnd2 - lumaLocalAverage;
            }
            // If the luma deltas at the current extremities is larger than the local gradient, we have reached the side of the edge.
            reached1 = abs(lumaEnd1) >= gradientScaled;
            reached2 = abs(lumaEnd2) >= gradientScaled;
            reachedBoth = reached1 && reached2;

            // If the side is not reached, we continue to explore in this direction, with a variable quality.
            if !reached1 {
                uv1 = uv1 - offset * QUALITY(i);
            }
            if !reached2 {
                uv2 = uv2 + offset * QUALITY(i);
            }

            // If both sides have been reached, stop the exploration.
            if reachedBoth {
                break;
            }
        }
    }

    // Compute the distances to each side edge of the edge segment
    var distance1 = select(texCoord.y - uv1.y, texCoord.x - uv1.x, isHorizontal);
    var distance2 = select(uv2.y - texCoord.y, uv2.x - texCoord.x, isHorizontal);

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

    // Return subpixel texCoord offset
    if (!correctVariation) {
        return vec2f(0.0);
    } else if isHorizontal {
        return vec2f(0.0, pixelOffset * stepLength);
    } else {
        return vec2f(pixelOffset * stepLength, 0.0);
    }
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
    if lumaRange < max(EDGE_THRESHOLD_MIN, lumaMax * EDGE_THRESHOLD_MAX) {
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

    // Determine how steep the edge is, 0 means fully horizonal/vertical, 1 means diagonal
    var steepness = 0.0;
    if abs(diffuseDirection.x) > abs(diffuseDirection.y) {
        steepness = abs(diffuseDirection.y / diffuseDirection.x);
    } else {
        steepness = abs(diffuseDirection.x / diffuseDirection.y);
    }

    steepness = min(steepness * 1.0, 1.0);

    // Calculate gradient on both sides of the current pixel
    var luma1 = select(lumaW, lumaS, isHorizontal);
    var luma2 = select(lumaE, lumaN, isHorizontal);    // Compute gradients in this direction.
    let gradient1 = luma1 - lumaCenter;
    let gradient2 = luma2 - lumaCenter;

    // Maintain ridges and thin lines. This is inspired by AXAA's 2nd enhancement, except we also apply it to negative edges and do a smooth transition instead of a threshold.
    // Note that we can diminish quite hard, because the neighbouring pixels likely get diffused in the direction of the edge (this is one of our advantages over fxaa).
    var edgeOffsetFactor = (1.0 - steepness) * min(1.0, f32(USE_EDGE_SEARCH));
    if sign(gradient1) == sign(gradient2) {
        // This is a ridge or a valley, e.g. a thin line. We want to presereve these.
        let ridgeness = min(abs(gradient1), abs(gradient2));
        let diminish_factor = 1.0 - (min(1.0, 10 * ridgeness));
        edgeOffsetFactor *= diminish_factor;
        diffuseStrength *= diminish_factor;
        // TODO: diminish edgeOffsetFactor faster
    }

    // For long edges, the diffusion has to be huge to remove the jaggies. What algorithms like FXAA do instead, is detect
    // the length of the edge segment (successive horizontal/vertical pixels), and the use that to calculate the subpixel
    // texture coordinate offset, perpendicular to the edge. So technically this is diffusion perpendicular to the edge,
    // but in a controlled manner to smooth the step/jaggy.
    var subpixelEdgeOffset = vec2f(0.0);
    if true {//(diffuseStrength >= 0.0) {
        subpixelEdgeOffset = get_subpixel_offset_for_long_edge(tex, smp, texCoord, pixelStep, isHorizontal, lumaCenter, luma1, luma2);
    }

    // The step to take for the diffusion effect (blur in the direction of the
    // edge). Note that for diagonal-ish lines, the most blur is obtained when
    // stepping halfway to the next pixel, i.e. 0.707, because then the
    // neighbour pixels are taken into account more. Let's use no more than 0.6
    // because then for horizontal lines, the max diffusion kernel is
    // effectively [0.6, 2 * 0.5, 0.6] which is still somewhat bell-shaped.
    // Actually, if we use 0.5, we trade a bit more smoothness for perceived sharpness.
    // Make its 0.51 so it does not look like some sort of offset.
    let max_step_size = 0.51;
    let diffuseStep = diffuseDirection * pixelStep * (max_step_size * diffuseStrength);

    // Compose the three texture coordinates, combining the ede-offset with the diffusion componennt, depending on the steepness of the edge.
    let texCoord0 = texCoord + subpixelEdgeOffset;
    let texCoord1 = texCoord - diffuseStep;
    let texCoord2 = texCoord + diffuseStep;

    // We mix the effects of the edge-search (FXAA 311 method) with the directional diffusion.
    // The factor below determines their ratio. We base it off the subpixelEdgeOffset,
    // which goes towards 0.5 for horizontal/vertical edges, and towards 0 for diagonal edges.
    // The multiplier (2.0) is actually relatively invariant for the end result.
    let diffuseVsEdge = sqrt(min(1.0, length(2.0 * subpixelEdgeOffset / pixelStep)));

    // Sample the final color
    var finalColor = vec3f(0.0);
    finalColor += diffuseVsEdge * textureSampleLevel(tex, smp, texCoord0, 0.0).rgb;
    finalColor += (1.0 - diffuseVsEdge) * 0.5 * textureSampleLevel(tex, smp, texCoord1, 0.0).rgb;
    finalColor += (1.0 - diffuseVsEdge) * 0.5 * textureSampleLevel(tex, smp, texCoord2, 0.0).rgb;

    return vec4f(finalColor, centerSample.a);
}
