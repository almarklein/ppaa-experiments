/**
Basic FXAA implementation based on the code on geeks3d.com with the
modification that the texture2DLod stuff was removed since it's
unsupported by WebGL.

Converted to wgsl, and adjusted for ppaa-research framework by Almar Klein (2025).
https://github.com/almarklein/ppaa-research/blob/main/wgsl/fxaa2.wgsl

--

From:
https://github.com/mitsuhiko/webgl-meincraft

Copyright (c) 2011 by Armin Ronacher.

Some rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.

    * The names of the contributors may not be used to endorse or
      promote products derived from this software without specific
      prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

const FXAA_REDUCE_MIN: f32 = 1.0 / 128.0;
const FXAA_REDUCE_MUL: f32 = 1.0 / 8.0;
const FXAA_SPAN_MAX: f32 = 8.0;

fn aaShader(
    tex: texture_2d<f32>,
    smp: sampler,
    texCoord: vec2<f32>,
    scaleFactor: f32,  // assumed to be 1
) -> vec4<f32> {

    let resolution = vec2<f32>(textureDimensions(tex));
    let fragcoord = texCoord * resolution;

    let v_rgbNW = texCoord + vec2<f32>(-1.0,  1.0);
    let v_rgbNE = texCoord + vec2<f32>( 1.0,  1.0);
    let v_rgbSW = texCoord + vec2<f32>(-1.0, -1.0);
    let v_rgbSE = texCoord + vec2<f32>( 1.0, -1.0);
    let v_rgbM  = texCoord;

    let inverseVP = vec2<f32>(1.0 / resolution.x, 1.0 / resolution.y);

    let rgbNW = textureSample(tex, smp, v_rgbNW).rgb;
    let rgbNE = textureSample(tex, smp, v_rgbNE).rgb;
    let rgbSW = textureSample(tex, smp, v_rgbSW).rgb;
    let rgbSE = textureSample(tex, smp, v_rgbSE).rgb;
    let texColor = textureSample(tex, smp, v_rgbM);
    let rgbM  = texColor.rgb;

    let luma = vec3<f32>(0.299, 0.587, 0.114);

    let lumaNW = dot(rgbNW, luma);
    let lumaNE = dot(rgbNE, luma);
    let lumaSW = dot(rgbSW, luma);
    let lumaSE = dot(rgbSE, luma);
    let lumaM  = dot(rgbM,  luma);

    let lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
    let lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));

    var dir = vec2<f32>(0.0, 0.0);
    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));

    let dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * (0.25 * FXAA_REDUCE_MUL), FXAA_REDUCE_MIN);
    let rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);

    dir = min(vec2<f32>(FXAA_SPAN_MAX, FXAA_SPAN_MAX),
              max(vec2<f32>(-FXAA_SPAN_MAX, -FXAA_SPAN_MAX),
              dir * rcpDirMin)) * inverseVP;

    let rgbA = 0.5 * (
        textureSample(tex, smp, fragcoord * inverseVP + dir * (1.0 / 3.0 - 0.5)).rgb +
        textureSample(tex, smp, fragcoord * inverseVP + dir * (2.0 / 3.0 - 0.5)).rgb
    );

    let rgbB = rgbA * 0.5 + 0.25 * (
        textureSample(tex, smp, fragcoord * inverseVP + dir * -0.5).rgb +
        textureSample(tex, smp, fragcoord * inverseVP + dir *  0.5).rgb
    );

    let lumaB = dot(rgbB, luma);

    var color: vec4<f32>;
    if (lumaB < lumaMin || lumaB > lumaMax) {
        color = vec4<f32>(rgbA, texColor.a);
    } else {
        color = vec4<f32>(rgbB, texColor.a);
    }
    return color;
}
