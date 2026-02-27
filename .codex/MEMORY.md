# MEMORY - Retina Cannon

## Core directives
- Never store plaintext secrets in versioned files, logs, output, or commit messages.
- Keep project-facing text in English (docs, comments, review notes, commit messages).
- Session start: read this file plus the last 2 entries in `SESSION_LOG.md`.
- Keep changes minimal, verifiable, and aligned with project goals.
- Do not change application logic without an explicit request.

## Working preferences
- Start with quick inspection: structure, security, git status.
- Run at least one concrete verification before closing (run/build/lint/grep).
- Keep patches small and single-purpose.

## Consolidated technical decisions
- Main repository: `/home/enuzzo/retinacannon` (this root).
- External dependency: `~/kms-glsl/` — detected by presence of `glsl.so` (NOT a `lib/` directory; `lib` is `lib.py`).
- Main run command: `/home/enuzzo/retinacannon/start_cannon.sh`.
- Stable runtime baseline: ~20 FPS on RPi4 with the canonical launcher.
- Runtime stack: `retina_cannon.py` + `rutt_etra.frag` (GLSL) + kms-glsl ctypes bridge.
- Active shader: `rutt_etra.frag` — four effects via `uEffectMode` uniform:
  - 0: Rutt-Etra CRT (scan-line displacement, CRT curvature, vignette)
  - 1: ASCII Cam (bitmap font glyphs, 4 color modes)
  - 2: Pixel Art (block grid, 6 palette modes: Full Color/Game Boy/CGA/Phosphor/Amber/Infrared)
  - 3: Signal Ghost (generative typography, motion/presence reactive, 6 color modes)
- Camera format: BGR888 at 1640×1232; uploaded as GL_RGB; shader uses `.bgr` swizzle.
- Motion detection: CPU-side in capture thread at 1/8 resolution; dead-zone 0.03, multiplier 30.0, asymmetric smoothing (attack 0.65, decay 0.92). Exposes `uMotionLevel`, `uPresenceScale`, `uPresenceCX/CY`.
- Keyboard thread: uses `select()` with 0.5s timeout (not blocking `os.read()`) because DRM takes TTY into graphics mode.
- ISIG disabled on TTY: Ctrl+C arrives as `\x03` byte; SIGTERM/SIGHUP routed to same graceful shutdown.
- SIGKILL forbidden: leaves DRM master locked, display state survives soft reboot (hard power cycle required).
- Safe kill from SSH: `kill -SIGINT $(pgrep -f retina_cannon.py)`
- stdin replaced with idle pipe (fd 0): prevents kms-glsl C code from interpreting stdin activity as interruption.
- Float uniforms via ctypes must use `c_float()` wrapper.
- Arrow keys: parser handles both `ESC [` and `ESC O` prefixes.

## Security and secrets
- Rule: secrets live only in ignored local files (`config.local.h`, `.env.local`, etc.).
- Any versioned templates must stay clean (`config.example.h`, `.env.example`).
- `.codex/*` must not include credentials; use placeholders like `<WIFI_PASSWORD>`.

## Recurring gotchas
- kms-glsl detection: check for `glsl.so` FILE, not `lib/` directory (lib is `lib.py`). (verified)
- Arrow keys may emit either `ESC [` or `ESC O`; keyboard parser must support both. (verified)
- DRM/KMS exclusive mode: never SIGKILL the process; display lock survives soft reboot. (verified by hard power cycle incident)
- When adding new effect modes: update `EFFECT_MODE_NAMES`, `_active_color_mode()`, `_set_active_color_mode()`, `_effect_param_label()`, `on_init`, `on_render`, keyboard handler, and `mainImage()` in shader.

## Pre-flight checklist
- [ ] Read `MEMORY.md`.
- [ ] Read the last 2 entries in `SESSION_LOG.md`.
- [ ] Check `git status`.
- [ ] Run a targeted secret scan.
- [ ] Test at least one real command before commit.
- [ ] Append an end-of-session log entry.
