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
   from Picamera2, stores the latest frame behind a `threading.Lock`.
2. **Render callback** — called by kms-glsl's C render loop; uploads the latest
   camera frame to a GL texture (`glTexSubImage2D`) and sets uniform values
   (color mode, wave, density, effect mode, view mode, camera aspect).
3. **GLSL shader** — `rutt_etra.frag` implements two effects:
   - **Rutt-Etra CRT** — luminance-displaced scan lines with CRT curvature, scanlines, vignette, noise.
   - **ASCII Cam** — maps luminance to bitmap font glyphs (upper/lower/digits from font8x8_basic).
4. **Keyboard thread** — reads from `/dev/tty` in raw mode (ICANON+ECHO+ISIG off),
   handles arrow keys (both ESC[ and ESCO prefixes), Space, V, F, Ctrl+C.

### Key design decisions

- **ISIG disabled on TTY** — Ctrl+C is caught as `\x03` in the keyboard thread
  instead of generating SIGINT; this allows graceful renderer shutdown via the
  stdin-pipe trick (`_quiet_stdin_w`).
- **Globals without locks** — `current_rutt_wave`, `current_effect_mode`, etc.
  are written from the keyboard thread and read from the render callback.
  CPython's GIL makes atomic int/float reads safe here; no extra lock needed.
- **stdin detached** — fd 0 is replaced with an idle pipe so kms-glsl's C code
  doesn't interpret stdin activity as "user interrupted". The pipe write-end
  (`_quiet_stdin_w`) is used to signal graceful stop.

## External dependency: kms-glsl

This project depends on `kms-glsl`, a separate local repository that provides
the C rendering library, Python bindings (`lib/glsl`, `lib/options`), and GL
constants (`gl.py`).

**Path resolution order** (both Python and shell scripts):
1. `KMS_GLSL_DIR` environment variable (if set and contains `lib/`)
2. `../kms-glsl` relative to this repo (sibling directory)
3. `~/kms-glsl` in the user's home

If none found, scripts exit with a clear `[FATAL]` message.

On the target Raspberry Pi, the typical layout is:
```
~/kms-glsl/          ← kms-glsl checkout
~/retinacannon/      ← this repo
```

## Project files

| File | Role |
|---|---|
| `retina_cannon.py` | Main runtime: camera init, GL setup, render loop, keyboard controls |
| `rutt_etra.frag` | Active GLSL shader (Rutt-Etra + ASCII effects) |
| `start_cannon.sh` | Canonical launcher script |
| `run_rutt.sh` | Quick launcher for Rutt-Etra shader |
| `run_base.sh` | Quick launcher for camera passthrough shader |
| `cam_passthrough.frag` | Camera passthrough shader |
| `cam_test.frag` | Camera test shader |
| `camera_test.frag` | Minimal camera test |
| `luce.frag` | Light test shader |
| `test.frag` | Basic test shader |
| `rutt_extra.frag` | Experimental Rutt variant |

## How to run

```bash
./start_cannon.sh
```

Or with a specific shader:
```bash
./start_cannon.sh  # uses rutt_etra.frag by default
./run_base.sh      # uses cam_passthrough.frag
```

Override kms-glsl location:
```bash
KMS_GLSL_DIR=/path/to/kms-glsl ./start_cannon.sh
```

## Runtime controls

| Key | Action |
|---|---|
| Arrow Up/Down | Cycle color mode |
| Arrow Left/Right | Adjust wave (Rutt) or density (ASCII) |
| Space | Toggle effect mode (Rutt-Etra / ASCII Cam) |
| V | Cycle view mode (16:9 / 4:3 / Fisheye) |
| F | Toggle FPS logging (terminal only) |
| Ctrl+C | Graceful shutdown |

## Defaults

- **Rutt-Etra** color mode: `Prism Warp` (index 2)
- **ASCII Cam** color mode: `Color symbols` (index 0)
- **Rutt wave**: 0.40 (range 0.40–3.80, step 0.10)
- **ASCII density**: 3.00 (range 1.00–6.00, step 0.20)
- **View mode**: Fisheye (index 2)
- **FPS baseline**: ~20 FPS on target hardware

## Testing

**This project cannot be smoke-tested without Raspberry Pi hardware** (camera +
DRM/KMS display). On non-Pi environments, `Picamera2` import or GLFW/EGL init
will fail. This is expected.

Validation checklist:
- `python3 -m py_compile retina_cannon.py` — syntax check (works anywhere)
- `bash -n start_cannon.sh` — shell syntax check
- On Pi: run `./start_cannon.sh`, verify ~20 FPS, test all keyboard controls

## Coding conventions

- All project-facing text in English (comments, docs, commit messages).
- Keep patches small and single-purpose.
- Never store secrets in versioned files — use `.env.local`, `config.local.h`, etc.
- Float uniforms passed through ctypes must use `c_float()` wrapper.
- Arrow key parser must handle both `ESC [` and `ESC O` prefixes.

## Multi-agent collaboration

This repo is worked on by both **Claude Code** and **OpenAI Codex**.
- Claude context: this file (`CLAUDE.md`)
- Codex context: `.codex/MEMORY.md` and `.codex/SESSION_LOG.md`
- Both agents follow the same coding conventions and commit style.
