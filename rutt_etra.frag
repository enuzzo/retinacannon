uniform sampler2D iChannel0;
uniform int uColorMode;

#define LINES 80.0
#define LINE_WIDTH 0.0015
#define EXTRUSION 0.055

float getLuma(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

vec3 getLineColor(int mode, vec3 camColor) {
    if (mode == 0) return vec3(1.0);          // Bianco
    if (mode == 1) return vec3(0.1, 1.0, 0.3); // Verde phosphor
    if (mode == 2) return vec3(1.0, 0.5, 0.05); // Ambra CRT
    return camColor * 2.0;                    // Colori camera
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;
    float baseI = floor(uv.y * LINES);
    float normI = baseI / LINES;

    float px = 1.0 / iResolution.x;
    float luma =
        getLuma(texture(iChannel0, vec2(uv.x - px*2.0, normI)).rgb) * 0.1 +
        getLuma(texture(iChannel0, vec2(uv.x - px,     normI)).rgb) * 0.2 +
        getLuma(texture(iChannel0, vec2(uv.x,           normI)).rgb) * 0.4 +
        getLuma(texture(iChannel0, vec2(uv.x + px,     normI)).rgb) * 0.2 +
        getLuma(texture(iChannel0, vec2(uv.x + px*2.0, normI)).rgb) * 0.1;

    vec3 camColor = texture(iChannel0, vec2(uv.x, normI)).rgb;
    float lineY = normI + luma * EXTRUSION;
    float dist = abs(uv.y - lineY);

    float lineAlpha = 1.0 - smoothstep(0.0, LINE_WIDTH, dist);
    float glow = (1.0 - smoothstep(0.0, LINE_WIDTH * 5.0, dist)) * 0.15 * luma;

    vec3 lineCol = getLineColor(uColorMode, camColor);
    fragColor = vec4(clamp(lineCol * (lineAlpha + glow), 0.0, 1.0), 1.0);
}
