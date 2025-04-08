// Marching cube (inspired) antialiasing.
// Proof of concept, probably not the right way to go.
// Copyright (C) 2013 Almar Klein


vec4 contributions(float iso, vec4 v0, vec4 v1, vec4 v2, vec4 v3)
{
    // Calculate strength
    float s0 = 1.0 / (abs(v0.a-iso) + 0.0001);
    float s1 = 1.0 / (abs(v1.a-iso) + 0.0001);
    float s2 = 1.0 / (abs(v2.a-iso) + 0.0001);

    // Normalize them
    //float norm = s0+s1+s2;
    //float norm = length(vec3(s0,s1,s2));
    float norm = 1*s0 + s1 + s2;

    s0 = s0/norm; s1 = s1/norm; s2=s2/norm;
    vec4 res = s0*v0 + s1*v1 + s2*v2;
    res.a = s0 + s1 + s2;
    return res;
}

vec4 aa_shader(sampler2D tex, vec2 texcoord, vec2 resolution) {

    // Parameters
    float ORIGINALITY = 0.25;
    float RIDGE_ENHANCEMENT = 2.0; // Scaling this with NPASSES works pretty good

    // Init step size in tex coords
    float dx = 1.0/resolution.x;
    float dy = 1.0/resolution.y;

    // Get centre location
    vec2 pos = texcoord;

    // Get center pixel. This is a corner cell for each of the four
    // cells that we will visit
    vec4 v0 = texture(tex, pos);

    //gl_FragColor = v0;  return;


    // Get other samples
    vec4 vl = texture(tex, pos+vec2(-dx, 0));
    vec4 vr = texture(tex, pos+vec2(+dx, 0));
    vec4 vu = texture(tex, pos+vec2(0, -dy));
    vec4 vd = texture(tex, pos+vec2(0, +dy));
    //
    vec4 vlu = texture(tex, pos+vec2(-dx, -dy));
    vec4 vru = texture(tex, pos+vec2(+dx, -dy));
    vec4 vld = texture(tex, pos+vec2(-dx, +dy));
    vec4 vrd = texture(tex, pos+vec2(+dx, +dy));

    // Calculate their respecive strength/lumincance/...
    v0.a = length(v0.rgb);
    vl.a = length(vl.rgb);  vr.a = length(vr.rgb);
    vu.a = length(vu.rgb);  vd.a = length(vd.rgb);
    vlu.a = length(vlu.rgb);  vru.a = length(vru.rgb);
    vld.a = length(vld.rgb);  vrd.a = length(vrd.rgb);

    // Calculate iso value for this fragment: the mean of the neightborhood
    float iso = v0.a + vl.a + vr.a + vu.a + vd.a + vlu.a + vru.a + vld.a + vrd.a;
    iso = iso / 9.0;

    // Initialise result
    vec4 result = v0;
    result.a = 0.0;//ORIGINALITY / (abs(v0.a-iso) + 0.0001);
    result.rgb = result.rgb * result.a;

    // Initialize variables
    vec4 v1;  vec4 v2;  vec4 v3;

    // Process cell: upper left
    v1 = vl;  v2 = vu;  v3 = vlu;
    if ((v0.a < iso) && (v1.a > iso) && (v2.a > iso))
    {
        if ( v3.a > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }
    if ((v0.a > iso) && (v1.a < iso) && (v2.a < iso))
    {
        if ( v3.a < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }

    // Process cell: upper right
    v1 = vr;  v2 = vu;  v3 = vru;
    if ((v0.a < iso) && (v1.a > iso) && (v2.a > iso))
    {
        if ( v3.a > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }
    if ((v0.a > iso) && (v1.a < iso) && (v2.a < iso))
    {
        if ( v3.a < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }

    // Process cell: lower left
    v1 = vl;  v2 = vd;  v3 = vld;
    if ((v0.a < iso) && (v1.a > iso) && (v2.a > iso))
    {
        if ( v3.a > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }
    if ((v0.a > iso) && (v1.a < iso) && (v2.a < iso))
    {
        if ( v3.a < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }

    // Process cell: lower right
    v1 = vr;  v2 = vd;  v3 = vrd;
    if ((v0.a < iso) && (v1.a > iso) && (v2.a > iso))
    {
        if ( v3.a > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) > iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }
    if ((v0.a > iso) && (v1.a < iso) && (v2.a < iso))
    {
        if ( v3.a < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
            result += vec4(RIDGE_ENHANCEMENT * v0.rgb, RIDGE_ENHANCEMENT);
        } else if ( 0.25*(v0.a+v1.a+v2.a+v3.a) < iso ) {
            result += contributions(iso, v0, v1, v2, v3);
        }
    }

    if (result.a > 0.0)
        return result / result.a;
    else
        return vec4(v0.rgb, 1.0);

}