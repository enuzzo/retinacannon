uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uRuttWave;
uniform float uAsciiDensity;
uniform int uEffectMode;
uniform int uViewMode;
uniform int uMirror;
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

vec2 cameraMirrorUV(vec2 uv) {
    if (uMirror != 0) {
        uv.x = 1.0 - uv.x;
    }
    return uv;
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
    vec2 sampleBase = cameraMirrorUV(uv);
    if (uColorMode == 2) {
        sampleBase += vec2(
            sin((sampleBase.y + iTime * 0.20) * 16.0),
            cos((sampleBase.x - iTime * 0.16) * 13.0)
        ) * 0.006;
    } else if (uColorMode == 3) {
        vec2 p = sampleBase - 0.5;
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

    float waveScale = 1.0;
    if (uColorMode == 3) waveScale = 6.0;
    else if (uColorMode == 4) waveScale = 10.0;
    else if (uColorMode == 5) waveScale = 14.0;
    float lineY = normI + luma * (EXTRUSION * uRuttWave * waveScale);
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
    } else if (uColorMode == 3) {
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
    } else if (uColorMode == 4) {
        // Mega Wave: Colors mode + horizontal blur + waveScale 10.0
        vec3 colorUp = liftShadows(texture(iChannel0, safeUV(sampleUV + vec2(0.0, 1.0 / LINES))).rgb);
        lineCol = mix(camColor, colorUp, 0.25) * 1.92;
    } else {
        // Prism Surge: Prism Warp + waveScale 14.0 + wider channel split
        float shift = 0.0055;
        float r = liftShadows(texture(iChannel0, safeUV(sampleUV + vec2(shift, 0.0))).rgb).r;
        float g = camColor.g;
        float b = liftShadows(texture(iChannel0, safeUV(sampleUV - vec2(shift, 0.0))).rgb).b;
        lineCol = vec3(r, g, b) * vec3(1.75, 1.20, 1.80);
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
    // Dense modes (2+3) run at 2× density and mix letters+symbols
    bool denseMode = (uColorMode >= 2);
    float density = denseMode
        ? clamp(uAsciiDensity * 2.0, 2.0, 12.0)
        : clamp(uAsciiDensity, 1.00, 6.00);
    vec2 grid = vec2(94.0 * density, floor(94.0 * density * iResolution.y / iResolution.x / charAspect));
    grid.y = max(grid.y, 18.0);

    vec2 cell = uv * grid;
    vec2 cellId = floor(cell);
    vec2 cellUV = fract(cell);
    vec2 sampleUV = safeUV((cellId + 0.5) / grid);
    sampleUV = cameraMirrorUV(sampleUV);

    vec3 camColor = liftShadows(texture(iChannel0, sampleUV).rgb);
    float luma = getLuma(camColor);
    float shadowBoost = 1.0 - smoothstep(0.08, 0.58, luma);
    float boosted = clamp(luma + shadowBoost * 0.18, 0.0, 1.0);
    boosted = clamp(pow(boosted, 0.83), 0.0, 1.0);
    vec3 camLifted = clamp(camColor + vec3(0.10 * shadowBoost), 0.0, 1.0);

    // Dense modes: not inverted. Modes 0/1: symbols only. Dense: 70% letters + 30% symbols.
    float tone = boosted;

    float glyph;
    if (denseMode) {
        // Per-cell random to decide letter vs symbol (70/30 split)
        float mixRoll = hash12(cellId * vec2(2.31, 1.79) + 3.7);
        if (mixRoll > 0.30) {
            float jitter = (hash12(cellId * vec2(0.71, 1.17)) - 0.5) * 0.22;
            float idxF = clamp(tone + jitter, 0.0, 1.0);
            int letterIndex = clamp(int(floor(idxF * 52.0)), 0, 51);
            glyph = glyphLetterInk(cellUV, letterIndex);
        } else {
            int level = int(clamp(floor(tone * 8.0), 0.0, 7.0));
            vec2 p = cellUV - 0.5;
            p.y *= charAspect;
            glyph = glyphSymbolInk(p, level);
        }
    } else {
        int level = int(clamp(floor(tone * 8.0), 0.0, 7.0));
        vec2 p = cellUV - 0.5;
        p.y *= charAspect;
        glyph = glyphSymbolInk(p, level);
    }

    vec3 tint;
    if (uColorMode == 0) {
        tint = camLifted;          // Color symbols
    } else if (uColorMode == 1) {
        tint = vec3(boosted);      // Monochrome symbols
    } else if (uColorMode == 2) {
        tint = vec3(boosted);      // Dense Mono Mix — monochrome, not inverted
    } else {
        tint = camLifted;          // Dense Color Mix — color, not inverted
    }

    float scan = 0.93 + 0.07 * sin(fragCoord.y * PI);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.25);
    float noise = (hash12(cellId + floor(iTime * 18.0)) - 0.5) * 0.040;

    float bgLevel = 0.05 + tone * 0.05;
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
//    2  Toxic Candy  — neon candy palette with rounded pixel corners
//
//  uPixelSize: block edge in screen pixels (4 – 48)

float bayer4(vec2 p) {
    vec2 m = mod(floor(p), 4.0);
    float x = m.x;
    float y = m.y;
    float v;
    if (y < 1.0) {
        if      (x < 1.0) v = 0.0;
        else if (x < 2.0) v = 8.0;
        else if (x < 3.0) v = 2.0;
        else              v = 10.0;
    } else if (y < 2.0) {
        if      (x < 1.0) v = 12.0;
        else if (x < 2.0) v = 4.0;
        else if (x < 3.0) v = 14.0;
        else              v = 6.0;
    } else if (y < 3.0) {
        if      (x < 1.0) v = 3.0;
        else if (x < 2.0) v = 11.0;
        else if (x < 3.0) v = 1.0;
        else              v = 9.0;
    } else {
        if      (x < 1.0) v = 15.0;
        else if (x < 2.0) v = 7.0;
        else if (x < 3.0) v = 13.0;
        else              v = 5.0;
    }
    return (v + 0.5) / 16.0;
}

vec3 renderPixelArt(vec2 uv, vec2 fragCoord) {
    float ps = max(uPixelSize, 2.0);

    // Snap to pixel-block centre and sample once
    vec2 blockId     = floor(fragCoord / ps);
    vec2 blockCenter = (blockId + 0.5) * ps;
    vec2 puv         = safeUV(blockCenter / iResolution.xy);
    puv = cameraMirrorUV(puv);
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

    } else {
        // ── Toxic Candy (mode 2) ────────────────────────────────────────────
        float sat = length(raw - vec3(getLuma(raw)));
        float t = clamp(pow(luma, 0.88) + (bayer4(blockId + 1.0) - 0.5) * 0.26, 0.0, 1.0);
        int lvl = clamp(int(floor(t * 5.0)), 0, 4);
        if      (lvl == 0) col = vec3(0.070, 0.070, 0.090);  // near-black
        else if (lvl == 1) col = vec3(0.224, 1.000, 0.078);  // toxic green
        else if (lvl == 2) col = vec3(0.000, 0.898, 1.000);  // electric cyan
        else if (lvl == 3) col = vec3(1.000, 0.310, 0.847);  // candy magenta
        else               col = vec3(1.000, 0.953, 0.690);  // pale glow

        // Push neon accents where source saturation is high.
        col = mix(col, col * vec3(1.05, 1.10, 1.05), smoothstep(0.18, 0.58, sat));

        // Rounded pixel corners using SDF — radius adapts to block size
        float r = clamp(4.0 / ps, 0.06, 0.32);
        vec2 q = abs(inBlock - 0.5) - vec2(0.5 - r);
        float sdf = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
        float pixelMask = 1.0 - smoothstep(-1.5 / ps, 1.5 / ps, sdf);
        col = mix(vec3(0.02, 0.02, 0.03), col, pixelMask);
    }

    return clamp(col, 0.0, 1.0);
}

vec3 thermalJet(float t) {
    float r = clamp(1.5 - abs(4.0 * t - 3.0), 0.0, 1.0);
    float g = clamp(1.5 - abs(4.0 * t - 2.0), 0.0, 1.0);
    float b = clamp(1.5 - abs(4.0 * t - 1.0), 0.0, 1.0);
    vec3 jet = vec3(r, g, b);
    return mix(jet, vec3(1.0), smoothstep(0.90, 1.0, t));
}

float edgeLuma4(vec2 uv, float stepUV) {
    vec2 dx = vec2(stepUV, 0.0);
    vec2 dy = vec2(0.0, stepUV);
    float lR = liftShadowLuma(getLuma(texture(iChannel0, safeUV(uv + dx)).bgr));
    float lL = liftShadowLuma(getLuma(texture(iChannel0, safeUV(uv - dx)).bgr));
    float lU = liftShadowLuma(getLuma(texture(iChannel0, safeUV(uv + dy)).bgr));
    float lD = liftShadowLuma(getLuma(texture(iChannel0, safeUV(uv - dy)).bgr));
    return clamp(length(vec2(lR - lL, lU - lD)) * 2.4, 0.0, 1.0);
}

// ── Raster Vision ──────────────────────────────────────────────────────────
//
//  uColorMode:
//    0  Thermal Raster   — blue cold / red hot
//    1  Thermal Inverted — red cold / blue hot
//    2  Comic B/W        — halftone ink with edge lines
//    3  Comic Pastel     — soft quantized halftone
//    4  Vibrant Pop      — saturated comic print
//
//  uPixelSize controls dot-cell size (left/right arrows in mode 4)
//  Larger value => fewer, larger dots. Smaller => denser raster.
vec3 renderRasterVision(vec2 uv, vec2 fragCoord) {
    float ps = max(uPixelSize, 2.0);

    vec2 blockId     = floor(fragCoord / ps);
    vec2 blockCenter = (blockId + 0.5) * ps;
    vec2 puv         = safeUV(blockCenter / iResolution.xy);
    puv = cameraMirrorUV(puv);
    vec2 dotUV       = fract(fragCoord / ps) - 0.5;

    vec3 raw  = texture(iChannel0, puv).bgr;
    float luma = liftShadowLuma(getLuma(raw));

    float seed = hash12(blockId * vec2(0.73, 1.31) + 9.17);
    float var = (seed - 0.5) * 0.16;
    vec2 jitter = (vec2(
        hash12(blockId + vec2(17.0, 11.0)),
        hash12(blockId + vec2(5.0, 23.0))
    ) - 0.5) * 0.20;
    vec2 dotP = dotUV + jitter;
    float edgeStep = max(ps / min(iResolution.x, iResolution.y), 0.0015);
    float edge = edgeLuma4(puv, edgeStep);

    vec3 col;
    if (uColorMode == 0 || uColorMode == 1) {
        float t = (uColorMode == 1) ? (1.0 - luma) : luma;
        vec3 heat = thermalJet(t);
        float radius = clamp(0.09 + pow(t, 0.78) * 0.36 + var, 0.05, 0.48);
        float dot = 1.0 - smoothstep(radius, radius + (0.055 + 1.2 / ps), length(dotP));
        vec3 bg = mix(vec3(0.010, 0.015, 0.020), heat * 0.32, 0.22);
        col = mix(bg, heat, dot);
        col = mix(col, vec3(0.0), smoothstep(0.34, 0.62, edge) * 0.10);
    } else if (uColorMode == 2) {
        float ink = clamp(1.0 - luma, 0.0, 1.0);
        float radius = clamp(0.07 + ink * 0.39 + var * 0.60, 0.05, 0.47);
        float dot = 1.0 - smoothstep(radius, radius + (0.050 + 0.9 / ps), length(dotP));
        vec3 paper = vec3(0.95, 0.94, 0.90);
        vec3 line = vec3(0.07);
        col = mix(paper, line, dot * (0.58 + ink * 0.42));
        col = mix(col, line, smoothstep(0.16, 0.34, edge));
    } else if (uColorMode == 3) {
        vec3 pastel = clamp(raw * 0.58 + vec3(0.36), 0.0, 1.0);
        pastel = floor(pastel * 5.0) / 4.0;
        float ink = clamp(1.0 - luma * 0.90, 0.0, 1.0);
        float radius = clamp(0.07 + ink * 0.35 + var * 0.50, 0.05, 0.46);
        float dot = 1.0 - smoothstep(radius, radius + (0.050 + 0.9 / ps), length(dotP));
        vec3 paper = vec3(0.98, 0.95, 0.90);
        col = mix(paper, pastel, dot * 0.88 + 0.08);
        col = mix(col, pastel * 0.55, smoothstep(0.20, 0.40, edge));
    } else {
        // Vibrant Pop: saturation boost (not brightness) to avoid channel clipping / blue skin
        vec3 gray = vec3(getLuma(raw));
        vec3 pop = clamp(gray + (raw - gray) * 2.0, 0.0, 1.0);
        pop = clamp(pow(pop, vec3(0.88)) * 1.10, 0.0, 1.0);
        pop = floor(pop * 6.0) / 5.0;
        float tone = clamp(luma, 0.0, 1.0);
        float radius = clamp(0.08 + tone * 0.36 + var * 0.50, 0.05, 0.47);
        float dot = 1.0 - smoothstep(radius, radius + (0.050 + 0.9 / ps), length(dotP));
        vec3 bg = mix(vec3(0.03, 0.03, 0.04), pop * 0.35, 0.35);
        col = mix(bg, pop, dot);
        col = mix(col, vec3(0.02), smoothstep(0.22, 0.42, edge) * 0.62);
    }

    return clamp(col, 0.0, 1.0);
}

vec4 hash44(vec4 p4) {
    p4 = fract(p4 * 0.3183099 + vec4(0.71, 0.113, 0.419, 0.279));
    vec4 q = p4 * (p4.wzxy + 19.19);
    p4 += fract(q.xwzy * q.zywx + q.yzzw);
    p4 = abs(fract(p4 * 1.61803) * 2.0 - 1.0);
    p4 += dot(p4, vec4(0.754877, 0.569840, 0.437016, 0.982451));
    p4 = fract(p4 * 0.618034 + p4.wxyz * 0.414214);
    p4 = fract(p4.xwzy * (p4.zywx + 0.61803) + p4.yzzw);
    return fract(123.45 * p4);
}

// ── Digital Codec Corruption ─────────────────────────────────────────────────
// uAsciiDensity: block corruption intensity (0.5..6.0)
// uColorMode: 0=RGB Mosh  1=Thermal Glitch  2=Acid Trip  3=Void Codec
vec3 renderDatamoshTrails(vec2 uv, vec2 fragCoord) {
    vec2 cuv = safeUV(cameraMirrorUV(uv));
    float amount = clamp(uAsciiDensity, 0.5, 6.0);

    // Macroblocks: grow larger with intensity (JPEG/H.264 artifact)
    float blockSize = mix(8.0, 32.0, amount / 6.0);
    vec2 blockUV = vec2(blockSize) / iResolution.xy;
    vec2 blockId = floor(cuv / blockUV);

    // Per-block corruption decision — animated at low frame rate
    float blockHash = hash12(blockId + floor(iTime * 0.7) * vec2(1.3, 0.7));
    float corruptThresh = mix(0.75, 0.28, amount / 6.0);
    bool corrupted = blockHash > corruptThresh;

    vec2 sampledUV = cuv;
    if (corrupted) {
        // Jump to wrong macroblock (codec keyframe error)
        vec2 blockOffset = vec2(
            floor(hash12(blockId * 2.1 + 0.3) * 9.0 - 4.5),
            floor(hash12(blockId * 1.7 + 0.7) * 7.0 - 3.5)
        ) * blockUV;
        sampledUV = safeUV(cuv + blockOffset);
    }

    vec3 base = texture(iChannel0, sampledUV).rgb;

    // Horizontal DC-smear artifact on corrupted blocks
    float smear = corrupted ? amount * 0.006 : 0.0;
    vec3 smearL = texture(iChannel0, safeUV(sampledUV - vec2(smear * 2.5, 0.0))).rgb;
    vec3 smearR = texture(iChannel0, safeUV(sampledUV + vec2(smear, 0.0))).rgb;

    // Aggressive baseline glitch on ALL blocks — no clean camera visible
    vec2 baseJitter = vec2(hash12(blockId * 0.71 + floor(iTime * 0.3)) - 0.5, 0.0) * 0.025 * amount;
    // Add vertical component for more chaos on non-corrupted blocks
    baseJitter.y = (hash12(blockId * 1.13 + floor(iTime * 0.5)) - 0.5) * 0.008 * amount;
    vec3 mild = texture(iChannel0, safeUV(sampledUV + baseJitter)).rgb;
    mild += (hash12(fragCoord * 0.5 + iTime * 25.0) - 0.5) * 0.09;
    mild *= vec3(1.06, 0.94, 1.05);

    vec3 col = corrupted
        ? mix(base, mix(smearL, smearR, 0.45), 0.80)   // extreme smear
        : mild;                                          // aggressive baseline (no clean base)

    if (uColorMode == 0) {
        // RGB Mosh: R, G, B sampled from different displaced positions → chromatic smear
        if (corrupted) {
            float spread = blockSize * 0.6 / iResolution.x * amount;
            float rR = texture(iChannel0, safeUV(sampledUV + vec2(spread * 1.2, 0.0))).r;
            float gG = texture(iChannel0, sampledUV).g;
            float bB = texture(iChannel0, safeUV(sampledUV - vec2(spread * 1.8, 0.0))).b;
            col = vec3(rR, gG, bB);
        }
    } else if (uColorMode == 1) {
        // Thermal Glitch: heat map on corrupted blocks, cool blue on clean blocks
        float luma = getLuma(col);
        vec3 heat;
        if (luma < 0.25)      heat = mix(vec3(0.0), vec3(0.5, 0.0, 0.1), luma * 4.0);
        else if (luma < 0.5)  heat = mix(vec3(0.5, 0.0, 0.1), vec3(1.0, 0.4, 0.0), (luma - 0.25) * 4.0);
        else if (luma < 0.75) heat = mix(vec3(1.0, 0.4, 0.0), vec3(1.0, 1.0, 0.0), (luma - 0.5) * 4.0);
        else                  heat = mix(vec3(1.0, 1.0, 0.0), vec3(1.0), (luma - 0.75) * 4.0);
        col = corrupted ? heat : mix(vec3(luma * 0.1, luma * 0.3, luma * 0.5), vec3(luma * 0.15), 0.3);
    } else if (uColorMode == 2) {
        // Acid Trip: hue channel rotation on corrupted blocks → neon blast
        if (corrupted) {
            col = clamp(col.gbr * vec3(1.5, 1.2, 1.8), 0.0, 1.0);
        } else {
            col = clamp(col * vec3(0.75, 1.05, 0.85), 0.0, 1.0);
        }
    } else {
        // Void Codec: corrupted blocks → black void, only edge pixels survive
        vec2 px = vec2(1.0) / iResolution.xy;
        float lR = getLuma(texture(iChannel0, safeUV(sampledUV + vec2(px.x, 0.0))).rgb);
        float lL = getLuma(texture(iChannel0, safeUV(sampledUV - vec2(px.x, 0.0))).rgb);
        float lU = getLuma(texture(iChannel0, safeUV(sampledUV + vec2(0.0, px.y))).rgb);
        float lD = getLuma(texture(iChannel0, safeUV(sampledUV - vec2(0.0, px.y))).rgb);
        float edge = clamp(length(vec2(lR - lL, lU - lD)) * 7.0, 0.0, 1.0);
        col = corrupted ? vec3(edge * 0.9) : col * 0.42;
    }

    return clamp(col, 0.0, 1.0);
}

// ── VHS Tracking Burn ───────────────────────────────────────────────────────
// uAsciiDensity: tracking intensity (0.5..5.0)
// uColorMode: 0=Signal Melt  1=Night Tape
vec3 renderVhsTrackingBurn(vec2 uv, vec2 fragCoord) {
    vec2 cuv = safeUV(cameraMirrorUV(uv));
    float tracking = clamp(uAsciiDensity, 0.5, 5.0);

    // Y/C separation: luma at cuv, chroma sampled with horizontal delay
    float chromaDelay = 0.004 * tracking;
    vec2 chromaUV = safeUV(cuv + vec2(chromaDelay, 0.0));

    // Chroma bleed: weighted average of 5 horizontal chroma samples
    float spread = 0.018 * tracking;
    vec3 chroma = vec3(0.0);
    chroma += texture(iChannel0, safeUV(chromaUV - vec2(spread * 2.0, 0.0))).rgb * 0.15;
    chroma += texture(iChannel0, safeUV(chromaUV - vec2(spread,       0.0))).rgb * 0.20;
    chroma += texture(iChannel0, chromaUV).rgb                                   * 0.30;
    chroma += texture(iChannel0, safeUV(chromaUV + vec2(spread,       0.0))).rgb * 0.20;
    chroma += texture(iChannel0, safeUV(chromaUV + vec2(spread * 2.0, 0.0))).rgb * 0.15;

    // Reconstruct: luma from original UV, chroma from bleed channel
    float lumaVal = getLuma(texture(iChannel0, cuv).rgb);
    vec3 col = vec3(lumaVal) * 0.55 + chroma * 0.55;

    // Scanline jitter: per-scanline horizontal wobble (amplified)
    float jitter = (hash12(vec2(floor(fragCoord.y), floor(iTime * 20.0))) - 0.5) * 0.010 * tracking;
    vec3 jittered = texture(iChannel0, safeUV(cuv + vec2(jitter, 0.0))).rgb;
    col = mix(col, jittered, 0.30);

    // Head-switching artifact: large displacement in bottom 12% of frame
    float headSwitch = 1.0 - smoothstep(0.10, 0.13, uv.y);
    if (headSwitch > 0.0) {
        float hsJitter = (hash12(vec2(floor(fragCoord.y * 0.25), iTime * 8.0)) - 0.5) * 0.12 * tracking;
        vec3 hsColor = texture(iChannel0, safeUV(cuv + vec2(hsJitter, 0.0))).rgb;
        col = mix(col, hsColor * 0.50, headSwitch);
    }

    // Luma noise (amplified)
    col += (hash12(fragCoord + iTime * 220.0) - 0.5) * 0.075 * tracking;

    // Alternating scanline dimming
    col *= 0.88 + 0.12 * sin(fragCoord.y * 2.0);

    // Color modes
    if (uColorMode == 0) {
        // Signal Melt: massive RGB split — extreme chromatic aberration
        float sp = spread * 3.0;
        col.r = texture(iChannel0, safeUV(cuv + vec2(sp, 0.0))).r;
        col.g = texture(iChannel0, cuv).g;
        col.b = texture(iChannel0, safeUV(cuv - vec2(sp * 1.5, 0.0))).b;
        col = clamp(col * 1.3, 0.0, 1.0);
    } else {
        // Night Tape: green phosphor security camera with heavy interference
        float lum = getLuma(col);
        // Heavy film grain
        float grain = (hash12(fragCoord * 1.3 + iTime * 180.0) - 0.5) * 0.20;
        // Horizontal interference bands — random bursts
        float bandNoise = hash12(vec2(floor(fragCoord.y * 0.12), floor(iTime * 9.0)));
        float band = bandNoise > 0.90 ? (bandNoise - 0.90) * 10.0 : 0.0;
        // Jitter on interference bands
        float hglitch = (hash12(vec2(floor(fragCoord.y * 0.18), floor(iTime * 18.0))) - 0.5) * band * 0.10;
        vec3 jitteredSrc = texture(iChannel0, safeUV(cuv + vec2(hglitch, 0.0))).rgb;
        lum = mix(lum, getLuma(jitteredSrc), band * 0.55);
        // Occasional full-line dropout
        float dropout = hash12(vec2(floor(fragCoord.y * 0.07), floor(iTime * 5.0)));
        lum *= (dropout > 0.96) ? 0.05 : 1.0;
        col = vec3(lum * 0.07, lum * 0.95 + grain, lum * 0.09);
        col += vec3(0.0, band * 0.30, 0.0);  // bright green interference burst
    }

    return clamp(col, 0.0, 1.0);
}

// ── Posterize Glitch Comic ──────────────────────────────────────────────────
// uAsciiDensity: quantization levels (2..12)
// uColorMode: 0=Warhol Pop  1=Neon Cel  2=Acid Bloom  3=Plasma Burn
vec3 renderPosterizeGlitchComic(vec2 uv, vec2 fragCoord) {
    vec2 cuv = safeUV(cameraMirrorUV(uv));
    float levels = floor(clamp(uAsciiDensity, 2.0, 12.0));

    // Glitch bands: random horizontal scanband shift (amplified)
    float bandHash = hash12(vec2(floor(fragCoord.y * 0.08), floor(iTime * 2.0)));
    if (bandHash > 0.72) {
        cuv.x = clamp(cuv.x + (bandHash - 0.72) * levels * 0.14, 0.001, 0.999);
    }

    vec3 base = texture(iChannel0, cuv).rgb;
    vec3 poster = floor(base * levels) / max(levels - 1.0, 1.0);

    // Edge detection for ink lines
    vec2 px = vec2(1.0) / iResolution.xy;
    float lR = getLuma(texture(iChannel0, safeUV(cuv + vec2(px.x, 0.0))).rgb);
    float lL = getLuma(texture(iChannel0, safeUV(cuv - vec2(px.x, 0.0))).rgb);
    float lU = getLuma(texture(iChannel0, safeUV(cuv + vec2(0.0, px.y))).rgb);
    float lD = getLuma(texture(iChannel0, safeUV(cuv - vec2(0.0, px.y))).rgb);
    float edge = clamp(length(vec2(lR - lL, lU - lD)) * 3.5, 0.0, 1.0);
    float ink = smoothstep(0.12, 0.32, edge);

    vec3 col;
    if (uColorMode == 0) {
        // Warhol Pop: bold pop palette mapped per posterize level
        const vec3 WARHOL0 = vec3(1.00, 0.05, 0.12);
        const vec3 WARHOL1 = vec3(1.00, 0.90, 0.00);
        const vec3 WARHOL2 = vec3(0.00, 0.85, 1.00);
        const vec3 WARHOL3 = vec3(0.90, 0.00, 0.90);
        const vec3 WARHOL4 = vec3(0.00, 0.95, 0.35);
        const vec3 WARHOL5 = vec3(1.00, 0.50, 0.00);
        int li = clamp(int(floor(getLuma(poster) * levels)), 0, 5);
        vec3 wc = li == 0 ? WARHOL0 : li == 1 ? WARHOL1 : li == 2 ? WARHOL2 :
                  li == 3 ? WARHOL3 : li == 4 ? WARHOL4 : WARHOL5;
        col = mix(wc, vec3(0.0), ink * 0.88);
    } else if (uColorMode == 1) {
        // Neon Cel: dark bg, neon ink edges in alternating cyan/magenta per level
        float luma = getLuma(poster);
        int level = int(floor(luma * levels));
        vec3 dark = poster * 0.15;
        vec3 neonA = vec3(0.0,  1.0,  0.95); // electric cyan
        vec3 neonB = vec3(1.0,  0.05, 0.85); // neon magenta
        vec3 neonC = vec3(0.95, 1.0,  0.0);  // acid yellow
        int ni = int(mod(float(level), 3.0));
        vec3 neonColor = ni == 0 ? neonA : (ni == 1 ? neonB : neonC);
        col = dark + neonColor * smoothstep(0.28, 0.55, ink) * 1.85;
    } else if (uColorMode == 2) {
        // Acid Bloom: HSV hue per level, saturated + glowing edges
        float levelF = float(clamp(int(floor(getLuma(poster) * levels)), 0, 11));
        float hue = fract(levelF / max(levels, 1.0) + iTime * 0.04);
        vec3 sat = clamp(abs(mod(hue * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
        col = sat * (0.85 - ink * 0.6) + sat * smoothstep(0.2, 0.5, ink) * 1.4;
    } else {
        // Plasma Burn: animated multi-sine plasma tinted per posterize level
        float luma = getLuma(poster);
        // Multi-wave plasma combining spatial and temporal frequencies
        float plasma = sin(uv.x * 9.0 + iTime * 2.5)
                     + sin(uv.y * 7.0 + iTime * 1.9)
                     + sin((uv.x + uv.y) * 5.5 + iTime * 3.1)
                     + sin(length(uv - vec2(0.5)) * 14.0 - iTime * 3.7);
        plasma = plasma * 0.25 + 0.5;  // normalize to 0..1
        // Per-level phase offset + global time drift for hue cycling
        int li = clamp(int(floor(luma * levels)), 0, int(levels) - 1);
        float levelPhase = float(li) / max(levels, 1.0) * 0.6;
        float hue = fract(plasma + levelPhase + iTime * 0.08);
        vec3 plasmaCol = clamp(abs(mod(hue * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
        // Boost saturation and mix with ink edges
        plasmaCol = pow(plasmaCol, vec3(0.7)) * (0.85 + luma * 0.45);
        col = mix(plasmaCol, vec3(0.0), ink * 0.70);
    }

    return clamp(col, 0.0, 1.0);
}

vec3 sampleExpCam(vec2 uv) {    return texture(iChannel0, safeUV(cameraMirrorUV(uv))).rgb;}

vec3 blur5(vec2 uv, vec2 axis, float px) {    vec2 off = axis * px;    vec3 c = sampleExpCam(uv) * 0.50;    c += sampleExpCam(uv + off) * 0.25;    c += sampleExpCam(uv - off) * 0.25;    return c;}

vec3 renderLensDotBevel(vec2 uv, vec2 fragCoord) {    float detail = clamp(uAsciiDensity, 1.0, 5.0);    float dn = (detail - 1.0) / 4.0;    float cell = mix(48.0, 22.0, dn);    float bevelK = (uColorMode == 1) ? 0.32 : ((uColorMode == 2) ? 0.42 : 0.20);    float specP = (uColorMode == 2) ? 72.0 : 54.0;    float specI = (uColorMode == 2) ? 0.55 : 0.40;    float blurPx = mix(2.0, 5.0, dn);    vec3 bg = 0.5 * (blur5(uv, vec2(1.0 / iResolution.x, 0.0), blurPx) + blur5(uv, vec2(0.0, 1.0 / iResolution.y), blurPx));    bg = clamp(bg * exp2(-0.55), 0.0, 0.95);    vec2 cid = floor(fragCoord / vec2(cell));    vec2 ctr = (cid + 0.5) * vec2(cell);    vec2 toC = fragCoord - ctr;    float d = length(toC);    float rad = max(0.1, (cell - 0.1) * 0.5);    float aa = max(fwidth(d), 0.001);    float disc = 1.0 - smoothstep(rad, rad + aa, d);    float bw = rad * bevelK;    float innerR = max(rad - bw, 0.0);    float s = clamp((d - innerR) / max(bw, 1e-5), 0.0, 1.0);    vec2 rdir = (d > 0.0) ? toC / d : vec2(1.0, 0.0);    vec3 n = normalize(vec3(rdir * sin(s * 1.57079632679), cos(s * 1.57079632679)));    vec3 L = normalize(vec3(0.55, 0.45, 0.72));    vec3 H = normalize(L + vec3(0.0, 0.0, 1.0));    vec3 base = sampleExpCam(ctr / iResolution.xy);    vec3 shade = base * (0.35 + 0.65 * max(dot(n, L), 0.0)) * mix(1.2, 1.0, s) + pow(max(dot(n, H), 0.0), specP) * specI;    return clamp(mix(bg, shade, disc), 0.0, 1.0);}

vec3 renderMirrorZoomTiles(vec2 uv, vec2 fragCoord) {    float zoomCtl = clamp(uAsciiDensity, 0.2, 1.6);    float speed = mix(0.50, 1.60, zoomCtl / 1.6);    float pulseAmp = (uColorMode == 1) ? 0.70 : ((uColorMode == 2) ? 0.90 : 0.48);    float zoom = (sin(iTime * speed) * 0.5 + 0.5) * pulseAmp;    float side = (uColorMode == 0) ? 0.12 : ((uColorMode == 1) ? 0.085 : 0.060);    vec2 uv1 = fragCoord / iResolution.x;    vec2 center = side * round(uv1 / side);    center.y *= iResolution.x / iResolution.y;    vec2 muv = fragCoord / iResolution.xy;    muv -= zoom * (center - vec2(0.5));    muv -= 0.5;    muv *= 1.0 + zoom * (1.0 + zoomCtl * 0.35);    muv += 0.5;    muv = abs(muv);    muv = step(1.0, muv) * 2.0 + sign(1.0 - muv) * muv;    vec3 col = texture(iChannel0, safeUV(cameraMirrorUV(muv))).rgb;    return clamp(col, 0.0, 1.0);}

vec3 renderChromaticTrails(vec2 uv, vec2 fragCoord) {    vec2 cuv = safeUV(cameraMirrorUV(uv));    float intensity = clamp(uAsciiDensity, 0.5, 2.4);    float inorm = (intensity - 0.5) / 1.9;    int tests = int(mix(6.0, 16.0, inorm));    float stride = mix(0.60, 1.20, inorm);    vec3 acc = vec3(0.0);    const int MAX_TESTS = 16;    for (int j = 0; j < MAX_TESTS; j++) {        if (j >= tests) break;        float fi = float(j);        vec2 suv = safeUV(cuv + vec2(0.0, -(fi * stride) / iResolution.y));        vec3 src = texture(iChannel0, suv).rgb;        vec3 wave = sin(fi / 40.0 + 6.2831853 * (vec3(0.0, 0.33, 0.66) + src)) * 0.5 + 0.5;        acc = max(acc, wave);    }    vec3 col = sin((vec3(0.0, 0.33, 0.66) + acc + cuv.y) * 6.2831853) * 0.5 + 0.5;    if (uColorMode == 1) {        col = clamp(col.gbr * vec3(1.25, 1.05, 1.20), 0.0, 1.0);    } else if (uColorMode == 2) {        col = thermalJet(getLuma(col));    }    float grain = (hash12(fragCoord + vec2(iTime * 33.0, iTime * 19.0)) - 0.5) * (0.02 + 0.02 * inorm);    col += grain;    return clamp(col, 0.0, 1.0);}

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
    } else if (uEffectMode == 3) {
        color = renderRasterVision(uv, fragCoord);
    } else if (uEffectMode == 4) {
        color = renderDatamoshTrails(uv, fragCoord);
    } else if (uEffectMode == 5) {
        color = renderVhsTrackingBurn(uv, fragCoord);
    } else if (uEffectMode == 6) {
        color = renderPosterizeGlitchComic(uv, fragCoord);
    } else if (uEffectMode == 7) {
        color = renderLensDotBevel(uv, fragCoord);
    } else if (uEffectMode == 8) {
        color = renderMirrorZoomTiles(uv, fragCoord);
    } else {
        color = renderChromaticTrails(uv, fragCoord);
    }
    fragColor = vec4(color, 1.0);
}
