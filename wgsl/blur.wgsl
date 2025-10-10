// A shader that simply blurs the image a bit.
//
// The purpose of this shader is to demonstrate how blurring removes aliasing
// effects, but also has negative effects. It can be used to compare more
// advanced methods with. Plus it may be nice for benchmarking since this shader
// does a bit more than the noaa shader.


@fragment
fn fs_main(varyings: Varyings) -> @location(0) vec4<f32> {

    let tex: texture_2d<f32> = colorTex;
    let smp: sampler = texSampler;
    let texCoord: vec2f = varyings.texCoord;

    let resolution = vec2f(textureDimensions(tex));
    let pixelStep = 1.0 / resolution.xy;

    // Sample the center pixel
    let center: vec4f = textureSampleLevel(tex, smp, texCoord, 0.0);

    // Kernel weights, these correspond to a truncated Gaussian
    const w0 = 1.0;
    const w1 = 0.2493522;  // exp(-1/(2*sigma*sigma)), with sigma 0.6
    const w2 = w1 * w1;

    // Collect new color ...
    var color = vec3f(0.0);

    // Add contrbution of center pixel
    color = color + w0 * center.rgb;

    // Add contribution for four direct neightbours
    color = color + w1 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(0, 1)).rgb;
    color = color + w1 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, 0)).rgb;
    color = color + w1 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(0, -1)).rgb;
    color = color + w1 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, 0)).rgb;

    // Add contribution for four direct neightbours
    color = color + w2 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, 1)).rgb;
    color = color + w2 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, 1)).rgb;
    color = color + w2 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(-1, -1)).rgb;
    color = color + w2 * textureSampleLevel(tex, smp, texCoord, 0.0, vec2i(1, -1)).rgb;

    // Normalize and return final color
    color = color / (w0 + 4.0 * w1 + 4.0 * w2);
    return vec4f(color.rgb, center.a);
}
