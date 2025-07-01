// A shader that just copies the pixels.

@fragment
fn fs_main(varyings: Varyings) -> @location(0) vec4<f32> {

    //let resolution = vec2<f32>(textureDimensions(colorTex).xy);
    //let fragCoord = varyings.ttexCoord * resolution;

    return textureSample(colorTex, texSampler, varyings.texCoord);
}
