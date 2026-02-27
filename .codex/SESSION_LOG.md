# SESSION_LOG (append-only)

## Rules
- Only append new entries at the end.
- No plaintext secrets; use placeholders.

---

## Template entry
### [YYYY-MM-DD HH:MM] Session
- Goal:
- Actions taken:
- Errors encountered:
- Fix:
- Concrete verification:
- Prevention:

---

### [2026-02-27 08:55] Bootstrap Retina Cannon root repo
- Goal: create the root local repo and operational memory in `.codex/`.
- Actions taken: created `.gitignore`, `README.md`, `.codex/*`; set ignored-local-secrets policy.
- Errors encountered: none blocking in this phase.
- Fix: n/a.
- Concrete verification: root had no `.git`; prepared for `git init` and initial commit.
- Prevention: always use `/home/enuzzo/retinacannon` as the primary repository root.

### [2026-02-27 08:58] Root-coherence cleanup across nested repo
- Goal: ensure all governance files live in `retinacannon` root and remove nested duplication.
- Actions taken: confirmed `.codex` exists only at root; removed nested `.codex` from `glslViewer`; restored nested `.gitignore` to upstream-equivalent content.
- Errors encountered: none.
- Fix: n/a.
- Concrete verification: `find` returns only `/home/enuzzo/retinacannon/.codex`; root git status is clean.
- Prevention: treat `glslViewer/` as external nested repo and keep project governance only at root.

### [2026-02-27 09:01] Coherence audit before start
- Goal: run a full coherence audit on folders, structure, and security in `retinacannon`.
- Actions taken: checked root and nested git status; validated folder layout and `.codex` placement; scanned for secret patterns; verified ignore rules with `check-ignore`; validated shell/python entrypoint syntax.
- Errors encountered: runtime smoke test failed on this shell with `GLFW error 0x1000e: Failed to detect any supported platform`.
- Fix: no code change applied; issue is environment/display availability, not repo consistency.
- Concrete verification: root repo is clean; no tracked local-secret files; `.codex` only in root; ignore rules are active.
- Prevention: run startup checks from a display-enabled session before runtime validation sign-off.

### [2026-02-27 09:06] Runtime path alignment to kms-glsl launcher
- Goal: restore working startup behavior used in previous sessions.
- Actions taken: updated `start_cannon.sh` to run `retina_cannon.py` through `kms-glsl` (`cd /home/enuzzo/kms-glsl`, `PYTHONPATH=/home/enuzzo/kms-glsl`).
- Errors encountered: none after alignment.
- Fix: replaced old `/usr/local/bin/glslViewer` launcher path with the known working `kms-glsl` Python flow.
- Concrete verification: startup succeeds and renders at ~20 FPS (`19.997686` and `19.999998` observed in timed run).
- Prevention: keep `start_cannon.sh` as canonical launcher and validate FPS via timed startup when troubleshooting.

### [2026-02-27 09:08] English-comments normalization on scripts
- Goal: keep script/Python comments and project-facing text consistently in English.
- Actions taken: scanned root `*.py`/`*.sh` files and translated non-English comments in `retina_cannon.py`; normalized color-mode labels to English.
- Errors encountered: none.
- Fix: updated only comments and user-facing labels; no runtime logic changes.
- Concrete verification: no Italian keywords found in root script comments; `python3 -m py_compile retina_cannon.py` passes.
- Prevention: include language check in future script reviews before commit.

### [2026-02-27 09:09] Runtime monitor report before next step
- Goal: run a final live check and capture FPS stability before planning the next phase.
- Actions taken: executed `start_cannon.sh` in timed live runs (10s and 16s) and monitored render logs.
- Errors encountered: none during these runs.
- Fix: n/a.
- Concrete verification:
  - Run A FPS samples: `20.000229`, `19.918130`, `19.945667`.
  - Run B FPS samples: `20.000256`, `20.000229`, `20.000152`, `20.000178`, `19.999970`, `20.000144`.
  - Consolidated FPS summary: min `19.918130`, max `20.000256`, average `19.984995`.
  - Camera + EGL + OpenGL ES initialization completed successfully in both runs.
- Prevention: when performance drifts, run a timed live check and compare against the ~20 FPS baseline.

### [2026-02-27 09:33] Keyboard mapping for distortion and color modes
- Goal: add interactive controls for distortion and color mode cycling.
- Actions taken: added shader uniform `uDistortion`; wired Python controls for Arrow Left/Right (distortion step `0.05`, range `0.10..3.00`) and kept Arrow Up/Down for color modes.
- Errors encountered: initial `ctypes` binding error on `glUniform1f` argument conversion.
- Fix: pass `c_float(current_distortion)` to `glUniform1f`.
- Concrete verification:
  - Distortion key test: `[DISTORTION] 1.05x` observed after Arrow Right.
  - Color key test: `[COLOR] Green phosphor` then `[COLOR] White` observed after Arrow Up/Down.
  - Rendering remained stable around ~20 FPS during interactive tests.
- Prevention: when adding new float uniforms through ctypes, always wrap scalar values with matching ctypes types.

### [2026-02-27 09:37] Keyboard feedback reliability fix
- Goal: fix missing arrow-key feedback on some terminals/keyboards.
- Actions taken: updated keyboard parser to accept both ANSI arrow prefixes (`ESC [` and `ESC O`).
- Errors encountered: none after parser update.
- Fix: changed condition from `ch2 == '['` to `ch2 in ('[', 'O')`.
- Concrete verification:
  - `ESC O` sequence test produced `[DISTORTION]` and `[COLOR]` feedback.
  - `ESC [` sequence test also produced `[DISTORTION]` feedback.
- Prevention: keep multi-prefix handling for terminal control sequences in interactive input code.

---

### [2026-02-27] Full session — kms-glsl fix, shutdown safety, 2 new effects, Signal Ghost redesign, docs

**Goal:** fix kms-glsl path detection regression, add robustness, add Pixel Art + Signal Ghost effects, update all documentation.

**Actions taken:**

1. **Git sync** — pulled 7 upstream commits (fast-forward, no conflicts).

2. **kms-glsl detection fix** — upstream commit introduced `[ -d "$_d/lib" ]` check; `lib` is `lib.py` (a file, not a directory). Fixed in `retina_cannon.py`, `start_cannon.sh`, `run_rutt.sh`, `run_base.sh` to check for `glsl.so` file presence instead.

3. **SIGTERM/SIGHUP handlers** — added `_handle_signal()` routing to `_request_renderer_stop()`; registered for both signals.

4. **Non-blocking keyboard thread** — replaced blocking `os.read(fd, 1)` with `select.select([fd], [], [], 0.5)` timeout loop; prevents hanging when DRM takes TTY into graphics mode.

5. **Nerd startup/shutdown banners** — `_print_startup_banner()`: scan-line logo, system stats box (hostname, SoC temp, RAM, uptime), random nerd quote, controls summary. `_print_shutdown_banner()`: clean logo + session stats (duration, total frames, avg FPS).

6. **Pixel Art effect (mode 2)** — block grid pixelation with 6 radically different palettes: Full Color, Game Boy DMG-01 (LCD gap effect), CGA mode 4, Phosphor P1, Amber P3, Infrared FLIR jet. Left/Right controls block size (4–48px, step 2).

7. **Signal Ghost effect (mode 3)** — interactive generative typography. Motion detection CPU-side in capture thread (1/8 resolution, dead-zone 0.03, multiplier 30.0, asymmetric smoothing). Letters change size/rate/wobble reactively. 6 color modes: Void/Matrix/Ghost Cam/Neon/Thermal/Chromatic.

8. **Signal Ghost redesign** — first version had letters always huge (scale 0.6–1.05) and no visible motion reaction. Redesigned: baseline scale 0.07–0.11 (breathe), per-cell staggered burst, motionBoost × proximity for centroid amplification.

9. **Default view fix** — `current_view_mode = 0` (16:9) instead of 2 (Fisheye).

10. **Shutdown banner cleanup** — removed corruption/glitch effect on exit logo, restored clean `_print_retina_logo(offset=3)`.

11. **Documentation** — rewrote `README.md` (all 4 effects, motion detection, shutdown safety, defaults table), rewrote `CLAUDE.md` (full uniforms table, all 4 effects, design decisions, effect mode checklist). Updated `.codex/MEMORY.md` and `.codex/SESSION_LOG.md`.

**Errors encountered:**
- kms-glsl not found `[FATAL]`: upstream broke path detection (lib/ vs lib.py). Fixed.
- System freeze requiring hard power cycle: test `./start_cannon.sh & kill %1` sent SIGTERM → DRM master leaked → display locked across soft reboot. Fixed: SIGTERM/SIGHUP handlers added.
- Signal Ghost letters always huge: scale formula included presence×0.55 + cellLuma×0.35 making baseline 0.6–1.05. Redesigned to 0.07–0.11 baseline.
- Signal Ghost no motion reaction: multiplier 14.0 didn't clear sensor noise; no dead-zone. Fixed: dead-zone 0.03, multiplier 30.0, asymmetric smoothing.

**Concrete verification:**
- `python3 -m py_compile retina_cannon.py` — passes.
- `bash -n start_cannon.sh` — passes.
- Live test: startup banner, ~20 FPS, all keyboard controls, graceful Ctrl+C shutdown confirmed by user.

**Prevention:**
- kms-glsl: always check for `glsl.so` file, not directory structure.
- DRM: never SIGKILL; never test with background kill without SIGINT.
- New effect modes: follow the 8-location checklist in CLAUDE.md.
