fn aa_shader(
    tex: texture_2d<f32>,
    smp: sampler,
    fragcoord: vec2<f32>,
) -> vec4<f32> {

    let resolution = vec2<f32>(textureDimensions(tex));
    let texcoord = fragcoord / resolution;

    return textureSample(tex, smp, texcoord);
}
