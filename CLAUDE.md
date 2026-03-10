# CLAUDE.md — Retina Cannon

## What this project is

Retina Cannon is a real-time camera-to-shader visual engine for Raspberry Pi.
It captures live video from a Pi camera, feeds it into a GLSL fragment shader,
and renders the output directly to the display via DRM/KMS + OpenGL ES.

Copyright (c) Netmilk Studio sagl — MIT License.

## System architecture

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Pi Camera   │────▶│ retina_cannon.py │────▶│  rutt_etra.frag │
│ (Picamera2 + │     │  Python runtime   │     │  GLSL shader    │
│  libcamera)  │     │  + keyboard ctrl  │     │  (GPU-side)     │
└──────────────┘     └────────┬─────────┘     └────────┬────────┘
                              │                        │
                     ┌────────▼─────────┐     ┌────────▼────────┐
                     │    kms-glsl      │     │  OpenGL ES 2.0  │
                     │  (C library +    │────▶│  DRM/KMS output │
                     │   Python ctypes) │     │  (fullscreen)   │
                     └──────────────────┘     └─────────────────┘
```

### Data flow

1. **Camera capture thread** — daemon thread captures BGR888 frames at 1640×1232
   from Picamera2, stores the latest frame behind a `threading.Lock`. Also runs
   motion/presence detection at 1/8 resolution on each captured frame.
2. **Motion detection** — computed in the capture thread, not the render callback:
   - `_motion_level`: frame-diff magnitude with dead-zone noise filter + asymmetric
     smoothing (fast attack 0.65, slow decay 0.92)
   - `_presence_scale`: mean luminance of the downsampled frame
   - `_presence_cx/cy`: weighted centroid of above-average bright regions
3. **Render callback** — called by kms-glsl's C render loop; uploads the latest
   camera frame (`glTexSubImage2D`) and sets all uniforms every frame.
4. **GLSL shader** — `rutt_etra.frag` implements ten effects via `uEffectMode`:
   - **0 Rutt-Etra CRT** — luminance-displaced scan lines, CRT curvature, vignette, noise
   - **1 ASCII Cam** — bitmap font glyphs mapped from luminance (font8x8_basic)
   - **2 Pixel Art** — camera pixelated to a block grid with retro palette modes
   - **3 Raster Vision** — variable-dot raster/halftone modes (thermal + comic looks)
   - **4 Digital Codec Corruption** — macroblock jumps, smears, and glitch palettes
   - **5 VHS Tracking Burn** — tracking jitter, tape noise, RGB melt variants
   - **6 Posterize Glitch Comic** — quantized comic style with animated palette variants
   - **7 Lens Dot Bevel** — beveled disc mosaic look
   - **8 Mirror Zoom Tiles** — mirrored tile zoom pulses
   - **9 Chromatic Trails** — stacked chromatic trails
5. **Keyboard thread** — reads `/dev/tty` in raw mode via `select()` with 0.5s timeout
   (non-blocking so it exits cleanly when `_running` goes False).
6. **Signal handlers** — `SIGTERM` and `SIGHUP` trigger the same graceful shutdown
   path as Ctrl+C (`_request_renderer_stop()`).

### Key design decisions

- **ISIG disabled on TTY** — Ctrl+C is caught as `\x03` in the keyboard thread
  instead of generating SIGINT; allows graceful renderer shutdown via stdin-pipe trick.
- **Globals without locks** — `current_*` variables are written from keyboard thread,
  read from render callback. CPython's GIL makes atomic int/float reads safe.
- **stdin detached** — fd 0 replaced with an idle pipe so kms-glsl's C code doesn't
  interpret stdin activity as "user interrupted". Write end (`_quiet_stdin_w`) signals stop.
- **select() in keyboard thread** — `os.read(fd, 1)` would block forever when DRM
  takes the TTY into graphics mode. `select()` with 0.5s timeout allows clean exit.
- **Motion detection in capture thread** — computed alongside the frame copy, not in
  the render callback, so it doesn't add latency to the GL pipeline.
- **kms-glsl detected by `glsl.so`** — path resolution checks for `glsl.so` (not
  a `lib/` directory, which doesn't exist in this repo's kms-glsl layout).

## Hardware setup

### Raspberry Pi 4 (previous)

- **Camera**: IMX219 standard FOV, connected via 15-pin CSI ribbon cable
- `camera_auto_detect=1` in `/boot/firmware/config.txt` was sufficient
- FPS baseline: ~20 FPS

### Raspberry Pi 5 (current)

- **Camera**: IMX219 160° wide-angle (same sensor, fisheye lens)
- **Port**: CAM0 (nearest to Ethernet/USB)
- **Cable**: Official RPi5 15-to-22 pin adapter (RPi5 uses 22-pin FPC connectors)
- **Critical**: `camera_auto_detect=1` may fail to detect IMX219 on RPi5.
  Fix: add explicit overlay in `/boot/firmware/config.txt` under `[all]`:
  ```
  dtoverlay=imx219,cam0
  ```
- Camera is only enumerated at boot — hot-plugging won't work, reboot required.
- FPS baseline: TBD (RPi5 GPU is faster, expect improvement over RPi4)

### Troubleshooting camera detection

1. `rpicam-hello --list-cameras` — must show the IMX219 sensor
2. If not detected, check `dmesg | grep -i cfe` — no output means CSI driver
   didn't initialize for the camera
3. `sudo dtoverlay imx219 cam0` — runtime test before rebooting
4. Verify flat cable orientation: contacts face the PCB on both ends
5. Try the other CSI port (CAM0 ↔ CAM1) if still not detected

## External dependency: kms-glsl

**Path resolution order** (both Python and shell scripts):
1. `KMS_GLSL_DIR` environment variable (if set and contains `glsl.so`)
2. `../kms-glsl` relative to this repo
3. `~/kms-glsl` in the user's home

On the target Raspberry Pi:
```
~/kms-glsl/          ← kms-glsl checkout (contains glsl.so, lib.py, gl.py)
~/retinacannon/      ← this repo
```

## Project files

| File | Role |
|---|---|
| `retina_cannon.py` | Main runtime: camera, GL setup, render loop, keyboard, motion detection |
| `rutt_etra.frag` | Active GLSL shader (all four effects) |
| `start_cannon.sh` | Canonical launcher |
| `run_rutt.sh` | Quick launcher for rutt_etra shader |
| `run_base.sh` | Quick launcher for camera passthrough |
| `cam_passthrough.frag` | Camera passthrough shader |

## GLSL uniforms reference

| Uniform | Type | Description |
|---|---|---|
| `iChannel0` | sampler2D | Camera texture (BGR uploaded as GL_RGB — `.bgr` swizzle to correct) |
| `iResolution` | vec2 | Display resolution (set by kms-glsl) |
| `iTime` | float | Elapsed time in seconds (set by kms-glsl) |
| `uEffectMode` | int | 0=Rutt, 1=ASCII, 2=PixelArt, 3=Raster, 4=Codec, 5=VHS, 6=Poster, 7=LensDot, 8=MirrorZoom, 9=ChromaticTrails, 10=VectorProfileScope |
| `uColorMode` | int | Per-effect color palette index |
| `uRuttWave` | float | Rutt-Etra displacement multiplier (0.40–3.80) |
| `uAsciiDensity` | float | Shared per-effect scalar (ASCII density / codec amount / VHS tracking / poster levels / lens detail / mirror zoom / trail intensity); for Rutt-Etra routes the ↑/↓ secondary param per sub-mode (split / tint / contrast / interference) |
| `uPixelSize` | float | Pixel Art block size / Raster dot-cell size in screen pixels (4–48) |
| `uViewMode` | int | 0=16:9, 1=4:3, 2=Fisheye |
| `uMirror` | int | 0=off, 1=horizontal mirror of current view |
| `uCameraAspect` | float | Camera W/H ratio |
| `uMotionLevel` | float | Frame-diff motion magnitude 0–1 |
| `uPresenceScale` | float | Scene luminance proxy 0–1 |
| `uPresenceCX` | float | Presence centroid X (0–1) |
| `uPresenceCY` | float | Presence centroid Y (0–1, GL coords: 0=bottom) |
| `uShowFps` | int | FPS overlay enable |
| `uFpsValue` | float | Current FPS for overlay |

## Effect color modes

Naming convention: `NN` = effect index, `NN.MM` = color variant (1-based, matches ↑ cycling order
from the default). The list order below is the exact array order in `retina_cannon.py` — `NN.01`
is always the default (index 0), and ↑ arrow increments through the list.

**Rutt-Etra (uEffectMode=0):** 00.01 Prism Warp · 00.02 Phosphor · 00.03 Wire Mono · 00.04 v002 Terrain

**ASCII Cam (uEffectMode=1):** 01.01 Symbol Color · 01.02 Symbol Mono · 01.03 Dense Mono Mix · 01.04 Dense Color Mix

**Pixel Art (uEffectMode=2):** 02.01 Game Boy · 02.02 Pixel Native · 02.03 Toxic Candy

**Raster Vision (uEffectMode=3):** 03.01 Thermal Raster · 03.02 Thermal Inverted · 03.03 Comic Ink Mono · 03.04 Comic Pastel · 03.05 Vibrant Pop

**Digital Codec Corruption (uEffectMode=4):** 04.01 RGB Mosh · 04.02 Thermal Glitch · 04.03 Acid Trip · 04.04 Void Codec

**VHS Tracking Burn (uEffectMode=5):** 05.01 Signal Melt · 05.02 Night Tape

**Posterize Glitch Comic (uEffectMode=6):** 06.01 Warhol Pop · 06.02 Neon Cel · 06.03 Acid Bloom · 06.04 Plasma Burn

**Lens Dot Bevel (uEffectMode=7):** 07.01 Soft Bevel · 07.02 Hard Bevel · 07.03 Specular Punch · 07.04 Toxic Candy Drift · 07.05 Warhol Drift · 07.06 Neon Flux Drift · 07.07 Thermal Drift · 07.08 Spectral Delta Bloom

**Mirror Zoom Tiles (uEffectMode=8):** 08.01 Pulse · 08.02 Wide Pulse · 08.03 Hyper Pulse

**Chromatic Trails (uEffectMode=9):** 09.01 RGB Trail · 09.02 Neon Trail · 09.03 Thermal Trail

**Vector Profile Scope (uEffectMode=10):** 10.01 Scope Mono · 10.02 Camera Overlay · 10.03 Tint Overlay · 10.04 Thermal Overlay

## Runtime controls

| Key | Action |
|---|---|
| Space | Cycle effect mode |
| S | 3-second countdown then save rendered screenshot to `shots/` |
| PgUp / PgDn | Cycle color mode (per-effect independent) |
| ↑ / ↓ | Per-effect secondary tweak (e.g. terrain interference; no-op if not defined for current mode) |
| ← / → | Adjust active effect parameter (wave/density/size/raster/codec/VHS/poster/lens/mirror/trail) |
| V | Cycle view mode |
| M | Toggle horizontal mirror of current view |
| F | Toggle FPS terminal logging |
| Ctrl+C | Graceful shutdown |

## Defaults

- **Default view**: 16:9
- **Default effect**: `00 Rutt-Etra CRT`
- **Rutt-Etra** color: `00.01 Prism Warp` (index 0), wave 0.40 (range 0.05–3.80)
  - ↑/↓ per sub-mode: Prism Warp = split 1.0 (0.1–5.0) · Phosphor = tint 1.0 (0.0–2.0, 0=cyan/1=green/2=amber) · Wire Mono = contrast 1.0 (0.2–3.0) · Terrain = interference 1.5 (0.5–5.0)
- **ASCII Cam** color: `01.01 Symbol Color` (index 0), density 3.00 (range 1.00–6.00), contrast 1.0 (↑/↓, range 0.20–3.00 via uRuttWave channel)
- **Pixel Art** color: `02.01 Game Boy` (index 0), block size 6px (range 4–48)
- **Raster Vision** color: `03.01 Thermal Raster` (index 0), dot size 12px (range 4–48)
- **Digital Codec Corruption** color: `04.01 RGB Mosh` (index 0), amount 2.0 (range 0.5–6.0)
- **VHS Tracking Burn** color: `05.01 Signal Melt` (index 0), tracking 1.5 (range 0.5–5.0)
- **Posterize Glitch Comic** color: `06.01 Warhol Pop` (index 0), levels 4 (range 2–12)
- **Lens Dot Bevel** color: `07.01 Soft Bevel` (index 0), detail 2.6 (range 0.20–14.0)
- **Mirror Zoom Tiles** color: `08.01 Pulse` (index 0), zoom 0.80 (range 0.2–1.6)
- **Chromatic Trails** color: `09.01 RGB Trail` (index 0), intensity 1.20 (range 0.5–2.4)
- **Vector Profile Scope** color: `10.01 Scope Mono` (index 0), grid 2.20 (range 0.8–3.4)
- **FPS baseline**: ~20 FPS on RPi4

## Testing

**Cannot smoke-test without Raspberry Pi hardware** (camera + DRM/KMS display).

Validation checklist:
- `python3 -m py_compile retina_cannon.py` — syntax check (works anywhere)
- `bash -n start_cannon.sh` — shell syntax check
- On Pi: `./start_cannon.sh`, verify ~20 FPS, test all keyboard controls

## Shutdown safety

Never use `SIGKILL` to stop the process. The DRM master may not be released
and the display can be left in a state that survives a soft reboot, requiring
a hard power cycle. Safe kill from SSH:
```bash
kill -SIGINT $(pgrep -f retina_cannon.py)
```
`SIGTERM` and `SIGHUP` are also handled gracefully.

## Coding conventions

- All project-facing text in English (comments, docs, commit messages).
- Keep patches small and single-purpose.
- Never store secrets in versioned files.
- Float uniforms via ctypes must use `c_float()` wrapper.
- Arrow key parser must handle both `ESC [` and `ESC O` prefixes.
- New effect modes: add to `EFFECT_MODE_NAMES`, `_active_color_mode()`,
  `_set_active_color_mode()`, `_effect_param_label()`, `on_init`, `on_render`,
  keyboard left/right handler, and `mainImage()` in the shader.

## Multi-agent collaboration

This repo is worked on by both **Claude Code** and **OpenAI Codex**.
- Claude context: this file (`CLAUDE.md`)
- Codex context: `.codex/MEMORY.md` and `.codex/SESSION_LOG.md`
- Both agents follow the same coding conventions and commit style.
