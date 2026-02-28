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
4. **GLSL shader** — `rutt_etra.frag` implements five effects via `uEffectMode`:
   - **0 Rutt-Etra CRT** — luminance-displaced scan lines, CRT curvature, vignette, noise
   - **1 ASCII Cam** — bitmap font glyphs mapped from luminance (font8x8_basic)
   - **2 Pixel Art** — camera pixelated to a block grid with retro palette modes
   - **3 Signal Ghost** — interactive generative typography driven by motion/presence
   - **4 Raster Vision** — dedicated variable-dot raster/halftone modes (thermal + comic looks)
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
| `uEffectMode` | int | 0=Rutt, 1=ASCII, 2=PixelArt, 3=SignalGhost, 4=RasterVision |
| `uColorMode` | int | Per-effect color palette index |
| `uRuttWave` | float | Rutt-Etra displacement multiplier (0.40–3.80) |
| `uAsciiDensity` | float | ASCII density / Ghost field density (1.0–6.0) |
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

**Rutt-Etra (uEffectMode=0):** B/W · Colors · Prism Warp · Acid Melt

**ASCII Cam (uEffectMode=1):** Color symbols · Monochrome symbols · Inverted mono · Inverted color

**Pixel Art (uEffectMode=2):** Full Color · Game Boy · CGA · Phosphor · Amber

**Signal Ghost (uEffectMode=3):** Void · Matrix · Ghost Cam · Neon · Thermal · Chromatic

**Raster Vision (uEffectMode=4):** Thermal Raster · Thermal Inverted · Comic B/W · Comic Pastel · Vibrant Pop

## Runtime controls

| Key | Action |
|---|---|
| Space | Cycle effect mode |
| S | 3-second countdown then save rendered screenshot to `shots/` |
| ↑ / ↓ | Cycle color mode (per-effect independent) |
| ← / → | Adjust effect parameter (wave/density/size/field density/dot size) |
| V | Cycle view mode |
| M | Toggle horizontal mirror of current view |
| F | Toggle FPS terminal logging |
| Ctrl+C | Graceful shutdown |

## Defaults

- **Default view**: 16:9
- **Rutt-Etra** color: `Prism Warp` (index 2)
- **ASCII Cam** color: `Color symbols` (index 0), density 3.00
- **Pixel Art** color: `Game Boy` (index 1), block size 16px
- **Signal Ghost** color: `Void` (index 0), field density 2.0
- **Raster Vision** color: `Thermal Raster` (index 0), dot size 12px
- **Rutt wave**: 0.40 (range 0.40–3.80, step 0.10)
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
