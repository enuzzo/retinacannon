# Retina Cannon

![Python](https://img.shields.io/badge/Python-3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![OpenGL ES](https://img.shields.io/badge/OpenGL%20ES-2.0-A855F7?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)

> _"What if I took the live camera feed and ran it through a shader that makes everything look like a 1970s vector art fever dream?"_
> - someone who had clearly watched too many Rutt-Etra videos at 2am and owned a Raspberry Pi.

**Retina Cannon** is a real-time camera-to-shader visual engine for Raspberry Pi.

This is not a camera filter app. Camera filter apps have sliders and a share button. This has a GLSL pipeline, a bare-metal DRM/KMS renderer, and a keyboard thread that intercepts Ctrl+C before the OS even knows it happened.

It grabs live video from the Pi Camera, feeds every frame into a fragment shader running on the GPU, and blasts the result fullscreen: no X server, no compositor, no display manager asking if you're sure. Just OpenGL ES talking directly to the display hardware, the way it was meant to be.

---

## Why this exists

Like most Raspberry Pi projects, this one started with a purchasing decision that seemed completely reasonable at the time.

The logic goes like this: *"I already have three Pis, but this one will be different: I'll use it as a dedicated Doom server / home NAS (I already have a NAS) / weather station for a city I don't live in / automatic cat feeder (no cat) / retro gaming console (will play it twice) / AI assistant that listens to everything I say (fine, maybe not that one)."*

Four Pis later, they sit on the desk. They don't say anything. They just look at you. Judgmentally. With their little red power LEDs.

At some point the only reasonable response is to give one of them a camera, a monitor, and a reason to live. Hence: Retina Cannon.

**The actual use case** is beautifully stupid: print a nice 3D-printed enclosure *(files coming soon - yes, we will actually share them, wiiiwwww 🎉)*, walk into a friend's place with a 100-inch TV doing absolutely nothing, plug in AC + HDMI, and suddenly you're the most interesting person at the party. No streaming service. No game console. Just a $40 computer turning your guests into glitchy CRT sculptures in real time.

**What's coming:** encoder knob and gesture controls, already prototyped on breadboard, already working, just not integrated yet. This is because the author also needs to eat, sleep, and occasionally interact with other humans. The todos are real. The timeline is optimistic. You know how it goes.

---

## What it does

Two effects, switchable live:

### Rutt-Etra CRT

In 1973, [Bill Rutt and Steve Etra](https://en.wikipedia.org/wiki/Rutt/Etra_Video_Synthesizer) built an analog video synthesizer that deflected scan lines based on the luminance of the incoming signal. It cost as much as a car, weighed as much as a refrigerator, and produced visuals that looked like the world was made of oscilloscope traces.

This is the same thing. In GLSL. On a $40 computer. Running at 20 FPS.

Frame luminance warps the scan lines. CRT curvature bends the edges. Vignette darkens the corners. Noise adds grain. Your face becomes a vector field. It is deeply unsettling in the best possible way.

### ASCII Cam

Every camera pixel gets mapped to a glyph from an 8×8 bitmap font hardcoded inside the shader itself. Luminance picks the character. The whole thing runs on the GPU, in real time, with no CPU involvement in the actual rendering.

It's that thing you watched on YouTube in 2007, convinced someone had spent weeks on it. It runs here at 20 FPS on hardware you can power from a phone charger.

---

## How it works

```
Pi Camera (BGR888, 1640×1232)
    │
    │  Picamera2 + libcamera
    ▼
capture thread  ──(threading.Lock)──▶  latest frame
                                            │
                                  C render loop (kms-glsl)
                                            │
                                  Python render callback
                                            │
                                  glTexSubImage2D  ← upload frame to GPU
                                            │
                                  GLSL fragment shader
                                            │
                                  DRM/KMS output (fullscreen, no windowing system)
```

**Capture**: a daemon thread runs continuously and keeps the latest frame behind a lock. The render loop always gets the freshest frame available and never blocks waiting for one.

**Render**: `kms-glsl`'s C loop fires a Python callback every frame. That callback uploads the texture and sets all the GLSL uniforms: color mode, wave intensity, character density, effect mode, view mode, camera aspect ratio. Python orchestrates; the GPU executes.

**Shader**: all visual logic lives in `rutt_etra.frag`. It is a single fragment shader that implements two completely different visual systems and switches between them via a uniform. The CPU has no idea what's happening visually and that's fine.

**Keyboard**: a separate thread reads from `/dev/tty` with `ICANON`, `ECHO`, and `ISIG` all disabled. This means the kernel's job of turning Ctrl+C into a SIGINT is explicitly circumvented. The signal arrives as raw `\x03` bytes, caught in Python, used to trigger a graceful shutdown. This is not an accident.

**stdin**: replaced with a silent pipe at startup. Without this, `kms-glsl`'s C code would interpret terminal activity on fd 0 as user input and behave unpredictably. The write end of the pipe doubles as the shutdown signal mechanism. Two problems, one ugly-but-effective solution.

---

## Requirements

- Raspberry Pi with camera support enabled
- `python3`, `libcamera`, `picamera2`
- [`kms-glsl`](https://github.com/keithzg/kms-glsl) - the C rendering backbone, expected in one of:
  - `KMS_GLSL_DIR` environment variable
  - `../kms-glsl` sibling directory ← recommended
  - `~/kms-glsl`

Recommended layout on the Pi:
```
~/kms-glsl/       ← external dependency
~/retinacannon/   ← this repo
```

If `kms-glsl` is missing, the launcher prints `[FATAL]` and exits. No cryptic import errors, no silent hangs.

---

## Run

```bash
./start_cannon.sh
```

Specific shader:
```bash
./run_rutt.sh     # Rutt-Etra (default)
./run_base.sh     # raw camera passthrough, for when you just want to see if the camera works
```

Non-standard `kms-glsl` location:
```bash
KMS_GLSL_DIR=/path/to/kms-glsl ./start_cannon.sh
```

---

## Controls

| Key | Action |
|---|---|
| `↑` / `↓` | Cycle color mode |
| `←` / `→` | Rutt-Etra: wave intensity / ASCII: character density |
| `Space` | Switch effect (Rutt-Etra ↔ ASCII Cam) |
| `V` | Cycle view mode (16:9 → 4:3 → Fisheye) |
| `F` | Toggle FPS logging to terminal |
| `Ctrl+C` | Clean shutdown |

Arrow keys work with both `ESC [` and `ESC O` escape sequences, because terminal emulators are an ungoverned wilderness and standardization is aspirational.

---

## Color modes

**Rutt-Etra**: `B/W` · `Colors` · `Prism Warp` · `Acid Melt`

**ASCII Cam**: `Color symbols` · `Monochrome symbols` · `Inverted mono` · `Inverted color`

Default startup: Rutt on `Prism Warp`, ASCII on `Color symbols`. Both picked by someone with strong opinions about what looks good at a gallery opening.

---

## Performance

~20 FPS on target hardware. Consistent. Measured. The original Rutt-Etra ran at whatever frame rate the video signal had. This runs at whatever the GPU and DRM pipeline can sustain. Same aesthetic; fractionally lower barrier to entry.

---

## Notes for developers

**`c_float()` is not optional.** Float uniforms passed to OpenGL via ctypes must be explicitly wrapped. If you skip it, the GPU receives garbage and the image becomes a psychedelic disaster. Impressive, but not what you wanted.

**The GIL is load-bearing here.** Globals like `current_rutt_wave` and `current_effect_mode` are written by the keyboard thread and read by the render callback with no explicit locking. CPython's GIL makes these reads atomically safe. If you port this to a free-threaded Python build, add locks. You have been warned.

**Testing without Pi hardware** will fail immediately. `Picamera2` won't import, EGL won't initialize, and `kms-glsl` will complain about the absence of a DRM device. This is correct behavior.

Syntax checks that work anywhere:
```bash
python3 -m py_compile retina_cannon.py
bash -n start_cannon.sh
```

---

## License

MIT - [Netmilk Studio sagl](https://netmilk.studio)

Do what you want with it. Attribution appreciated. Don't blame us if it runs at an art show and someone asks you to explain what a fragment shader is.
