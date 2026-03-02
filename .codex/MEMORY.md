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
- Active shader: `rutt_etra.frag` — ten effects via `uEffectMode` uniform:
  - 0: Rutt-Etra CRT
  - 1: ASCII Cam
  - 2: Pixel Art
  - 3: Raster Vision
  - 4: Digital Codec Corruption
  - 5: VHS Tracking Burn
  - 6: Posterize Glitch Comic
  - 7: Lens Dot Bevel
  - 8: Mirror Zoom Tiles
  - 9: Chromatic Trails
- Boot/exit splash: VHS-style centered ASCII title with local figlet font `fonts/Slant Relief.flf`, optional `lolcat` colorization, random startup/shutdown lines, and configurable countdown via `--splash` (`-1` = hold until keypress).
- Figlet wrap guard: always render title with `figlet -w 1000` to avoid internal 80-column word splitting.
- lolcat path fallback: use `/usr/games/lolcat` if not present in regular `PATH`.
- Startup defaults: `view=16:9`, `mirror=ON`, `effect=Rutt-Etra CRT`, `pixel mode=Game Boy`, `raster mode=Thermal Raster`.
- Screenshot feature (`S`): 3-second countdown then frame dump to `shots/` with filename suffixes for effect/variant/view/mirror.
- Camera format: BGR888 at 1640x1232; uploaded as GL_RGB.
- Color baseline rule: when creating new effects, sample camera with `.rgb` first and compare skin tone against Rutt default. Use `.bgr` only intentionally per-effect; blind `.bgr` in new effects caused blue-skin regressions.
- Motion detection: CPU-side in capture thread at 1/8 resolution; dead-zone 0.03, multiplier 30.0, asymmetric smoothing (attack 0.65, decay 0.92). Exposes `uMotionLevel`, `uPresenceScale`, `uPresenceCX/CY`.
- Keyboard thread: uses `select()` with 0.5s timeout (not blocking `os.read()`) because DRM takes TTY into graphics mode.
- ISIG disabled on TTY: Ctrl+C arrives as `\x03` byte; SIGTERM/SIGHUP routed to same graceful shutdown.
- SIGKILL forbidden: leaves DRM master locked, display state survives soft reboot (hard power cycle required).
- Safe kill from SSH: `kill -SIGINT $(pgrep -f retina_cannon.py)`.
- stdin replaced with idle pipe (fd 0): prevents kms-glsl C code from interpreting stdin activity as interruption.
- Float uniforms via ctypes must use `c_float()` wrapper.
- Arrow keys: parser handles both `ESC [` and `ESC O` prefixes.
- Lens Dot (`uEffectMode=7`) now has 8 color modes:
  - Existing base modes (must remain behavior-compatible): Soft Bevel, Hard Bevel, Specular Punch
  - Added drift modes: Toxic Candy Drift, Warhol Drift, Neon Flux Drift, Thermal Drift
  - Added temporal mode: Spectral Delta Bloom
- Lens Dot detail control range: `0.20..14.0` (step `0.25`):
  - left side supports very large dots (about 6 dots across at minimum)
  - right side supports very dense dot grids
- Spectral Delta Bloom uses temporal comparison between current and previous camera frames:
  - `iChannel0` = current frame, `iChannel1` = previous/lagged frame
  - growth threshold fixed at 50% color-change delta
  - above threshold, growth is proportional to extra delta
  - known current visual behavior: expansion can appear square-ish because dot ownership remains cell-based.

## Security and secrets
- Rule: secrets live only in ignored local files (`config.local.h`, `.env.local`, etc.).
- Any versioned templates must stay clean (`config.example.h`, `.env.example`).
- `.codex/*` must not include credentials; use placeholders like `<WIFI_PASSWORD>`.

## Recurring gotchas
- kms-glsl detection: check for `glsl.so` FILE, not `lib/` directory (lib is `lib.py`). (verified)
- Arrow keys may emit either `ESC [` or `ESC O`; keyboard parser must support both. (verified)
- DRM/KMS exclusive mode: never SIGKILL the process; display lock survives soft reboot. (verified by hard power cycle incident)
- Screenshot capture in callback timing: force a one-off draw before `glReadPixels` or dumps can be black.
- When adding new effect modes: update `EFFECT_MODE_NAMES`, `_active_color_mode()`, `_set_active_color_mode()`, `_effect_param_label()`, `on_init`, `on_render`, keyboard handler, and `mainImage()` in shader.
- Blue-skin regression trap: channel-order mismatches (`rgb` vs `bgr`) can affect only some effects while Rutt looks correct. Troubleshoot by comparing the problematic effect against Rutt in the same session and standardize sampling in the new effect path.
- Lens Dot 07.08 caveat: temporal growth is intentionally aggressive for visibility; apparent square blooms are expected with the current cell-based partitioning.

## Totry shortlist (2026-03-01)
- Exclude by dependency mismatch (extra channels/multipass/Shadertoy keyboard): `3.txt`, `4.txt`, `5.txt`, `6.txt`, `7.txt`, `9.txt`.
- Exclude by likely FPS collapse on RPi with no direct fallback plan: `10.txt`.
- Remaining practical candidates: `1.txt`, `2.txt`, `8.txt`.
- Priority order for trials: `2.txt` (strong visual payoff), `1.txt` (easy win), `8.txt` (only with perf guardrails).

## Pre-flight checklist
- [ ] Read `MEMORY.md`.
- [ ] Read the last 2 entries in `SESSION_LOG.md`.
- [ ] Check `git status`.
- [ ] Run a targeted secret scan.
- [ ] Test at least one real command before commit.
- [ ] Append an end-of-session log entry.
