uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uDistortion;
uniform int uEffectMode;

#define LINES 80.0
#define LINE_WIDTH 0.0026
#define EXTRUSION 0.055
#define CRT_CURVATURE 0.065
#define NOISE_STRENGTH 0.025

float getLuma(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 warpCRT(vec2 uv) {
    vec2 p = uv * 2.0 - 1.0;
    float r2 = dot(p, p);
    p *= 1.0 + CRT_CURVATURE * r2;
    return p * 0.5 + 0.5;
}

vec3 getLineColor(int mode, vec3 camColor) {
    if (mode == 0) return vec3(1.0);            // White monochrome
    if (mode == 1) return vec3(0.1, 1.0, 0.3);  // Green phosphor
    if (mode == 2) return vec3(1.0, 0.5, 0.05); // Amber CRT
    return camColor * 1.8;                      // Camera colors
}

float glyphInk(vec2 p, int level) {
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

vec3 renderRutt(vec2 uv, vec2 fragCoord) {
    float hJitter = (hash12(vec2(floor(uv.y * LINES), floor(iTime * 35.0))) - 0.5) * 0.0025;
    uv.x = clamp(uv.x + hJitter, 0.0, 1.0);

    float baseI = floor(uv.y * LINES);
    float normI = baseI / LINES;

    float px = 1.0 / iResolution.x;
    float luma =
        getLuma(texture(iChannel0, vec2(uv.x - px * 2.0, normI)).rgb) * 0.1 +
        getLuma(texture(iChannel0, vec2(uv.x - px, normI)).rgb) * 0.2 +
        getLuma(texture(iChannel0, vec2(uv.x, normI)).rgb) * 0.4 +
        getLuma(texture(iChannel0, vec2(uv.x + px, normI)).rgb) * 0.2 +
        getLuma(texture(iChannel0, vec2(uv.x + px * 2.0, normI)).rgb) * 0.1;

    vec3 camColor = texture(iChannel0, vec2(uv.x, normI)).rgb;
    float lineY = normI + luma * (EXTRUSION * uDistortion);
    float dist = abs(uv.y - lineY);

    float lineAlpha = 1.0 - smoothstep(0.0, LINE_WIDTH, dist);
    float glow = (1.0 - smoothstep(0.0, LINE_WIDTH * 6.0, dist)) * 0.28 * luma;
    float scan = 0.96 + 0.04 * sin((uv.y * iResolution.y) * 3.14159265);
    float grille = 0.98 + 0.02 * sin((uv.x * iResolution.x) * 1.5);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.22);
    float noise = (hash12(fragCoord + vec2(iTime * 60.0, iTime * 13.0)) - 0.5) * NOISE_STRENGTH;

    vec3 lineCol = getLineColor(uColorMode, camColor);
    vec3 color = lineCol * (lineAlpha + glow);
    color *= scan * grille * mix(0.55, 1.0, vignette);
    color *= 1.25;
    color += noise;
    return clamp(color, 0.0, 1.0);
}

vec3 renderAscii(vec2 uv, vec2 fragCoord) {
    float charAspect = 1.90;
    vec2 grid = vec2(120.0, floor(120.0 * iResolution.y / iResolution.x / charAspect));
    grid.y = max(grid.y, 24.0);

    vec2 cell = uv * grid;
    vec2 cellId = floor(cell);
    vec2 cellUV = fract(cell);

    vec2 sampleUV = (cellId + 0.5) / grid;
    vec3 camColor = texture(iChannel0, sampleUV).rgb;
    float luma = getLuma(camColor);

    float boosted = clamp(pow(luma, 0.82), 0.0, 1.0);
    int level = int(clamp(floor(boosted * 8.0), 0.0, 7.0));

    vec2 p = cellUV - 0.5;
    p.y *= charAspect;
    float ink = glyphInk(p, level);

    float scan = 0.90 + 0.10 * sin(fragCoord.y * 3.14159265);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.26);
    float noise = (hash12(cellId + floor(iTime * 24.0)) - 0.5) * 0.04;

    vec3 tint = getLineColor(uColorMode, camColor);
    vec3 color = tint * ink * (0.35 + boosted * 1.1);
    color += tint * (0.03 + boosted * 0.04);
    color += noise * (0.25 + ink * 0.75);
    color *= scan * mix(0.30, 1.0, vignette);
    return clamp(color, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    uv = warpCRT(uv);
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color = renderRutt(uv, fragCoord);
    if (uEffectMode == 1) {
        color = renderAscii(uv, fragCoord);
    }
    fragColor = vec4(color, 1.0);
}
