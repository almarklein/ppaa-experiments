// NVIDIA FXAA 3.11 - console version
//
// Original source code by TIMOTHY LOTTES
// https://gist.github.com/kosua20/0c506b81b3812ac900048059d2383126
//
// Converted to wgsl by Almar Klein (2025): https://github.com/almarklein/ppaa-experiments/blob/main/wgsl/fxaa3c.wgsl

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


fn rgb2luma(rgb: vec3<f32>) -> f32 {
    return sqrt(dot(rgb, vec3<f32>(0.299, 0.587, 0.114)));
}


@fragment
fn fs_main(varyings: Varyings) -> @location(0) vec4<f32> {

    let tex: texture_2d<f32> = colorTex;
    let samp: sampler = texSampler;
    let texCoord: vec2f = varyings.texCoord;

    let resolution = vec2<f32>(textureDimensions(tex));
    let inverseScreenSize = 1.0 / resolution.xy;

    let fxaaConsolePosPos = vec4f(texCoord - inverseScreenSize, texCoord + inverseScreenSize);
    let fxaaConsoleRcpFrameOpt = 0.5 * vec4f(-inverseScreenSize, inverseScreenSize);
    let fxaaConsoleRcpFrameOpt2 = 2.0 * vec4f(-inverseScreenSize, inverseScreenSize);
    const fxaaConsoleEdgeSharpness = 8.0;

    let lumaNw: f32 = rgb2luma(textureSampleLevel(tex, samp, fxaaConsolePosPos.xy, 0.0).rgb);
    let lumaSw: f32 = rgb2luma(textureSampleLevel(tex, samp, fxaaConsolePosPos.xw, 0.0).rgb);
    var lumaNe: f32 = rgb2luma(textureSampleLevel(tex, samp, fxaaConsolePosPos.zy, 0.0).rgb);
    let lumaSe: f32 = rgb2luma(textureSampleLevel(tex, samp, fxaaConsolePosPos.zw, 0.0).rgb);

    let rgbyM: vec4f = textureSampleLevel(tex, samp, texCoord.xy, 0.0);
    let lumaM: f32 = rgb2luma(rgbyM.rgb);

    let lumaMaxNwSw: f32 = max(lumaNw, lumaSw);
    lumaNe += 1.0/384.0; // WUT
    let lumaMinNwSw: f32 = min(lumaNw, lumaSw);
    let lumaMaxNeSe: f32 = max(lumaNe, lumaSe);
    let lumaMinNeSe: f32 = min(lumaNe, lumaSe);
    let lumaMax: f32 = max(lumaMaxNeSe, lumaMaxNwSw);
    let lumaMin: f32 = min(lumaMinNeSe, lumaMinNwSw);

    let lumaMaxScaled: f32 = lumaMax * EDGE_THRESHOLD_MAX;
    let lumaMinM: f32 = min(lumaMin, lumaM);
    let lumaMaxScaledClamped: f32 = max(EDGE_THRESHOLD_MIN, lumaMaxScaled);
    let lumaMaxM: f32 = max(lumaMax, lumaM);
    let dirSwMinusNe: f32 = lumaSw - lumaNe;
    let lumaMaxSubMinM: f32 = lumaMaxM - lumaMinM;
    let dirSeMinusNw: f32 = lumaSe - lumaNw;
    if(lumaMaxSubMinM < lumaMaxScaledClamped) { return rgbyM; }

    var dir: vec2f;
    dir.x = dirSwMinusNe + dirSeMinusNw;
    dir.y = dirSwMinusNe - dirSeMinusNw;

    let dir1: vec2f = normalize(dir.xy);
    let rgbyN1: vec4f = textureSampleLevel(tex, samp, texCoord - dir1 * fxaaConsoleRcpFrameOpt.zw, 0.0);
    let rgbyP1: vec4f = textureSampleLevel(tex, samp, texCoord + dir1 * fxaaConsoleRcpFrameOpt.zw, 0.0);

    let dirAbsMinTimesC: f32 = min(abs(dir1.x), abs(dir1.y)) * fxaaConsoleEdgeSharpness;
    let dir2: vec2f = clamp(dir1.xy / dirAbsMinTimesC, vec2f(-2.0), vec2f(2.0));
    let rgbyN2: vec4f = textureSampleLevel(tex, samp, texCoord - dir2 * fxaaConsoleRcpFrameOpt2.zw, 0.0);
    let rgbyP2: vec4f = textureSampleLevel(tex, samp, texCoord + dir2 * fxaaConsoleRcpFrameOpt2.zw, 0.0);
    let rgbyA: vec4f = rgbyN1 + rgbyP1;
    var rgbyB: vec4f = ((rgbyN2 + rgbyP2) * 0.25) + (rgbyA * 0.25);

    let lumaB = rgb2luma(rgbyB.rgb);
    let twoTap = (lumaB < lumaMin) || (lumaB > lumaMax);
    if(twoTap) {
        rgbyB = vec4f(rgbyA.rgb * 0.5, rgbyB.a);
    }
    return rgbyB;
}
