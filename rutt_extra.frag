#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform sampler2D u_tex0;
uniform float u_time;

// Valori fissi per il test (belli e pronti)
const float lines = 60.0;
const float extrusion = 0.5;
const float brightness = 1.8;
const float yscale = 0.8;

float getLuma(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    vec3 finalColor = vec3(0.05, 0.05, 0.08);

    for(float i = 60.0; i >= 0.0; i--) {
        float normIndex = i / 60.0;
        vec2 sampleUV = vec2(uv.x, normIndex);
        
        // Prendiamo il video
        vec3 texColor = texture2D(u_tex0, sampleUV).rgb;
        float luma = getLuma(texColor);

        // Deformazione Rutt-Etra
        float lineY = (normIndex * yscale) - 0.1;
        lineY += luma * extrusion;

        float dist = uv.y - lineY;
        float aaWidth = max(fwidth(dist), 0.001);
        float lineAlpha = 1.0 - smoothstep(0.0, aaWidth * 1.5, abs(dist));

        vec3 lineColor = texColor * brightness;

        float fillAlpha = 1.0 - smoothstep(0.0, aaWidth, dist);
        if (fillAlpha > 0.5) { finalColor = mix(finalColor, vec3(0.0), 1.0); }
        finalColor = mix(finalColor, lineColor, lineAlpha);
    }
    gl_FragColor = vec4(finalColor, 1.0);
}
