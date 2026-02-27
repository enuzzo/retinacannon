# Retina Cannon

> _"What if I took the live camera feed and ran it through a shader that makes everything look like a 1970s vector art fever dream?"_
> — someone who had clearly seen too many Rutt-Etra videos at 2am.

**Retina Cannon** is a real-time camera-to-shader visual engine for Raspberry Pi. It grabs the live Pi Camera feed, pushes it through a GLSL pipeline, and renders the output directly via DRM/KMS + OpenGL ES — no X11, no Wayland, no excuses. Straight to the framebuffer, the way nature intended.

The result? Reality filtered through the aesthetic of a 1970s graphics machine that dropped acid. Or rendered in ASCII. Depends on the mood.

---

## What it does

Two main effects, switchable on the fly:

### Rutt-Etra CRT
Inspired by the [Rutt/Etra Scan Processor](https://en.wikipedia.org/wiki/Rutt/Etra_Video_Synthesizer) — a 1973 analog video synthesizer that deflected scan lines based on the luminance of the signal. Same concept, GLSL, Raspberry Pi, 20 FPS. Frame luminance warps the scan lines, adds CRT curvature, vignette, grain. Your face becomes an oscilloscope.

### ASCII Cam
Maps every camera pixel to a glyph from an 8×8 bitmap font hardcoded in the shader. Luminance picks the character. The result is that thing you watched on YouTube in 2007, now running in real time on hardware that costs €40.

---

## How it works

```
Pi Camera (BGR888, 1640×1232)
    │
    │  Picamera2 + libcamera
    ▼
capture thread  ──(threading.Lock)──▶  frame buffer
                                            │
                                  render callback (C)
                                            │
                                    glTexSubImage2D
                                            │
                                  GLSL fragment shader
                                            │
                                  DRM/KMS output (fullscreen)
```

- **Capture** — daemon thread runs continuously, always holds the freshest frame behind a lock. The render loop never blocks waiting for a new frame.
- **Render** — `kms-glsl`'s C loop calls a Python callback every frame. That's where the texture gets uploaded and uniforms get set (color mode, wave, density, effect, camera aspect ratio).
- **Shader** — all the visual logic lives in `rutt_etra.frag`. Python passes parameters, the GPU does the actual work.
- **Keyboard** — separate thread on `/dev/tty` in raw mode, `ICANON`/`ECHO`/`ISIG` all off. Ctrl+C arrives as `\x03` instead of SIGINT, which lets the C render loop shut down cleanly without drama.
- **stdin** — replaced with a silent pipe at startup, so `kms-glsl` doesn't interpret terminal activity as "something weird happened".

---

## Requirements

- Raspberry Pi with camera support enabled
- `python3`, `libcamera`, `picamera2`
- [`kms-glsl`](https://github.com/keithzg/kms-glsl) in one of these locations:
  - `KMS_GLSL_DIR` environment variable
  - `../kms-glsl` sibling directory (recommended)
  - `~/kms-glsl`

Recommended layout:
```
~/kms-glsl/       ← external dependency
~/retinacannon/   ← this repo
```

---

## Run

```bash
./start_cannon.sh
```

With a specific shader:
```bash
./run_rutt.sh     # Rutt-Etra (default)
./run_base.sh     # raw camera passthrough
```

With kms-glsl in a non-standard location:
```bash
KMS_GLSL_DIR=/path/to/kms-glsl ./start_cannon.sh
```

---

## Controls

| Key | Action |
|---|---|
| `↑` / `↓` | Cycle color mode |
| `←` / `→` | Rutt-Etra: wave intensity — ASCII: character density |
| `Space` | Toggle effect (Rutt-Etra ↔ ASCII Cam) |
| `V` | Cycle view mode (16:9 → 4:3 → Fisheye) |
| `F` | Toggle FPS logging to terminal |
| `Ctrl+C` | Clean shutdown |

---

## Color modes

**Rutt-Etra** — `B/W` · `Colors` · `Prism Warp` · `Acid Melt`

**ASCII Cam** — `Color symbols` · `Monochrome symbols` · `Inverted mono` · `Inverted color`

Defaults: Rutt starts on `Prism Warp`, ASCII on `Color symbols`. Both chosen by someone with a clear sense of visual drama.

---

## Performance

~20 FPS on target hardware. Stable, verified. Not 60 FPS — but the original Rutt-Etra didn't do 60 FPS either, and that thing cost as much as a car.

---

## Developer notes

- Float uniforms passed via ctypes **must be wrapped with `c_float()`**. If the image turns into a mosaic of cosmic glitches, you probably forgot this.
- The arrow key parser handles both `ESC [` and `ESC O` prefixes — because terminals are a chaotic ecosystem and no standard is ever truly standard.
- Globals like `current_rutt_wave` and `current_effect_mode` are written from the keyboard thread and read from the render callback with no extra locks. CPython's GIL makes these reads atomically safe. Not a bug, a deliberate design decision.

---

## Testing

Without Pi hardware (camera + DRM/KMS display) the project won't start. That's expected.

What works anywhere:
```bash
python3 -m py_compile retina_cannon.py  # syntax check
bash -n start_cannon.sh                 # shell syntax check
```

On Pi: run `./start_cannon.sh`, verify ~20 FPS, test all controls.

---

## License

MIT — [Netmilk Studio sagl](https://netmilk.studio)

Do what you want. Credit if you can. Don't break anything important.
