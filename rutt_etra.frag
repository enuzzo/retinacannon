uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uRuttWave;
uniform float uAsciiDensity;
uniform int uEffectMode;
uniform int uViewMode;
uniform float uCameraAspect;

#define LINES 72.0
#define LINE_WIDTH 0.0015
#define EXTRUSION 0.055
#define CRT_CURVATURE 0.065
#define NOISE_STRENGTH 0.020
#define PI 3.14159265

// Letter bitmaps are derived from font8x8_basic (public domain):
// https://github.com/dhepper/font8x8/blob/master/font8x8_basic.h
const int FONT_UPPER[26][8] = int[26][8](
    int[8](12, 30, 51, 51, 63, 51, 51, 0),
    int[8](63, 102, 102, 62, 102, 102, 63, 0),
    int[8](60, 102, 3, 3, 3, 102, 60, 0),
    int[8](31, 54, 102, 102, 102, 54, 31, 0),
    int[8](127, 70, 22, 30, 22, 70, 127, 0),
    int[8](127, 70, 22, 30, 22, 6, 15, 0),
    int[8](60, 102, 3, 3, 115, 102, 124, 0),
    int[8](51, 51, 51, 63, 51, 51, 51, 0),
    int[8](30, 12, 12, 12, 12, 12, 30, 0),
    int[8](120, 48, 48, 48, 51, 51, 30, 0),
    int[8](103, 102, 54, 30, 54, 102, 103, 0),
    int[8](15, 6, 6, 6, 70, 102, 127, 0),
    int[8](99, 119, 127, 127, 107, 99, 99, 0),
    int[8](99, 103, 111, 123, 115, 99, 99, 0),
    int[8](28, 54, 99, 99, 99, 54, 28, 0),
    int[8](63, 102, 102, 62, 6, 6, 15, 0),
    int[8](30, 51, 51, 51, 59, 30, 56, 0),
    int[8](63, 102, 102, 62, 54, 102, 103, 0),
    int[8](30, 51, 7, 14, 56, 51, 30, 0),
    int[8](63, 45, 12, 12, 12, 12, 30, 0),
    int[8](51, 51, 51, 51, 51, 51, 63, 0),
    int[8](51, 51, 51, 51, 51, 30, 12, 0),
    int[8](99, 99, 99, 107, 127, 119, 99, 0),
    int[8](99, 99, 54, 28, 28, 54, 99, 0),
    int[8](51, 51, 51, 30, 12, 12, 30, 0),
    int[8](127, 99, 49, 24, 76, 102, 127, 0)
);

const int FONT_LOWER[26][8] = int[26][8](
    int[8](0, 0, 30, 48, 62, 51, 110, 0),
    int[8](7, 6, 6, 62, 102, 102, 59, 0),
    int[8](0, 0, 30, 51, 3, 51, 30, 0),
    int[8](56, 48, 48, 62, 51, 51, 110, 0),
    int[8](0, 0, 30, 51, 63, 3, 30, 0),
    int[8](28, 54, 6, 15, 6, 6, 15, 0),
    int[8](0, 0, 110, 51, 51, 62, 48, 31),
    int[8](7, 6, 54, 110, 102, 102, 103, 0),
    int[8](12, 0, 14, 12, 12, 12, 30, 0),
    int[8](48, 0, 48, 48, 48, 51, 51, 30),
    int[8](7, 6, 102, 54, 30, 54, 103, 0),
    int[8](14, 12, 12, 12, 12, 12, 30, 0),
    int[8](0, 0, 51, 127, 127, 107, 99, 0),
    int[8](0, 0, 31, 51, 51, 51, 51, 0),
    int[8](0, 0, 30, 51, 51, 51, 30, 0),
    int[8](0, 0, 59, 102, 102, 62, 6, 15),
    int[8](0, 0, 110, 51, 51, 62, 48, 120),
    int[8](0, 0, 59, 110, 102, 6, 15, 0),
    int[8](0, 0, 62, 3, 30, 48, 31, 0),
    int[8](8, 12, 62, 12, 12, 44, 24, 0),
    int[8](0, 0, 51, 51, 51, 51, 110, 0),
    int[8](0, 0, 51, 51, 51, 30, 12, 0),
    int[8](0, 0, 99, 107, 127, 127, 54, 0),
    int[8](0, 0, 99, 54, 28, 54, 99, 0),
    int[8](0, 0, 51, 51, 51, 62, 48, 31),
    int[8](0, 0, 63, 25, 12, 38, 63, 0)
);

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

vec3 liftShadows(vec3 color) {
    float luma = getLuma(color);
    float shadow = 1.0 - smoothstep(0.08, 0.58, luma);
    float gamma = mix(1.0, 0.72, shadow);
    return clamp(pow(color, vec3(gamma)), 0.0, 1.0);
}

float liftShadowLuma(float luma) {
    float shadow = 1.0 - smoothstep(0.08, 0.58, luma);
    float gamma = mix(1.0, 0.72, shadow);
    return clamp(pow(luma, gamma), 0.0, 1.0);
}

vec2 warpCRT(vec2 uv) {
    vec2 p = uv * 2.0 - 1.0;
    float r2 = dot(p, p);
    p *= 1.0 + CRT_CURVATURE * r2;
    return p * 0.5 + 0.5;
}

vec2 mapCameraAspect(vec2 uv, float targetAspect) {
    float srcAspect = max(uCameraAspect, 0.1);
    vec2 outUV = uv;
    if (targetAspect > srcAspect) {
        float scaleY = srcAspect / targetAspect;
        outUV.y = (uv.y - 0.5) * scaleY + 0.5;
    } else if (targetAspect < srcAspect) {
        float scaleX = targetAspect / srcAspect;
        outUV.x = (uv.x - 0.5) * scaleX + 0.5;
    }
    return outUV;
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

int letterRowBits(int letterIndex, int row) {
    int r = clamp(row, 0, 7);
    if (letterIndex < 26) {
        return FONT_UPPER[letterIndex][r];
    }
    return FONT_LOWER[letterIndex - 26][r];
}

float glyphLetterInk(vec2 cellUV, int letterIndex) {
    vec2 uv = clamp(cellUV, 0.0, 0.999);
    int col = int(floor(uv.x * 8.0));
    int row = int(floor((1.0 - uv.y) * 8.0));
    int bits = letterRowBits(clamp(letterIndex, 0, 51), row);
    int ink = (bits >> col) & 1;
    return float(ink);
}

vec3 renderRutt(vec2 uv, vec2 fragCoord) {
    vec2 sampleBase = uv;
    if (uColorMode == 2) {
        sampleBase += vec2(
            sin((uv.y + iTime * 0.20) * 16.0),
            cos((uv.x - iTime * 0.16) * 13.0)
        ) * 0.006;
    } else if (uColorMode == 3) {
        vec2 p = uv - 0.5;
        float r = length(p);
        float a = atan(p.y, p.x);
        a += sin(r * 8.0 - iTime * 0.18) * 0.032;
        sampleBase = 0.5 + vec2(cos(a), sin(a)) * r;
        sampleBase += vec2(
            cos((sampleBase.y + iTime * 0.10) * 9.0),
            sin((sampleBase.x - iTime * 0.09) * 8.0)
        ) * 0.0035;
    }
    sampleBase = safeUV(sampleBase);

    float hJitter = (hash12(vec2(floor(sampleBase.y * LINES), floor(iTime * 35.0))) - 0.5) * 0.0025;
    sampleBase.x = clamp(sampleBase.x + hJitter, 0.0, 1.0);

    float baseI = floor(sampleBase.y * LINES);
    float normI = baseI / LINES;
    vec2 sampleUV = vec2(sampleBase.x, normI);

    float px = 1.0 / iResolution.x;
    float lumaRaw =
        getLuma(texture(iChannel0, safeUV(sampleUV + vec2(-px * 2.0, 0.0))).rgb) * 0.1 +
        getLuma(texture(iChannel0, safeUV(sampleUV + vec2(-px, 0.0))).rgb) * 0.2 +
        getLuma(texture(iChannel0, safeUV(sampleUV)).rgb) * 0.4 +
        getLuma(texture(iChannel0, safeUV(sampleUV + vec2(px, 0.0))).rgb) * 0.2 +
        getLuma(texture(iChannel0, safeUV(sampleUV + vec2(px * 2.0, 0.0))).rgb) * 0.1;
    float luma = liftShadowLuma(lumaRaw);

    float lineY = normI + luma * (EXTRUSION * uRuttWave);
    float dist = abs(sampleBase.y - lineY);
    float baseDist = abs(sampleBase.y - normI);

    float lineAlpha = 1.0 - smoothstep(0.0, LINE_WIDTH, dist);
    float glow = (1.0 - smoothstep(0.0, LINE_WIDTH * 5.0, dist)) * 0.24 * luma;
    float scaffold = 1.0 - smoothstep(0.0, LINE_WIDTH * 1.6, baseDist);
    float haze = (1.0 - smoothstep(0.0, LINE_WIDTH * 12.0, dist)) * 0.08 * luma;

    vec3 camColor = liftShadows(texture(iChannel0, safeUV(sampleUV)).rgb);
    vec3 lineCol;
    if (uColorMode == 0) {
        lineCol = vec3(1.08);
    } else if (uColorMode == 1) {
        lineCol = pow(camColor, vec3(0.90)) * 1.92;
    } else if (uColorMode == 2) {
        float shift = 0.0022;
        float r = liftShadows(texture(iChannel0, safeUV(sampleUV + vec2(shift, 0.0))).rgb).r;
        float g = camColor.g;
        float b = liftShadows(texture(iChannel0, safeUV(sampleUV + vec2(-shift, 0.0))).rgb).b;
        lineCol = vec3(r, g, b) * vec3(1.65, 1.18, 1.72);
    } else {
        vec2 slowUV = safeUV(sampleUV + vec2(
            sin((normI + iTime * 0.11) * 7.5),
            cos((sampleUV.x - iTime * 0.09) * 6.2)
        ) * 0.004);
        vec3 melt = liftShadows(texture(iChannel0, slowUV).rgb).bgr;
        lineCol = vec3(
            melt.r * 1.45 + melt.g * 0.20,
            melt.g * 1.08 + melt.b * 0.15,
            melt.b * 1.40 + melt.r * 0.18
        );
    }

    float scan = 0.97 + 0.03 * sin((sampleBase.y * iResolution.y) * PI);
    float grille = 0.985 + 0.015 * sin((sampleBase.x * iResolution.x) * 1.7);
    float vignette = pow(clamp(16.0 * sampleBase.x * sampleBase.y * (1.0 - sampleBase.x) * (1.0 - sampleBase.y), 0.0, 1.0), 0.20);
    float noise = (hash12(fragCoord + vec2(iTime * 48.0, iTime * 17.0)) - 0.5) * NOISE_STRENGTH;

    vec3 color = lineCol * (lineAlpha + glow + haze);
    color += lineCol * scaffold * (0.06 + 0.14 * luma);
    color *= scan * grille * mix(0.72, 1.0, vignette);
    color *= 1.34;
    color += noise;
    return clamp(color, 0.0, 1.0);
}

vec3 renderAscii(vec2 uv, vec2 fragCoord) {
    float charAspect = 1.85;
    float density = clamp(uAsciiDensity, 1.00, 6.00);
    vec2 grid = vec2(94.0 * density, floor(94.0 * density * iResolution.y / iResolution.x / charAspect));
    grid.y = max(grid.y, 18.0);

    vec2 cell = uv * grid;
    vec2 cellId = floor(cell);
    vec2 cellUV = fract(cell);
    vec2 sampleUV = safeUV((cellId + 0.5) / grid);

    vec3 camColor = liftShadows(texture(iChannel0, sampleUV).rgb);
    float luma = getLuma(camColor);
    float boosted = clamp(pow(luma, 0.86), 0.0, 1.0);

    bool letters = (uColorMode >= 2);
    bool invertMode = (uColorMode >= 2);
    float tone = invertMode ? (1.0 - boosted) : boosted;

    float glyph;
    if (letters) {
        float jitter = (hash12(cellId * vec2(0.71, 1.17)) - 0.5) * 0.22;
        float idxF = clamp(tone + jitter, 0.0, 1.0);
        int letterIndex = int(floor(idxF * 52.0));
        letterIndex = clamp(letterIndex, 0, 51);
        glyph = glyphLetterInk(cellUV, letterIndex);
    } else {
        int level = int(clamp(floor(tone * 8.0), 0.0, 7.0));
        vec2 p = cellUV - 0.5;
        p.y *= charAspect;
        glyph = glyphSymbolInk(p, level);
    }

    vec3 tint;
    if (uColorMode == 0) {
        tint = camColor;
    } else if (uColorMode == 1) {
        tint = vec3(boosted);
    } else if (uColorMode == 2) {
        tint = vec3(1.0 - boosted);
    } else {
        tint = 1.0 - camColor.bgr;
        tint = pow(tint, vec3(0.86)) * vec3(1.18, 1.08, 1.25);
    }

    float scan = 0.93 + 0.07 * sin(fragCoord.y * PI);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.25);
    float noise = (hash12(cellId + floor(iTime * 18.0)) - 0.5) * 0.040;

    float bgLevel = invertMode ? (0.10 + (1.0 - tone) * 0.14) : (0.03 + tone * 0.04);
    vec3 color = vec3(bgLevel) * tint;
    color += tint * glyph * (0.45 + tone * 1.25);
    color += noise * (0.15 + glyph * 0.85);
    color *= scan * mix(0.40, 1.0, vignette);
    return clamp(color, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    if (uViewMode == 0) {
        uv = mapCameraAspect(uv, 16.0 / 9.0);
    } else if (uViewMode == 1) {
        uv = mapCameraAspect(uv, 4.0 / 3.0);
    } else {
        uv = mapCameraAspect(uv, 4.0 / 3.0);
        uv = warpCRT(uv);
    }
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color;
    if (uEffectMode == 0) {
        color = renderRutt(uv, fragCoord);
    } else {
        color = renderAscii(uv, fragCoord);
    }
    fragColor = vec4(color, 1.0);
}
