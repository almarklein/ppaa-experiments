vec4 aa_shader(sampler2D tex, vec2 fragcoord) {
    vec2 resolution = vec2(textureSize(tex, 0).xy);
    vec2 texcoord = fragcoord / resolution;
    return texture(tex, coord);
}