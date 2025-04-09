// Directionally Localized antiAliasing
// Slides: http://and.intercon.ru/releases/talks/dlaagdc2011/slides/
//
// Original ver: facepuncherfromrussia (2011)
//
// Update   ver: ForserX (2018-2019)
// https://github.com/ForserX/DLAA/blob/master/dlaa.hlsl
//
// Converted to wgsl, and adjusted for ppaa-research framework by Almar Klein (2025).
// https://github.com/almarklein/ppaa-research/blob/main/wgsl/dlaa.wgsl


fn Luminance(rgb: vec3f) -> f32 {
    // Assuming HD luminance coefficients
    return dot(rgb, vec3f(0.2126, 0.7152, 0.0722));
}

fn aa_shader(
    tex: texture_2d<f32>,
    smp: sampler,
    fragcoord: vec2<f32>,
) -> vec4<f32> {

    let resolution = vec2<f32>(textureDimensions(tex));
    let invRes = 1.0 / resolution;
    let tc = fragcoord * invRes;

    let lambda: f32 = 3.0;
    let epsilon: f32 = 0.1;

    let center = textureSample(tex, smp, tc + vec2f( 0.0,  0.0) * invRes);
    let left_01 = textureSample(tex, smp, tc + vec2f(-1.5,  0.0) * invRes);
    let right_01 = textureSample(tex, smp, tc + vec2f(1.5, 0.0) * invRes);
    let top_01 = textureSample(tex, smp, tc + vec2f(0.0, -1.5) * invRes);
    let bottom_01 = textureSample(tex, smp, tc + vec2f(0.0, 1.5) * invRes);

    let w_h = 2.0 * (left_01 + right_01);
    let w_v = 2.0 * (top_01 + bottom_01);

    let left = textureSample(tex, smp, tc + vec2f(-1.0, 0.0) * invRes);
    let right = textureSample(tex, smp, tc + vec2f(1.0, 0.0) * invRes);
    let top = textureSample(tex, smp, tc + vec2f(0.0, -1.0) * invRes);
    let bottom = textureSample(tex, smp, tc + vec2f(0.0, 1.0) * invRes);

    let edge_h = abs(left + right - 2.0 * center) / 2.0;
    let edge_v = abs(top + bottom - 2.0 * center) / 2.0;

    let blurred_h = (w_h + 2.0 * center) / 6.0;
    let blurred_v = (w_v + 2.0 * center) / 6.0;

    let edge_h_lum = Luminance(edge_h.xyz);
    let edge_v_lum = Luminance(edge_v.xyz);
    let blurred_h_lum = Luminance(blurred_h.xyz);
    let blurred_v_lum = Luminance(blurred_v.xyz);

    let edge_mask_h = clamp((lambda * edge_h_lum - epsilon) / blurred_v_lum, 0.0, 1.0);
    let edge_mask_v = clamp((lambda * edge_v_lum - epsilon) / blurred_h_lum, 0.0, 1.0);

    var clr = center;
    clr = mix(clr, blurred_h, edge_mask_v);
    clr = mix(clr, blurred_v, edge_mask_h * 0.5);

    var h_blurs: array<vec4f, 8> = array<vec4f, 8>(
        textureSample(tex, smp, tc + vec2f(1.5, 0.0) * invRes), textureSample(tex, smp, tc + vec2f(3.5, 0.0) * invRes),
        textureSample(tex, smp, tc + vec2f(5.5, 0.0) * invRes), textureSample(tex, smp, tc + vec2f(7.5, 0.0) * invRes),
        textureSample(tex, smp, tc + vec2f(-1.5, 0.0) * invRes), textureSample(tex, smp, tc + vec2f(-3.5, 0.0) * invRes),
        textureSample(tex, smp, tc + vec2f(-5.5, 0.0) * invRes), textureSample(tex, smp, tc + vec2f(-7.5, 0.0) * invRes)
    );

    var v_blurs: array<vec4f, 8> = array<vec4f, 8>(
        textureSample(tex, smp, tc + vec2f(0.0, 1.5) * invRes), textureSample(tex, smp, tc + vec2f(0.0, 3.5) * invRes),
        textureSample(tex, smp, tc + vec2f(0.0, 5.5) * invRes), textureSample(tex, smp, tc + vec2f(0.0, 7.5) * invRes),
        textureSample(tex, smp, tc + vec2f(0.0, -1.5) * invRes), textureSample(tex, smp, tc + vec2f(0.0, -3.5) * invRes),
        textureSample(tex, smp, tc + vec2f(0.0, -5.5) * invRes), textureSample(tex, smp, tc + vec2f(0.0, -7.5) * invRes)
    );

    let long_edge_mask_h = clamp(
        (h_blurs[0].a + h_blurs[1].a + h_blurs[2].a + h_blurs[3].a + h_blurs[4].a + h_blurs[5].a + h_blurs[6].a + h_blurs[7].a) / 8.0 * 2.0 - 1.0,
        0.0, 1.0);
    let long_edge_mask_v = clamp(
        (v_blurs[0].a + v_blurs[1].a + v_blurs[2].a + v_blurs[3].a + v_blurs[4].a + v_blurs[5].a + v_blurs[6].a + v_blurs[7].a) / 8.0 * 2.0 - 1.0,
        0.0, 1.0);

    if (abs(long_edge_mask_h - long_edge_mask_v) > 0.2) {
        let long_blurred_h = (h_blurs[0] + h_blurs[1] + h_blurs[2] + h_blurs[3] + h_blurs[4] + h_blurs[5] + h_blurs[6] + h_blurs[7]) / 8.0;
        let long_blurred_v = (v_blurs[0] + v_blurs[1] + v_blurs[2] + v_blurs[3] + v_blurs[4] + v_blurs[5] + v_blurs[6] + v_blurs[7]) / 8.0;

        let lb_h_lum = Luminance(long_blurred_h.xyz);
        let lb_v_lum = Luminance(long_blurred_v.xyz);
        let center_lum = Luminance(center.xyz);
        let left_lum = Luminance(left.xyz);
        let right_lum = Luminance(right.xyz);
        let top_lum = Luminance(top.xyz);
        let bottom_lum = Luminance(bottom.xyz);

        var clr_v = center;
        var clr_h = center;

        let hx = clamp((lb_h_lum - top_lum) / (center_lum - top_lum), 0.0, 1.0);
        let vx = clamp((lb_v_lum - left_lum) / (center_lum - left_lum), 0.0, 1.0);
        let hy = clamp(1.0 + (lb_h_lum - center_lum) / (center_lum - bottom_lum), 0.0, 1.0);
        let vy = clamp(1.0 + (lb_v_lum - center_lum) / (center_lum - right_lum), 0.0, 1.0);

        let vhxy = vec4f(vx, vy, hx, hy);
        let safe_vhxy = select(vhxy, vec4f(1.0), vhxy == vec4f(0.0));

        clr_v = mix(left, clr_v, safe_vhxy.x);
        clr_v = mix(right, clr_v, safe_vhxy.y);
        clr_h = mix(top, clr_h, safe_vhxy.z);
        clr_h = mix(bottom, clr_h, safe_vhxy.w);

        clr = mix(clr, clr_v, long_edge_mask_v);
        clr = mix(clr, clr_h, long_edge_mask_h);
    }

    return clr;
}
