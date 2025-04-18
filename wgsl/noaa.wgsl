// A shader that just copies the pixels.

fn aaShader(
    tex: texture_2d<f32>,
    smp: sampler,
    texCoord: vec2<f32>,
    scaleFactor: f32,
) -> vec4<f32> {

    //let resolution = vec2<f32>(textureDimensions(tex));
    //let fragCoord = texCoord * resolution;

    return textureSample(tex, smp, texCoord);
}
