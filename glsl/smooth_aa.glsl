// Antialiasing by simple Gaussian smoothing. Included for comparison.
// Copyright (C) 2013 Almar Klein


vec4 aa_shader(sampler2D tex, vec2 fragcoord) {

    vec2 resolution = vec2(textureSize(tex, 0).xy);
    vec2 texcoord = fragcoord / resolution;

    // Init value
    vec3 color = vec3(0.0, 0.0, 0.0);

    // Init kernel and number of steps
    //vec4 kernel = vec4(0.399, 0.242, 0.054, 0.004); // Gaussian sigma 1.0
    vec4 kernel = vec4(0.53, 0.22, 0.015, 0.00018); // Gaussian sigma 0.75
    //vec4 kernel = vec4(0.79, 0.11, 0.0026, 0.000001); // Gaussian sigma 0.5
    int sze = 3;

    // Init step size in tex coords
    float dx = 1.0 / resolution.x;
    float dy = 1.0 / resolution.y;

    // Convolve
    for (int y=-sze; y<sze+1; y++)
    {
        for (int x=-sze; x<sze+1; x++)
        {
            float k = kernel[int(abs(float(x)))] * kernel[int(abs(float(y)))];
            vec2 dpos = vec2(float(x)*dx, float(y)*dy);
            color += texture(tex, texcoord+dpos).rgb * k;
        }
    }
    return vec4(color.r, color.g, color.b, 1.0);

}
