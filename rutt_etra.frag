uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uRuttWave;
uniform float uAsciiDensity;
uniform int uEffectMode;

#define LINES 84.0
#define LINE_WIDTH 0.0032
#define CRT_CURVATURE 0.065
#define NOISE_STRENGTH 0.022
#define PI 3.14159265

float getLuma(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 safeUV(vec2 uv) {
    return clamp(uv, vec2(0.001), vec2(0.999));
}

vec2 warpCRT(vec2 uv) {
    vec2 p = uv * 2.0 - 1.0;
    float r2 = dot(p, p);
    p *= 1.0 + CRT_CURVATURE * r2;
    return p * 0.5 + 0.5;
}

float segInk(vec2 p, vec2 a, vec2 b, float w) {
    vec2 pa = p - a;
    vec2 ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    float d = length(pa - ba * h);
    return 1.0 - smoothstep(w, w + 0.025, d);
}

float glyphSymbolInk(vec2 p, int level) {
    if (level == 0) {
        return 0.0;
    }
    if (level == 1) {
        return 1.0 - smoothstep(0.08, 0.11, length(p));
    }
    if (level == 2) {
        float d1 = 1.0 - smoothstep(0.07, 0.10, length(p - vec2(0.0, 0.20)));
        float d2 = 1.0 - smoothstep(0.07, 0.10, length(p + vec2(0.0, 0.20)));
        return max(d1, d2);
    }
    if (level == 3) {
        float v = 1.0 - smoothstep(0.04, 0.07, abs(p.x));
        float h = 1.0 - smoothstep(0.04, 0.07, abs(p.y));
        return max(v, h) * (1.0 - smoothstep(0.45, 0.52, length(p)));
    }
    if (level == 4) {
        float dA = abs(p.x - p.y) * 0.7071;
        float dB = abs(p.x + p.y) * 0.7071;
        float xa = 1.0 - smoothstep(0.04, 0.07, dA);
        float xb = 1.0 - smoothstep(0.04, 0.07, dB);
        return max(xa, xb);
    }
    if (level == 5) {
        float ring = abs(length(p) - 0.28);
        return 1.0 - smoothstep(0.04, 0.07, ring);
    }
    if (level == 6) {
        float v1 = 1.0 - smoothstep(0.035, 0.06, abs(p.x - 0.18));
        float v2 = 1.0 - smoothstep(0.035, 0.06, abs(p.x + 0.18));
        float h1 = 1.0 - smoothstep(0.035, 0.06, abs(p.y - 0.18));
        float h2 = 1.0 - smoothstep(0.035, 0.06, abs(p.y + 0.18));
        float c = 1.0 - smoothstep(0.04, 0.07, min(abs(p.x), abs(p.y)));
        return max(max(v1, v2), max(max(h1, h2), c));
    }
    float box = (1.0 - smoothstep(0.42, 0.48, abs(p.x))) * (1.0 - smoothstep(0.42, 0.48, abs(p.y)));
    return box;
}

float glyphLetterInk(vec2 p, int level) {
    if (level == 0) {
        return 0.0;
    }
    if (level == 1) { // I
        float v = segInk(p, vec2(0.0, -0.38), vec2(0.0, 0.38), 0.055);
        float t = segInk(p, vec2(-0.20, 0.38), vec2(0.20, 0.38), 0.045);
        float b = segInk(p, vec2(-0.20, -0.38), vec2(0.20, -0.38), 0.045);
        return max(v, max(t, b));
    }
    if (level == 2) { // L
        float v = segInk(p, vec2(-0.18, -0.38), vec2(-0.18, 0.38), 0.055);
        float b = segInk(p, vec2(-0.18, -0.38), vec2(0.24, -0.38), 0.045);
        return max(v, b);
    }
    if (level == 3) { // T
        float v = segInk(p, vec2(0.0, -0.38), vec2(0.0, 0.36), 0.055);
        float t = segInk(p, vec2(-0.28, 0.36), vec2(0.28, 0.36), 0.045);
        return max(v, t);
    }
    if (level == 4) { // A
        float l = segInk(p, vec2(-0.24, -0.38), vec2(0.0, 0.38), 0.055);
        float r = segInk(p, vec2(0.24, -0.38), vec2(0.0, 0.38), 0.055);
        float m = segInk(p, vec2(-0.12, 0.02), vec2(0.12, 0.02), 0.045);
        return max(max(l, r), m);
    }
    if (level == 5) { // R
        float v = segInk(p, vec2(-0.22, -0.38), vec2(-0.22, 0.38), 0.055);
        float t = segInk(p, vec2(-0.22, 0.38), vec2(0.16, 0.38), 0.045);
        float m = segInk(p, vec2(-0.22, 0.02), vec2(0.14, 0.02), 0.045);
        float r = segInk(p, vec2(0.16, 0.38), vec2(0.16, 0.02), 0.055);
        float d = segInk(p, vec2(-0.04, 0.02), vec2(0.22, -0.38), 0.050);
        return max(max(max(v, t), max(m, r)), d);
    }
    if (level == 6) { // M
        float l = segInk(p, vec2(-0.24, -0.38), vec2(-0.24, 0.38), 0.055);
        float r = segInk(p, vec2(0.24, -0.38), vec2(0.24, 0.38), 0.055);
        float d1 = segInk(p, vec2(-0.24, 0.38), vec2(0.0, -0.02), 0.050);
        float d2 = segInk(p, vec2(0.24, 0.38), vec2(0.0, -0.02), 0.050);
        return max(max(l, r), max(d1, d2));
    }
    // W
    float d1 = segInk(p, vec2(-0.28, 0.34), vec2(-0.10, -0.38), 0.050);
    float d2 = segInk(p, vec2(-0.10, -0.38), vec2(0.0, 0.06), 0.050);
    float d3 = segInk(p, vec2(0.0, 0.06), vec2(0.10, -0.38), 0.050);
    float d4 = segInk(p, vec2(0.10, -0.38), vec2(0.28, 0.34), 0.050);
    return max(max(d1, d2), max(d3, d4));
}

vec2 ruttModeWarp(vec2 uv, int mode, float waveCtl) {
    if (mode == 2) {
        float a = 0.008 + 0.015 * waveCtl;
        uv += vec2(
            sin((uv.y + iTime * 0.7) * 26.0),
            cos((uv.x - iTime * 0.4) * 23.0)
        ) * a;
    } else if (mode == 3) {
        vec2 p = uv - 0.5;
        float r = length(p);
        float ang = atan(p.y, p.x);
        ang += sin(r * 30.0 - iTime * 2.1) * (0.08 + 0.12 * waveCtl);
        uv = 0.5 + vec2(cos(ang), sin(ang)) * r;
        uv += vec2(
            cos((uv.y + iTime) * 42.0),
            sin((uv.x - iTime * 0.8) * 37.0)
        ) * (0.004 + 0.012 * waveCtl);
    }
    return safeUV(uv);
}

vec3 renderRutt(vec2 uv, vec2 fragCoord) {
    float waveCtl = clamp((uRuttWave - 0.40) / (3.80 - 0.40), 0.0, 1.0);
    vec2 warpedUV = ruttModeWarp(uv, uColorMode, waveCtl);

    float hJitter = (hash12(vec2(floor(warpedUV.y * LINES), floor(iTime * 35.0))) - 0.5) * 0.0025;
    warpedUV.x = clamp(warpedUV.x + hJitter, 0.0, 1.0);

    float baseI = floor(warpedUV.y * LINES);
    float normI = baseI / LINES;
    vec2 sampleUV = vec2(warpedUV.x, normI);

    float px = 1.0 / iResolution.x;
    float l0 = getLuma(texture(iChannel0, safeUV(sampleUV + vec2(-2.0 * px, 0.0))).rgb);
    float l1 = getLuma(texture(iChannel0, safeUV(sampleUV + vec2(-1.0 * px, 0.0))).rgb);
    float l2 = getLuma(texture(iChannel0, safeUV(sampleUV)).rgb);
    float l3 = getLuma(texture(iChannel0, safeUV(sampleUV + vec2( 1.0 * px, 0.0))).rgb);
    float l4 = getLuma(texture(iChannel0, safeUV(sampleUV + vec2( 2.0 * px, 0.0))).rgb);
    float luma = l0 * 0.08 + l1 * 0.22 + l2 * 0.40 + l3 * 0.22 + l4 * 0.08;

    float edge = abs(l4 - l0) + abs(l3 - l1);
    float waveFreq = mix(2.8, 18.0, waveCtl);
    float ridge = 0.5 + 0.5 * sin((sampleUV.x * waveFreq + normI * 11.0) + iTime * 0.7);
    float ridge2 = 0.5 + 0.5 * sin((sampleUV.x * waveFreq * 0.55 - normI * 17.0) - iTime * 1.1);
    float profile = pow(clamp(luma + edge * 0.75, 0.0, 1.0), mix(1.45, 0.62, waveCtl));
    float crest = profile * mix(0.55, 1.15, ridge * 0.7 + ridge2 * 0.3);
    float peakAmplitude = mix(0.035, 0.180, waveCtl);
    float lineY = normI + crest * peakAmplitude;

    float dist = abs(warpedUV.y - lineY);
    float lineAlpha = 1.0 - smoothstep(0.0, LINE_WIDTH * (1.0 + waveCtl * 0.5), dist);
    float glow = (1.0 - smoothstep(0.0, LINE_WIDTH * 8.0, dist)) * (0.22 + 0.40 * crest);

    vec3 camColor = texture(iChannel0, safeUV(sampleUV)).rgb;
    vec3 lineCol;
    if (uColorMode == 0) {
        lineCol = vec3(1.08);
    } else if (uColorMode == 1) {
        lineCol = pow(camColor, vec3(0.90)) * 1.90;
    } else if (uColorMode == 2) {
        float shift = (0.0018 + 0.0045 * waveCtl) * (0.50 + ridge);
        float r = texture(iChannel0, safeUV(sampleUV + vec2( shift, 0.0))).r;
        float g = texture(iChannel0, safeUV(sampleUV)).g;
        float b = texture(iChannel0, safeUV(sampleUV + vec2(-shift, 0.0))).b;
        lineCol = vec3(r, g, b) * vec3(1.55, 1.20, 1.75);
    } else {
        vec2 meltUV = safeUV(sampleUV + vec2(
            sin((normI + iTime * 0.8) * 38.0),
            cos((sampleUV.x - iTime * 0.6) * 30.0)
        ) * (0.004 + 0.010 * waveCtl));
        vec3 melt = texture(iChannel0, meltUV).bgr;
        lineCol = vec3(
            melt.r * 1.70 + melt.b * 0.15,
            melt.g * 1.05 + melt.r * 0.20,
            melt.b * 1.65 + melt.g * 0.20
        );
    }

    float scan = 0.97 + 0.03 * sin((warpedUV.y * iResolution.y) * PI);
    float grille = 0.985 + 0.015 * sin((warpedUV.x * iResolution.x) * 1.7);
    float vignette = pow(clamp(16.0 * warpedUV.x * warpedUV.y * (1.0 - warpedUV.x) * (1.0 - warpedUV.y), 0.0, 1.0), 0.20);
    float noise = (hash12(fragCoord + vec2(iTime * 53.0, iTime * 17.0)) - 0.5) * NOISE_STRENGTH;

    vec3 color = lineCol * (lineAlpha + glow);
    color *= scan * grille * mix(0.70, 1.0, vignette);
    color *= 1.40;
    color += noise;
    return clamp(color, 0.0, 1.0);
}

vec3 renderAscii(vec2 uv, vec2 fragCoord) {
    float charAspect = 1.85;
    float density = clamp(uAsciiDensity, 0.55, 2.40);
    vec2 grid = vec2(92.0 * density, floor(92.0 * density * iResolution.y / iResolution.x / charAspect));
    grid.y = max(grid.y, 18.0);

    vec2 cell = uv * grid;
    vec2 cellId = floor(cell);
    vec2 cellUV = fract(cell);
    vec2 sampleUV = (cellId + 0.5) / grid;

    if (uColorMode >= 2) {
        sampleUV += vec2(
            sin((cellId.y + iTime * 7.0) * 0.21),
            cos((cellId.x - iTime * 6.0) * 0.17)
        ) * 0.0016;
    }
    sampleUV = safeUV(sampleUV);

    vec3 camColor = texture(iChannel0, sampleUV).rgb;
    float luma = getLuma(camColor);
    float boosted = clamp(pow(luma, 0.85), 0.0, 1.0);
    int level = int(clamp(floor(boosted * 8.0), 0.0, 7.0));

    vec2 p = cellUV - 0.5;
    p.y *= charAspect;
    float ink = (uColorMode >= 2) ? glyphLetterInk(p, level) : glyphSymbolInk(p, level);

    bool mono = (uColorMode == 1 || uColorMode == 2);
    vec3 tint;
    if (uColorMode == 3) {
        tint = pow(camColor.bgr, vec3(0.82)) * vec3(1.30, 1.10, 1.45);
    } else if (mono) {
        tint = vec3(boosted);
    } else {
        tint = camColor;
    }

    float scan = 0.93 + 0.07 * sin(fragCoord.y * PI);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.25);
    float noise = (hash12(cellId + floor(iTime * 18.0)) - 0.5) * 0.045;

    vec3 color = tint * ink * (0.45 + boosted * 1.25);
    color += tint * (mono ? (0.03 + boosted * 0.07) : (0.02 + boosted * 0.05));
    color += noise * (0.15 + ink * 0.85);
    color *= scan * mix(0.40, 1.0, vignette);
    return clamp(color, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    uv = warpCRT(uv);
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color = (uEffectMode == 0) ? renderRutt(uv, fragCoord) : renderAscii(uv, fragCoord);
    fragColor = vec4(color, 1.0);
}
