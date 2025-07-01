// ddaa1.wgsl version 1.1
//
// Directional Diffusion Anti Aliasinng (DDAA) version 1: Smooth along the edges based on Scharr kernel.
//
// v0: original (2013): https://github.com/vispy/experimental/blob/master/fsaa/ddaa.glsl
// v1: ported to wgsl and tweaked (2025): https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/ddaa1.wgsl
//
// This is the predecessor to ddaa2. It is included for comparison, and because its simpler and faster than ddaa2.

// ========== DDAA CONFIG ==========

// The strength of the diffusion.
const DDAA_STRENGTH = 3.0;


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
    // if lumaRange < max(EDGE_THRESHOLD_MIN, lumaMax * EDGE_THRESHOLD_MAX) {
    //     return centerSample;
    // }

    // Combine the four edges lumas (using intermediary variables for future computations with the same values).
    let lumaSUp = lumaS + lumaN;
    let lumaWRight = lumaW + lumaE;
    let lumaWCorners = lumaSW + lumaNW;

    // Same for corners
    let lumaSCorners = lumaSW + lumaSE;
    let lumaECorners = lumaSE + lumaNE;
    let lumaNCorners = lumaNE + lumaNW;

    // Is the local edge horizontal or vertical ?
    let edgeHorizontal = abs(-2.0 * lumaW + lumaWCorners) + abs(-2.0 * lumaCenter + lumaSUp) * 2.0 + abs(-2.0 * lumaE + lumaECorners);
    let edgeVertical = abs(-2.0 * lumaN + lumaNCorners) + abs(-2.0 * lumaCenter + lumaWRight) * 2.0 + abs(-2.0 * lumaS + lumaSCorners);
    let isHorizontal = (edgeHorizontal >= edgeVertical);
    //let isHorizontal = (abs(diffuseDirection.x) >= abs(diffuseDirection.y)); -> different, resulting in wrong ridge detection

     // Calculate gradient on both sides of the current pixel
    var luma1 = select(lumaW, lumaS, isHorizontal);
    var luma2 = select(lumaE, lumaN, isHorizontal);  // Compute gradients in this direction.
    let gradient1 = luma1 - lumaCenter;
    let gradient2 = luma2 - lumaCenter;

    // Calculate the image gradient using the Scharr kernel, which is (relatively) rotationally invariant.
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

    // Maintain ridges and thin lines. This is inspired by AXAA's 2nd enhancement, except we also apply it to negative edges and do a smooth transition instead of a threshold.
    // Note that we can diminish quite hard, because the neighbouring pixels likely get diffused in the direction of the edge (this is one of our advantages over fxaa).
    if sign(gradient1) == sign(gradient2) {
        // This is a ridge or a valley, e.g. a thin line. We want to presereve these.
        let ridgeness = min(abs(gradient1), abs(gradient2));
        let diminish_factor = 1.0 - (min(1.0, 10 * ridgeness));
        diffuseStrength *= diminish_factor;
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

    // Compose the texture coordinates
    let texCoord1 = texCoord - diffuseStep;
    let texCoord2 = texCoord + diffuseStep;

    // Sample the final color
    var finalColor = vec3f(0.0);
    finalColor += 0.5 * textureSampleLevel(tex, smp, texCoord1, 0.0).rgb;
    finalColor += 0.5 * textureSampleLevel(tex, smp, texCoord2, 0.0).rgb;

    return vec4f(finalColor, centerSample.a);
}
