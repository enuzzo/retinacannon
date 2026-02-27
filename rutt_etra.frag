uniform sampler2D iChannel0;
uniform int uColorMode;
uniform float uDistortion;

#define LINES 80.0
#define LINE_WIDTH 0.0015
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

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    uv = warpCRT(uv);
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

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
    float glow = (1.0 - smoothstep(0.0, LINE_WIDTH * 5.0, dist)) * 0.15 * luma;
    float scan = 0.92 + 0.08 * sin((uv.y * iResolution.y) * 3.14159265);
    float grille = 0.95 + 0.05 * sin((uv.x * iResolution.x) * 1.5);
    float vignette = pow(clamp(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.0, 1.0), 0.22);
    float noise = (hash12(fragCoord + vec2(iTime * 60.0, iTime * 13.0)) - 0.5) * NOISE_STRENGTH;

    vec3 lineCol = getLineColor(uColorMode, camColor);
    vec3 color = lineCol * (lineAlpha + glow);
    color *= scan * grille * mix(0.35, 1.0, vignette);
    color += noise;

    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
