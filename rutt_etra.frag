uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uRuttWave;
uniform float uAsciiDensity;
uniform int uEffectMode;
uniform int uViewMode;
uniform float uCameraAspect;
uniform int uShowFps;
uniform float uFpsValue;
uniform float uPixelSize;
uniform float uMotionLevel;
uniform float uPresenceScale;
uniform float uPresenceCX;
uniform float uPresenceCY;

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

const int FONT_DIGITS[10][8] = int[10][8](
    int[8](62, 99, 115, 123, 111, 103, 62, 0),
    int[8](12, 14, 12, 12, 12, 12, 63, 0),
    int[8](30, 51, 48, 28, 6, 51, 63, 0),
    int[8](30, 51, 48, 28, 48, 51, 30, 0),
    int[8](56, 60, 54, 51, 127, 48, 120, 0),
    int[8](63, 3, 31, 48, 48, 51, 30, 0),
    int[8](28, 6, 3, 31, 51, 51, 30, 0),
    int[8](63, 51, 48, 24, 12, 12, 12, 0),
    int[8](30, 51, 51, 30, 51, 51, 30, 0),
    int[8](30, 51, 51, 62, 48, 24, 14, 0)
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

float glyphUpperInk(vec2 uv, int letterIndex) {
    vec2 p = clamp(uv, 0.0, 0.999);
    int col = int(floor(p.x * 8.0));
    int row = int(floor((1.0 - p.y) * 8.0));
    int bits = FONT_UPPER[clamp(letterIndex, 0, 25)][row];
    return float((bits >> col) & 1);
}

float glyphDigitInk(vec2 uv, int digit) {
    vec2 p = clamp(uv, 0.0, 0.999);
    int col = int(floor(p.x * 8.0));
    int row = int(floor((1.0 - p.y) * 8.0));
    int bits = FONT_DIGITS[clamp(digit, 0, 9)][row];
    return float((bits >> col) & 1);
}

float glyphDotInk(vec2 uv) {
    vec2 p = clamp(uv, 0.0, 1.0);
    float dx = abs(p.x - 0.5);
    float dy = abs(p.y - 0.82);
    return 1.0 - smoothstep(0.14, 0.20, max(dx, dy));
}

float drawOverlayGlyph(vec2 topCoord, vec2 origin, int slot, int kind, int index, float scale) {
    float advance = 9.0 * scale;
    vec2 size = vec2(8.0 * scale);
    vec2 p = topCoord - (origin + vec2(float(slot) * advance, 0.0));
    if (p.x < 0.0 || p.y < 0.0 || p.x >= size.x || p.y >= size.y) {
        return 0.0;
    }
    vec2 uv = p / size;
    if (kind == 0) return glyphUpperInk(uv, index);
    if (kind == 1) return glyphDigitInk(uv, index);
    return glyphDotInk(uv);
}

vec3 drawFpsOverlay(vec3 color, vec2 fragCoord) {
    if (uShowFps == 0) {
        return color;
    }

    vec2 topCoord = vec2(fragCoord.x, iResolution.y - fragCoord.y);
    vec2 origin = vec2(20.0, 18.0);
    float scale = 2.0;
    float boxW = 172.0;
    float boxH = 28.0;

    if (topCoord.x >= origin.x - 8.0 && topCoord.x <= origin.x + boxW
            && topCoord.y >= origin.y - 8.0 && topCoord.y <= origin.y + boxH) {
        color = mix(color, vec3(0.0), 0.78);
    }

    float fpsClamped = clamp(uFpsValue, 0.0, 999.9);
    int fpsInt = int(floor(fpsClamped));
    int d2 = fpsInt / 100;
    int d1 = (fpsInt / 10) % 10;
    int d0 = fpsInt % 10;
    int dT = int(clamp(floor(fract(fpsClamped) * 10.0), 0.0, 9.0));

    float ink = 0.0;
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 0, 0, 5, scale));   // F
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 1, 0, 15, scale));  // P
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 2, 0, 18, scale));  // S
    if (d2 > 0) {
        ink = max(ink, drawOverlayGlyph(topCoord, origin, 4, 1, d2, scale));
    }
    if (d2 > 0 || d1 > 0) {
        ink = max(ink, drawOverlayGlyph(topCoord, origin, 5, 1, d1, scale));
    }
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 6, 1, d0, scale));
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 7, 2, 0, scale));
    ink = max(ink, drawOverlayGlyph(topCoord, origin, 8, 1, dT, scale));

    if (ink > 0.0) {
        color = mix(color, vec3(1.0), clamp(ink, 0.0, 1.0));
    }
    return color;
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
    float shadowBoost = 1.0 - smoothstep(0.08, 0.58, luma);
    float boosted = clamp(luma + shadowBoost * 0.18, 0.0, 1.0);
    boosted = clamp(pow(boosted, 0.83), 0.0, 1.0);
    vec3 camLifted = clamp(camColor + vec3(0.10 * shadowBoost), 0.0, 1.0);

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
        tint = camLifted;
    } else if (uColorMode == 1) {
        tint = vec3(boosted);
    } else if (uColorMode == 2) {
        tint = vec3(1.0 - boosted);
    } else {
        tint = 1.0 - camLifted.bgr;
        tint = pow(tint, vec3(0.86)) * vec3(1.18, 1.08, 1.25);
    }

    float scan = 0.93 + 0.07 * sin(fragCoord.y * PI);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.25);
    float noise = (hash12(cellId + floor(iTime * 18.0)) - 0.5) * 0.040;

    float bgLevel = invertMode ? (0.12 + (1.0 - tone) * 0.16) : (0.05 + tone * 0.05);
    vec3 color = vec3(bgLevel) * tint;
    color += tint * glyph * (0.45 + tone * 1.25);
    color += noise * (0.15 + glyph * 0.85);
    color *= scan * mix(0.40, 1.0, vignette);
    return clamp(color, 0.0, 1.0);
}

// ── Pixel Art ──────────────────────────────────────────────────────────────
//
//  uColorMode:
//    0  Full Color   — camera pixelated, colors corrected (BGR→RGB)
//    1  Game Boy     — DMG-01 four-shade green palette + LCD pixel gap
//    2  CGA          — Mode 4 Palette 1 hi: black / cyan / magenta / white
//    3  Phosphor     — P1 green terminal with subtle bloom
//    4  Amber        — P3 amber monitor with warm glow
//    5  Infrared     — FLIR jet colormap, white-hot
//
//  uPixelSize: block edge in screen pixels (4 – 48)

vec3 renderPixelArt(vec2 uv, vec2 fragCoord) {
    float ps = max(uPixelSize, 2.0);

    // Snap to pixel-block centre and sample once
    vec2 blockId     = floor(fragCoord / ps);
    vec2 blockCenter = (blockId + 0.5) * ps;
    vec2 puv         = safeUV(blockCenter / iResolution.xy);
    vec2 inBlock     = fract(fragCoord / ps);   // 0..1 inside the block

    vec3 raw  = texture(iChannel0, puv).bgr;    // camera is BGR — swap once
    float luma = liftShadowLuma(getLuma(raw));

    vec3 col;

    if (uColorMode == 0) {
        // ── Full Color ──────────────────────────────────────────────────────
        col = raw;

    } else if (uColorMode == 1) {
        // ── Game Boy DMG-01 ─────────────────────────────────────────────────
        int lvl = clamp(int(floor(luma * 4.0)), 0, 3);
        if      (lvl == 0) col = vec3(0.059, 0.220, 0.059);  // darkest
        else if (lvl == 1) col = vec3(0.188, 0.384, 0.188);
        else if (lvl == 2) col = vec3(0.545, 0.675, 0.059);
        else               col = vec3(0.608, 0.737, 0.059);  // lightest

        // LCD pixel gap — adaptive to block size
        float gapW = clamp(1.5 / ps, 0.04, 0.18);
        float bx = smoothstep(0.0, gapW, inBlock.x) * (1.0 - smoothstep(1.0 - gapW, 1.0, inBlock.x));
        float by = smoothstep(0.0, gapW, inBlock.y) * (1.0 - smoothstep(1.0 - gapW, 1.0, inBlock.y));
        col = mix(vec3(0.031, 0.110, 0.031), col, bx * by);

    } else if (uColorMode == 2) {
        // ── CGA Mode 4 Palette 1 Hi ─────────────────────────────────────────
        //    black / cyan / magenta / white
        int lvl = clamp(int(floor(luma * 4.0)), 0, 3);
        if      (lvl == 0) col = vec3(0.0);
        else if (lvl == 1) col = vec3(0.333, 1.0,   1.0  );  // #55FFFF
        else if (lvl == 2) col = vec3(1.0,   0.333, 1.0  );  // #FF55FF
        else               col = vec3(1.0);

    } else if (uColorMode == 3) {
        // ── Phosphor P1 green ───────────────────────────────────────────────
        float g = pow(luma, 0.85) * 0.92;
        col  = vec3(0.0, g, g * 0.06);                // slight warm tinge
        col += vec3(0.0, luma * luma * 0.10, 0.0);   // soft bloom
        // subtle vignette for CRT feel
        float vig = pow(clamp(16.0 * puv.x * puv.y * (1.0-puv.x) * (1.0-puv.y), 0.0, 1.0), 0.30);
        col *= mix(0.55, 1.0, vig);

    } else if (uColorMode == 4) {
        // ── Amber P3 monitor ────────────────────────────────────────────────
        float a = pow(luma, 0.88) * 0.96;
        col  = vec3(a * 1.10, a * 0.54, 0.0);
        col += vec3(a * a * 0.09, a * a * 0.04, 0.0); // warm bloom
        float vig = pow(clamp(16.0 * puv.x * puv.y * (1.0-puv.x) * (1.0-puv.y), 0.0, 1.0), 0.30);
        col *= mix(0.55, 1.0, vig);

    } else {
        // ── Infrared / FLIR jet ─────────────────────────────────────────────
        //    cold (blue) → cyan → green → yellow → orange → red → white-hot
        float t = luma;
        float r = clamp(1.5 - abs(4.0 * t - 3.0), 0.0, 1.0);
        float g = clamp(1.5 - abs(4.0 * t - 2.0), 0.0, 1.0);
        float b = clamp(1.5 - abs(4.0 * t - 1.0), 0.0, 1.0);
        col = vec3(r, g, b);
        col = mix(col, vec3(1.0), smoothstep(0.88, 1.0, luma)); // white-hot
    }

    return clamp(col, 0.0, 1.0);
}

// ── Signal Ghost ────────────────────────────────────────────────────────────
//
//  A living field of letters that breathes and flows with your presence.
//  Motion detection (CPU-side) drives two uniforms:
//    uPresenceScale  — overall brightness: 0 = nobody, 1 = very close
//    uMotionLevel    — frame-diff magnitude: 0 = still, 1 = strong motion
//    uPresenceCX/CY  — weighted centroid of bright regions (0..1)
//
//  uColorMode:
//    0  Void          — white glyphs on black, minimal
//    1  Matrix        — classic green terminal rain
//    2  Ghost Cam     — letters tinted by camera color, dim camera bg
//    3  Neon          — position-driven hue rotation, glowing
//    4  Thermal       — FLIR jet coloring per local luminance
//    5  Chromatic     — RGB channels split by motion intensity
//
//  uAsciiDensity: field density (0.5 → 5.0), left/right arrow

vec3 renderSignalGhost(vec2 uv, vec2 fragCoord) {
    float presence = clamp(uPresenceScale * 2.2, 0.0, 1.0);
    float motion   = clamp(uMotionLevel, 0.0, 1.0);
    vec2  presPos  = vec2(uPresenceCX, uPresenceCY);

    // Flow field: smooth UV warp that stirs with motion and presence
    vec2 flow = vec2(
        sin(iTime * 0.22 + uv.y * 5.1 + uPresenceCY * 3.14) * 0.018,
        cos(iTime * 0.17 + uv.x * 4.3 + uPresenceCX * 3.14) * 0.014
    ) * (0.4 + motion * 2.5 + presence * 0.6);

    // Radial pull toward presence centroid — letters lean in when you approach
    vec2 toPresence = presPos - uv;
    flow += normalize(toPresence + vec2(0.001)) * motion * 0.022;

    vec2 wUV = uv + flow;

    // Grid
    float cols = 8.0 + uAsciiDensity * 7.0;          // 11 – 43 columns
    float rows = floor(cols * iResolution.y / iResolution.x * 0.65);
    vec2  cellCount = vec2(cols, max(rows, 8.0));
    vec2  gridUV    = wUV * cellCount;
    vec2  cellId    = floor(gridUV);
    vec2  cellUV    = fract(gridUV);                  // 0..1 within cell

    // Per-cell personality
    float ch  = hash12(cellId);
    float ch2 = hash12(cellId * 2.3 + 1.7);

    // Sample camera at this cell's position for color and local energy
    vec2 sampleUV = safeUV((cellId + 0.5) / cellCount);
    vec3 camCol   = texture(iChannel0, sampleUV).bgr;  // BGR→RGB
    float cellLuma = liftShadowLuma(getLuma(camCol));

    // Letter: changes faster during motion, each cell staggered by ch
    float changeRate = 0.06 + motion * 5.0 + presence * 0.8;
    float slot       = floor(iTime * changeRate + ch * 8.0);
    int   letter     = clamp(int(floor(hash12(cellId + vec2(slot * 0.09, slot * 0.13)) * 26.0)), 0, 25);

    // Scale: breathes slowly; expands when someone is present or moving
    float breathe = 0.5 + 0.5 * sin(iTime * (0.35 + ch * 0.9) + ch * 6.28);
    float scale   = clamp(
        0.12 + breathe * 0.14 + presence * 0.55 + cellLuma * 0.35 + motion * ch * 0.22,
        0.06, 1.05
    );

    // Wobble offset within cell driven by motion
    vec2 wobble = vec2(ch - 0.5, ch2 - 0.5) * motion * 0.18;
    vec2 letterUV = (cellUV - 0.5 - wobble) / scale + 0.5;

    float ink = 0.0;
    if (letterUV.x >= 0.0 && letterUV.x < 1.0 && letterUV.y >= 0.0 && letterUV.y < 1.0) {
        ink = glyphUpperInk(clamp(letterUV, 0.0, 0.999), letter);
    }

    float glow = smoothstep(0.0, 0.45, ink) * (0.25 + cellLuma * 0.35 + presence * 0.40);

    vec3 col;

    if (uColorMode == 0) {
        // ── Void: white on black ────────────────────────────────────────────
        float v = ink * (0.55 + presence * 0.45) + glow * 0.18;
        col = vec3(v);

    } else if (uColorMode == 1) {
        // ── Matrix: green terminal ───────────────────────────────────────────
        float g = ink * (0.45 + cellLuma * 0.35 + presence * 0.20);
        col = vec3(g * 0.15, g, g * 0.08);
        col += vec3(0.0, glow * 0.12, 0.0);

    } else if (uColorMode == 2) {
        // ── Ghost Cam: letters tinted by camera, dim ghost bg ────────────────
        col  = camCol * ink * (0.55 + presence * 0.45);
        col += camCol * 0.06;                          // very dim camera ghost

    } else if (uColorMode == 3) {
        // ── Neon: position-driven hue, glowing ──────────────────────────────
        float hue = fract(uv.x * 0.4 + uv.y * 0.25 + iTime * 0.04 + motion * 0.25);
        vec3  c   = clamp(abs(mod(hue * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
        col = c * ink * (0.75 + presence * 0.25);
        col += c * glow * 0.35;

    } else if (uColorMode == 4) {
        // ── Thermal: FLIR jet per cell luminance ─────────────────────────────
        float t = cellLuma;
        float r = clamp(1.5 - abs(4.0 * t - 3.0), 0.0, 1.0);
        float g = clamp(1.5 - abs(4.0 * t - 2.0), 0.0, 1.0);
        float b = clamp(1.5 - abs(4.0 * t - 1.0), 0.0, 1.0);
        vec3  tc = mix(vec3(r, g, b), vec3(1.0), smoothstep(0.88, 1.0, cellLuma));
        col  = tc * ink * (0.7 + presence * 0.3);
        col += tc * glow * 0.20;

    } else {
        // ── Chromatic: RGB channels offset by motion ─────────────────────────
        float shift = motion * 0.010;
        float rL = liftShadowLuma(getLuma(texture(iChannel0, safeUV(sampleUV + vec2( shift, 0.0))).bgr));
        float bL = liftShadowLuma(getLuma(texture(iChannel0, safeUV(sampleUV + vec2(-shift, 0.0))).bgr));
        col  = vec3(ink * rL, ink * cellLuma, ink * bL) * (0.8 + presence * 0.5 + motion * 0.3);
        col += glow * vec3(0.08, 0.0, 0.18);
    }

    return clamp(col, 0.0, 1.0);
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
    } else if (uEffectMode == 1) {
        color = renderAscii(uv, fragCoord);
    } else if (uEffectMode == 2) {
        color = renderPixelArt(uv, fragCoord);
    } else {
        color = renderSignalGhost(uv, fragCoord);
    }
    fragColor = vec4(color, 1.0);
}
