uniform sampler2D iChannel0;

// 1.0 = mantieni 4:3 con bande nere, 0.0 = stretch fullscreen
#define KEEP_ASPECT 1.0

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    float screenAR = iResolution.x / iResolution.y;  // es. 1.778 (16:9)
    float camAR    = 4.0 / 3.0;                       // 1.333

    // scale > 1: la cam è più stretta dello schermo -> pillarbox
    float scale = screenAR / camAR;
    vec2 uv_corrected;
    uv_corrected.y = uv.y;
    uv_corrected.x = (uv.x - 0.5) * scale + 0.5;

    vec2 final_uv = mix(uv, uv_corrected, KEEP_ASPECT);

    if (KEEP_ASPECT > 0.5 && (final_uv.x < 0.0 || final_uv.x > 1.0)) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    fragColor = texture(iChannel0, final_uv);
}
