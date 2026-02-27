# Retina Cannon

Retina Cannon is a real-time camera-to-shader visual engine for Raspberry Pi.
It captures live video, feeds it into a GLSL pipeline, and renders a CRT-style effect through DRM/KMS + OpenGL ES.

## Features
- Live camera capture pipeline (Picamera2 + libcamera).
- Real-time shader rendering with `kms-glsl`.
- Interactive controls for color modes and per-effect parameters.
- Dual effect mode: Rutt-Etra CRT + ASCII Cam.
- Stable runtime baseline around 20 FPS on the current target setup.

## Requirements
- Raspberry Pi with camera support enabled.
- `python3`, `libcamera`, `picamera2`.
- Local `kms-glsl` checkout at `/home/enuzzo/kms-glsl`.

## Run
```bash
./start_cannon.sh
```

## Controls
- `Arrow Up/Down`: cycle color modes.
- `Arrow Left/Right`:
  - in `Rutt-Etra`: increase/decrease wave intensity/frequency.
  - in `ASCII Cam`: increase/decrease character density.
- `Space`: switch effect mode (Rutt-Etra / ASCII Cam).
- `Ctrl+C`: stop rendering.

## Color Modes
- `Rutt-Etra`: `B/W`, `Colors`, `Prism Warp`, `Acid Melt`.
- `ASCII Cam`: `Color symbols`, `Monochrome symbols`, `Monochrome letters`, `Color letters`.

## Project Files
- `retina_cannon.py`: main runtime and input handling.
- `rutt_etra.frag`: active shader effect.
- `start_cannon.sh`: canonical launcher script.
