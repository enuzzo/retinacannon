# Retina Cannon

![Retina Cannon Demo](demo/retinacannon.png)

![Python](https://img.shields.io/badge/Python-3-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![OpenGL ES](https://img.shields.io/badge/OpenGL%20ES-2.0-A855F7?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)

> "What if I took the live camera feed and ran it through a shader that makes everything look like a 1970s vector art fever dream?"
> _Someone who had clearly watched too many Rutt-Etra videos at 2am and owned a bunch of unused Raspberry Pis_

**Retina Cannon** is a real-time camera-to-shader visual engine for Raspberry Pi. Because, why not? WHY NOT?!?1! 🙃

This is not a camera filter app. Camera filter apps have sliders and a share button. This has a GLSL pipeline, a bare-metal DRM/KMS renderer, and a keyboard thread that intercepts Ctrl+C before the OS even knows it happened.

It grabs live video from the Pi Camera, feeds every frame into a fragment shader running on the GPU, and blasts the result fullscreen: no X server, no compositor, no display manager asking if you're sure. Just OpenGL ES talking directly to the display hardware, the way it was meant to be.

---

## Why this exists

Like most Raspberry Pi projects, this one started with a purchasing decision that seemed completely reasonable at the time.

The logic goes like this: *"I already have three Pis, but this one will be different: I'll use it as a dedicated Doom server / home NAS (I already have a NAS) / weather station for a city I don't live in / automatic cat feeder (no cat) / retro gaming console (will play it twice) / AI assistant that listens to everything I say (fine, maybe not that one)."*

Four Pis later, they sit on the desk. They don't say anything. They just look at you. Judgmentally. With their little red power LEDs.

At some point the only reasonable response is to give one of them a camera, a monitor, and a reason to live. Hence: Retina Cannon.

**The actual use case** is beautifully stupid: print a nice 3D-printed enclosure *(files coming soon)*, walk into a friend's place with a 100-inch TV doing absolutely nothing, plug in AC + HDMI, and suddenly you're the most interesting person at the party. No streaming service. No game console. Just a $40 computer turning your guests into glitchy CRT sculptures in real time.

**What's coming:** encoder knob and gesture controls, already prototyped on breadboard. Audio-reactive shaders, once the microphone is mounted. The todos are real. The timeline is optimistic. You know how it goes.

---

### TL;DR

*(Sprinkled with emojis because let's face it: reading is hard, and a proper TL;DR needs them—kind of like a toddler needing a picture book instead of actual text).*

* 📷 **The Pipeline:** Live Pi Cam → one GLSL Shader → Bare-Metal GPU. No desktop environment, no X11 bloat, zero compositor bullshit. Just pure graphical violence injected straight into the display hardware.
* ⌨️ **The Controls:** Mash `Space` to cycle through 11 reality-bending shaders. Arrow keys for live tweaks. `V/M/F/S` for View, Mirror, FPS, and Screenshots.
* 🚀 **The Execution:** Run `./start_cannon.sh`, point the lens at a human face, and instantly generate pretentious living-room glitch art.
* 💥 **The Dependencies:** You need a Raspberry Pi, a camera, and `kms-glsl`. If `glsl.so` is missing, the whole thing violently crashes and burns on launch. As it rightfully should.
* 🔌 **The Flex:** Plug in HDMI + AC at a party, step back, and let everyone assume you spent six agonizing weeks coding a custom cyber-art installation.

---

## Effects

Eleven effects, all in a single shader, switchable live with `Space`:

| ID | Effect |
|---|---|
| 00 | Rutt-Etra CRT |
| 01 | ASCII Cam |
| 02 | Pixel Art |
| 03 | Raster Vision |
| 04 | Digital Codec Corruption |
| 05 | VHS Tracking Burn |
| 06 | Posterize Glitch Comic |
| 07 | Lens Dot Bevel |
| 08 | Mirror Zoom Tiles |
| 09 | Chromatic Trails |
| 10 | Vector Profile Scope |

### Canonical Sub-Effect Catalog (EE.MM)

Use `EE.MM` as the canonical ID:
- `EE` = effect ID (`00..10`)
- `MM` = sub-effect/color-mode index (`01..N`)

This is the reference to communicate changes, cleanup tasks, and future renames without ambiguity.

#### 00 - Rutt-Etra CRT
| Code | Name | Brief Description | ↑/↓ secondary tweak |
|---|---|---|---|
| 00.01 | Prism Warp | Subtle chromatic RGB split with camera color bleed — default look. ←/→ = wave. | Chromatic split width (0.1–5.0, default 1.0) |
| 00.02 | Phosphor | P31-style phosphor CRT. ←/→ = wave. | Phosphor tint: 0=cyan · 1=green · 2=amber (default 1.0) |
| 00.03 | Wire Mono | Classic white scanline wireframe on black. ←/→ = wave. | Displacement contrast gamma (0.2–3.0, default 1.0) |
| 00.04 | v002 Terrain | Joy Division–style terrain with scan-line interference. ←/→ = wave. | Interference between adjacent lines (0.5–5.0, default 1.5) |

#### 01 - ASCII Cam
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 01.01 | Symbol Color | Color symbols | Symbol-only ASCII with source color preserved. | Source RGB, warm highlights |
| 01.02 | Symbol Mono | Monochrome symbols | Symbol-only ASCII in luminance grayscale. | White, gray, black |
| 01.03 | Dense Mono Mix | Dense Mono Mix | Dense letters+symbols mix (70/30), monochrome. | White, gray, black |
| 01.04 | Dense Color Mix | Dense Color Mix | Dense letters+symbols mix (70/30), full color. | Source RGB, teal, orange |

#### 02 - Pixel Art
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 02.01 | Pixel Native | Full Color | Clean pixelation with corrected camera color. | Source RGB |
| 02.02 | DMG Classic | Game Boy | DMG-style green palette with LCD pixel gap look. | Dark green, olive, pale lime |
| 02.03 | Toxic Candy | Toxic Candy | Neon quantized palette with rounded pixel corners. | Toxic green, cyan, candy magenta, cream |

#### 03 - Raster Vision
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 03.01 | Thermal Raster | Thermal Raster | Halftone thermal dots, blue-cold to red-hot. | Blue, cyan, yellow, red |
| 03.02 | Thermal Inverted | Thermal Inverted | Thermal mapping inverted (hot/cold flipped). | Red, orange, blue |
| 03.03 | Comic Ink Mono | Comic B/W | Black-ink halftone with edge lines. | Black, off-white |
| 03.04 | Comic Pastel | Comic Pastel | Posterized pastel halftone comic treatment. | Peach, mint, light blue, cream |
| 03.05 | Vibrant Pop | Vibrant Pop | Saturated pop-print raster with strong contrast edges. | Red, cyan, yellow, deep black |

#### 04 - Digital Codec Corruption
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 04.01 | RGB Mosh | RGB Mosh | Macroblock jumps plus chromatic smear artifacts. | Red, green, blue, glitch purple |
| 04.02 | Thermal Glitch | Thermal Glitch | Corruption mapped to heat-like thermal look. | Blue, cyan, yellow, red |
| 04.03 | Acid Trip | Acid Trip | Hue-rotated glitch bursts with neon corruption zones. | Lime, magenta, violet |
| 04.04 | Void Codec | Void Codec | Corrupted macroblocks collapse into black voids. | Black, white edges, cold blue |

#### 05 - VHS Tracking Burn
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 05.01 | Signal Melt | Signal Melt | Strong RGB channel separation and tracking melt. | Red, green, blue streaks |
| 05.02 | Night Tape | Night Tape | Security-cam phosphor style with heavy tape noise. | Phosphor green, black, gray |

#### 06 - Posterize Glitch Comic
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 06.01 | Warhol Pop | Warhol Pop | Hard poster levels with bold pop palette swaps. | Red, yellow, cyan, violet, lime |
| 06.02 | Neon Cel | Neon Cel | Neon edge ink on dark cel-style background. | Cyan, magenta, yellow, black |
| 06.03 | Acid Bloom | Acid Bloom | Animated HSV color cycling over quantized levels. | Full rainbow spectrum |
| 06.04 | Plasma Burn | Plasma Burn | Plasma-like animated banding with comic edges. | Magenta, orange, electric blue |

#### 07 - Lens Dot Bevel
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 07.01 | Soft Bevel | Soft Bevel | Dot-lens mosaic with soft bevel and subtle specular. | Neutral highlights, source hues |
| 07.02 | Hard Bevel | Hard Bevel | Sharper bevel profile and stronger shape contrast. | Bright highlights, deeper shadows |
| 07.03 | Specular Punch | Specular Punch | High specular punch for glossy bead-like look. | White hotspots, source hues |
| 07.04 | Toxic Candy Drift | Toxic Candy Drift | Fast camera-driven dot motion with slow toxic candy color drift. | Toxic green, cyan, candy magenta, pale glow |
| 07.05 | Warhol Drift | Warhol Drift | Pop-art palette transitions per dot with very slow crossfade. | Red, yellow, cyan, violet, lime, orange |
| 07.06 | Neon Flux Drift | Neon Flux Drift | Tri-neon loop with restrained hue travel over beveled dots. | Neon cyan, magenta, acid yellow |
| 07.07 | Thermal Drift | Thermal Drift | Heat-map style dot palette with deliberately slow temporal sweep. | Blue, cyan, yellow, red |
| 07.08 | Spectral Delta Bloom | Spectral Delta Bloom | Only dots with >50% temporal color change grow, proportionally to the measured RGB delta; expansion can read as square-ish bloom due to cell ownership. | Slow spectral rainbow + white-hot peaks |

#### 08 - Mirror Zoom Tiles
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 08.01 | Pulse | Pulse | Mirrored tile zoom pulse, balanced motion. | Source RGB, mirrored symmetry |
| 08.02 | Wide Pulse | Wide Pulse | Broader pulse and larger tile rhythm. | Source RGB, wider bands |
| 08.03 | Hyper Pulse | Hyper Pulse | Faster, denser tile pulse and stronger zoom energy. | Source RGB, high-motion streaks |

#### 09 - Chromatic Trails
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 09.01 | RGB Trail | RGB Trail | Multi-sample chromatic trail accumulation. | Red, green, blue |
| 09.02 | Neon Trail | Neon Trail | Neon remap variant with stronger synthetic vibe. | Neon green, cyan, pink |
| 09.03 | Thermal Trail | Thermal Trail | Trail output mapped to thermal pseudo-color. | Blue, yellow, red |

#### 10 - Vector Profile Scope
| Code | Name | Legacy Alias | Brief Description | Dominant Colors |
|---|---|---|---|---|
| 10.01 | Scope Mono | Scope Mono | Black background with white horizontal/vertical profile traces. | White, black |
| 10.02 | Camera Overlay | Camera Overlay | Camera-driven color sampled only on profile traces (no visible underlay). | Source RGB on black |
| 10.03 | Tint Overlay | Tint Overlay | Warm Shadertoy-like tint applied only to profile traces (no visible underlay). | Warm reds, source RGB on black |
| 10.04 | Thermal Overlay | Thermal Overlay | Thermal remap applied only to profile traces (no visible underlay). | Thermal blue/yellow/red on black |

### Rutt-Etra CRT

In 1973, [Bill Rutt and Steve Etra](https://en.wikipedia.org/wiki/Rutt/Etra_Video_Synthesizer) built an analog video synthesizer that deflected scan lines based on the luminance of the incoming signal. It cost as much as a car, weighed as much as a refrigerator, and produced visuals that looked like the world was made of oscilloscope traces.

This is the same thing. In GLSL. On a $40 computer. Running at 20 FPS.

Frame luminance warps the scan lines. CRT curvature bends the edges. Vignette darkens the corners. Noise adds grain. Your face becomes a vector field.

Every sub-mode now has a **secondary parameter on ↑/↓** — a second dimension of expression beyond wave intensity.

| Mode | Look | ↑/↓ does |
|---|---|---|
| Prism Warp | Subtle RGB split with camera bleed — the default | Chromatic split width: narrow to full blowout |
| Phosphor | P31 green phosphor tube | Tint sweep: cold cyan → classic green → warm amber |
| Wire Mono | Classic white scan lines on black | Displacement contrast: flat uniform → bright spikes only |
| v002 Terrain | Joy Division terrain with luminance mountains | Interference: independent lines → coupled wave peaks |

### ASCII Cam

Every camera pixel gets mapped to a glyph from an 8×8 bitmap font hardcoded inside the shader. Luminance picks the character. The whole thing runs on the GPU in real time, with no CPU involvement in the actual rendering. Dense modes run at double character density and mix letters with symbols (70/30 split, per-cell random).

| Mode | Look |
|---|---|
| Symbol Color | Density-scaled symbols, camera-accurate color |
| Symbol Mono | Same, luminance grayscale |
| Dense Mono Mix | 2× density, 70% letters + 30% symbols, monochrome |
| Dense Color Mix | 2× density, 70% letters + 30% symbols, camera color |

### Pixel Art

The camera downsampled to a grid of blocks, each rendered as a single pixel of a retro palette. The block size is tunable from near-native (4px) to aggressively chunky (48px). Cycling color mode applies a per-mode default block size first, then `←` / `→` still tweak live.

| Mode | Code | Look | Default size |
|---|---|---|---|
| Game Boy | 02.01 | DMG-01 four-shade green + authentic LCD pixel gap | 6px |
| Pixel Native | 02.02 | Pixelated camera, colors corrected | 4px |
| Toxic Candy | 02.03 | Neon candy palette — aggressively quantized, with rounded pixel corners | 8px |

### Raster Vision

Dedicated halftone/raster effect: thermal and comic looks rendered as variable-size dots with realistic halftone jitter and edge detection.
`←` / `→` controls raster cell size (bigger = fewer/larger dots, smaller = denser dots).

| Mode | Look |
|---|---|
| Thermal Raster | Blue-cold / red-hot raster dots |
| Thermal Inverted | Red-cold / blue-hot raster dots |
| Comic Ink Mono | Black-ink halftone + edge lines |
| Comic Pastel | Soft posterized pastel halftone |
| Vibrant Pop | Saturated comic-print style, saturation-boosted to prevent channel clipping |

### Digital Codec Corruption

Macroblocking, keyframe corruption, DC smear — looks like an H.264 stream having a stroke. Every block gets a baseline aggressive jitter; "corrupted" blocks get the full treatment: wrong-macroblock jump + horizontal smear. No pixel in the frame is clean.

| Mode | Look |
|---|---|
| RGB Mosh | Chromatic smear on corrupted blocks |
| Thermal Glitch | Heat map on corrupted, cool blue on mild blocks |
| Acid Trip | Hue rotation → neon blast on corruption |
| Void Codec | Corrupted = black void, only edges survive |

`←` / `→` controls corruption intensity (amount 0.5–6.0).

### VHS Tracking Burn

Analog tape chaos: chroma bleed, Y/C separation, scanline jitter, head-switching artifact in the bottom 12%, luma noise. Two distinct vibes.

| Mode | Look |
|---|---|
| Signal Melt | Massive RGB split — R, G, B sampled from 3× separate horizontal offsets |
| Night Tape | Green phosphor security cam — heavy grain, interference bands, line dropouts |

`←` / `→` controls tracking intensity (0.5–5.0).

### Posterize Glitch Comic

Hard luminance quantization + edge ink detection + random horizontal band glitch. Instant printed-comic meltdown, four very different color treatments.

| Mode | Look |
|---|---|
| Warhol Pop | Per-level bold pop palette: red / yellow / cyan / violet / lime / orange |
| Neon Cel | Dark bg, neon cyan/magenta/yellow ink on edges per quantize level |
| Acid Bloom | Animated HSV hue per level — slowly cycling rainbow posterization |
| Plasma Burn | Multi-sine animated plasma tinted per level — full chromatic delirium |

`←` / `→` controls quantization levels (2–12).

### Lens Dot Bevel

Disc mosaic with beveled shading and specular highlights, sampled from the live camera.

| Mode | Look |
|---|---|
| Soft Bevel | Gentle bevel and lower specular |
| Hard Bevel | Sharper bevel profile |
| Specular Punch | Strong highlight and crisp bead look |
| Toxic Candy Drift | Toxic candy palette drift, color cycle intentionally slow |
| Warhol Drift | Warhol palette swap with very slow crossfade |
| Neon Flux Drift | Neon triad drift with slow hue transition |
| Thermal Drift | Thermal palette sweep at restrained speed |
| Spectral Delta Bloom | Dots expand only where temporal color change exceeds 50%, proportional growth with grid-bloom character |

`←` / `→` controls detail (0.20–14.0): far left can reach roughly 6 dots across the screen, far right can produce very dense dot grids.

Implementation note (07.08): temporal growth uses current frame vs previous frame (`iChannel0` vs `iChannel1`) with threshold fixed at 50%. At high deltas, dots can look square-ish because each fragment still belongs to a fixed dot cell.

### Mirror Zoom Tiles

Tiled mirror zoom with pulsating scale and mode-dependent tile size.

| Mode | Look |
|---|---|
| Pulse | Balanced zoom pulse |
| Wide Pulse | Wider, smoother pulse |
| Hyper Pulse | Stronger pulse and denser tiling |

`←` / `→` controls zoom amount (0.2–1.6).

### Chromatic Trails

Temporal-looking chromatic accumulation with scanline-style trail stacking.

| Mode | Look |
|---|---|
| RGB Trail | Classic multicolor trail |
| Neon Trail | G/B/R remap with stronger neon feel |
| Thermal Trail | Trail remapped to thermal palette |

`←` / `→` controls trail intensity (0.5–2.4).

### Vector Profile Scope

Variant inspired by Shadertoy profile-scope visuals: a quantized sampling grid builds horizontal and vertical luminance traces from the live camera stream.

| Mode | Look |
|---|---|
| Scope Mono | Black background, white traces only |
| Camera Overlay | Camera-colored traces only on black |
| Tint Overlay | Warm-tinted traces only on black |
| Thermal Overlay | Thermal-colored traces only on black |

`←` / `→` controls scope grid density (0.8–3.4).

---

## How it works

```
Pi Camera (BGR888, 1640x1232)
    │
    │  Picamera2 + libcamera
    ▼
capture thread ──(threading.Lock)──▶ latest frame
    │                                      │
    │  motion detection (1/8 res)    C render loop (kms-glsl)
    │  uMotionLevel, uPresence*             │
    │                                Python render callback
    │                                      │
    └──────────────────────────────▶ glTexSubImage2D + uniforms
                                           │
                                    GLSL fragment shader
                                           │
                                    DRM/KMS output (fullscreen)
```

**Capture**: a daemon thread runs continuously, keeps the latest frame behind a lock, and computes motion/presence data at 1/8 resolution on the side — negligible CPU cost.

**Render**: `kms-glsl`'s C loop fires a Python callback every frame. The callback uploads the texture and pushes all uniforms to the GPU.

**Shader**: all visual logic lives in `rutt_etra.frag`. One fragment shader, eleven visual systems, routed by `uEffectMode`.

**Keyboard**: a separate thread reads `/dev/tty` in raw mode (`ICANON`, `ECHO`, `ISIG` all disabled). Ctrl+C arrives as `\x03` bytes and triggers graceful shutdown. `SIGTERM` and `SIGHUP` are also handled — kill from SSH works cleanly.

**stdin**: replaced with a silent pipe at startup so `kms-glsl`'s C code doesn't mistake terminal activity for user input. The write end doubles as the shutdown signal mechanism.

---

## Requirements

- Raspberry Pi with camera support enabled
- `python3`, `libcamera`, `picamera2`, `numpy`
- [`kms-glsl`](https://github.com/keithzg/kms-glsl) in one of:
  - `KMS_GLSL_DIR` environment variable
  - `../kms-glsl` sibling directory (recommended)
  - `~/kms-glsl`

Recommended layout on the Pi:
```
~/kms-glsl/       ← external dependency
~/retinacannon/   ← this repo
```

Detection looks for `glsl.so` inside the candidate directory. If not found, the launcher prints `[FATAL]` and exits.

---

## Run

```bash
./start_cannon.sh
```

Specific shader:
```bash
./run_rutt.sh     # Rutt-Etra (default)
./run_base.sh     # raw camera passthrough
```

Non-standard `kms-glsl` location:
```bash
KMS_GLSL_DIR=/path/to/kms-glsl ./start_cannon.sh
```

Kill cleanly from SSH (when DRM has taken over the local terminal):
```bash
kill -SIGINT $(pgrep -f retina_cannon.py)
```

---

## Controls

| Key | Action |
|---|---|
| `Space` | Cycle effect: Rutt-Etra → ASCII Cam → Pixel Art → Raster Vision → Digital Codec Corruption → VHS Tracking Burn → Posterize Glitch Comic → Lens Dot Bevel → Mirror Zoom Tiles → Chromatic Trails → Vector Profile Scope |
| `S` | 3-second countdown then save rendered screenshot to `shots/` |
| `PgUp` / `PgDn` | Cycle color mode (per-effect, independent) |
| `↑` / `↓` | Per-effect secondary tweak — Rutt: sub-mode parameter (split / tint / contrast / interference); other effects: not yet assigned |
| `←` / `→` | Primary parameter — Rutt: wave · ASCII: density · Pixel: block size · Raster: dot size · Codec: amount · VHS: tracking · Poster: levels · Dot: detail · Mirror: zoom · Trail: intensity · Scope: grid |
| `V` | Cycle view: 16:9 → 4:3 → Fisheye |
| `M` | Toggle horizontal mirror of current view |
| `F` | Toggle FPS logging to terminal |
| `Ctrl+C` | Clean shutdown |

Runtime status now prints explicit IDs (for example `EFFECT 02`, `COLOR 02.02/03`) so scene ordering stays unambiguous during tuning, cleanup, and screenshot selection.

Arrow keys handle both `ESC [` and `ESC O` prefixes. Because terminal emulators are ungoverned.

### Screenshot Mode (`S`)

Press `S`, get a dramatic 3-second terminal countdown, then a frame dump of whatever glorious visual chaos is on screen.

Files are saved to `shots/` as:
`YYYYMMDD_HHMMSS_<EE-effect-name>_<EE-MM-variant-name>_<view>_mirror-(on|off).png`

So yes, your shader experiments are timestamped evidence now. Very professional.

---

## Startup / Shutdown

On boot, the terminal runs a 3-phase animated sequence before the renderer takes over:

1. **Matrix rain reveal** — columns of B/W block characters (`█▓▒░·`) cascade down the full screen height. As each column's trail passes a row, that row's content materializes in gray. Trail fades from bright white to dark gray with no color — pure monochrome rain.
2. **Colorize** — once all drops have finished, rows light up in full color in random order over ~0.6s, scattering across the screen like a static discharge: lolcat rainbow on the figlet title, electric cyan on the NFO box borders, white on the metadata.
3. **Countdown** — `LAUNCHING IN N ████░░` progress bar runs below the revealed content.
4. **Matrix cover** — a faster reverse sweep erases everything back to black before DRM takes the display. The camera feed appears in fullscreen.

The NFO/cracktro status box shows: hostname, SoC temperature, RAM, uptime, shader, active effect. The boot quote is rendered as `>>  quote  <<` (dim brackets, bright text — pure ASCII, Pi framebuffer safe).

On shutdown: clean session stats (duration, estimated frames, average FPS) plus a randomly chosen send-off line.

---

## Defaults

| Parameter | Value |
|---|---|
| View mode | 16:9 |
| Mirror | ON (because the camera should stop gaslighting you) |
| Effect | Rutt-Etra CRT |
| Rutt color | 00.01 Prism Warp |
| ASCII color | 01.01 Symbol Color |
| Pixel Art color | 02.01 Game Boy |
| Raster Vision color | 03.01 Thermal Raster |
| Codec color | 04.01 RGB Mosh |
| VHS color | 05.01 Signal Melt |
| Poster color | 06.01 Warhol Pop |
| Lens Dot color | 07.01 Soft Bevel |
| Mirror Zoom color | 08.01 Pulse |
| Chromatic Trails color | 09.01 RGB Trail |
| Vector Profile Scope color | 10.01 Scope Mono |
| Rutt wave | 0.40 (range 0.05–3.80, extended left) |
| ASCII density | 3.00 |
| Pixel block size | 6px (Game Boy default) |
| Raster dot size | 12px |
| Codec amount | 2.0 |
| VHS tracking | 1.5 |
| Poster levels | 4 |
| Lens Dot detail | 2.6 |
| Mirror Zoom amount | 0.80 |
| Chromatic Trails intensity | 1.20 |
| Vector Profile Scope grid | 2.20 |
| FPS baseline | ~20 FPS |

---

## Notes for developers

**`c_float()` is not optional.** Float uniforms via ctypes must be explicitly wrapped or the GPU gets garbage.

**The GIL is load-bearing.** Globals like `current_rutt_wave` are written by the keyboard thread and read by the render callback with no explicit locking. CPython's GIL makes these reads atomically safe. Port to free-threaded Python and add locks.

**Never use SIGKILL to stop the process.** SIGTERM and SIGHUP are handled gracefully (same shutdown path as Ctrl+C), but a SIGKILL will leave DRM in an exclusive state that may survive a soft reboot and require a hard power cycle.

**Blue-skin in new raster effects** usually means brightness boosting is clipping the red channel. Use saturation boost (`mix(gray, raw, factor)`) instead.

**Testing without Pi hardware** will fail immediately. `Picamera2` won't import, EGL won't initialize, `kms-glsl` will complain. This is correct.

Syntax checks that work anywhere:
```bash
python3 -m py_compile retina_cannon.py
bash -n start_cannon.sh
```

---

## License

MIT - [Netmilk Studio sagl](https://netmilk.studio)

Do what you want with it. Attribution appreciated. Don't blame us if it runs at an art show and someone asks you to explain what a fragment shader is.
