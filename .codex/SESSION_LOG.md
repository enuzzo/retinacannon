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

### [2026-02-28 17:40] Screenshot docs refresh + knowledge sync
- Goal: document the `S` screenshot feature clearly in README with project tone, and sync knowledge files to current runtime behavior.
- Actions taken: updated `README.md` controls/defaults with a dedicated `Screenshot Mode (S)` section (countdown, naming pattern, `shots/` destination); refreshed `.codex/MEMORY.md` technical decisions to reflect 5 effects (including Raster Vision), mirror default ON, and screenshot capture behavior; appended this session entry.
- Errors encountered: none.
- Fix: n/a.
- Concrete verification: reviewed resulting docs via `sed`; values now match code constants in `retina_cannon.py` (`EFFECT_MODE_NAMES`, `RASTER_COLOR_MODE_NAMES`, `current_mirror_view = 1`, screenshot save path `RETINA_DIR / 'shots'`).
- Prevention: when controls/effects change, update `README.md`, `MEMORY.md`, and append `SESSION_LOG.md` in the same session before commit.

### [2026-02-28 19:27] README TL;DR iteration + remote sync
- Goal: add a punchy TL;DR section in README, then align local with upstream edits.
- Actions taken: inserted TL;DR between `Why this exists` and `Effects`; adjusted copy to English; replaced TL;DR with user-provided final text; pushed commits (`f056b84`, `46a42c9`); pulled latest upstream changes to local (`1f14375`).
- Errors encountered: transient sandbox restrictions on some git read commands.
- Fix: retried blocked commands with approved elevated execution where needed.
- Concrete verification: `git push` succeeded to `origin/main`; subsequent `git pull` fast-forwarded local `main` to `1f14375`; current status is clean (`## main...origin/main`).
- Prevention: for doc-copy iterations, update README first, then push immediately and run pull after any remote-side edits.

### [2026-02-28 21:19] Splash redesign stabilization + Pixel palette cleanup
- Goal: finalize VHS/warez splash UX and remove the unwanted blue-skin Pixel preset while keeping runtime controls practical.
- Actions taken: added local figlet font support (`fonts/Slant Relief.flf`) and updated splash to use centered title render with `figlet -w 1000`; added lolcat integration with `/usr/games/lolcat` fallback; introduced `--splash` argument (default 10, `-1` hold-until-key); added 20 startup + 20 shutdown random lines; tuned splash layout spacing and quote rendering; replaced Pixel palettes (removed legacy phosphor/amber and then removed CGA on request), keeping Full Color + Game Boy + CMYK Melt + Toxic Candy with per-mode default block sizes; simplified countdown to a progressive grayscale 10→0 line.
- Errors encountered: figlet title was being internally wrapped at default width and appearing split; splash redraw loop caused visible flashing; lolcat path was not always resolved through PATH.
- Fix: forced figlet width to 1000, switched countdown rendering to stable line updates, and added explicit `/usr/games/lolcat` fallback.
- Concrete verification: `python3 -m py_compile retina_cannon.py` passes after each splash/countdown iteration; `grep` checks confirmed removal of `CGA` references from README + shader + Python mode names.
- Prevention: keep splash rendering single-frame stable where possible, force figlet width explicitly, and test terminal utility paths (`command -v` plus known distro fallback locations) before assuming monochrome fallback behavior.

### [2026-02-28 23:19] Targeted color-order troubleshooting on new effects
- Goal: remove persistent blue-skin tint from newly added effects while preserving the known-correct baseline rendering.
- Actions taken: compared sampling strategy in `renderRutt()` (predominantly `.rgb`) versus the 3 new effects; identified mixed `.bgr` usage in new paths; switched new effect sampling to `.rgb` and removed aggressive default channel-split from those paths.
- Errors encountered: visual mismatch was not global (Rutt looked correct), making the issue appear effect-specific and inconsistent.
- Fix: standardized channel sampling for new effects to `.rgb` and documented explicit RGB/BGR rules in `MEMORY.md`.
- Concrete verification: user confirmed normal skin tones after the RGB alignment fix; Python syntax check remained clean (`python3 -m py_compile retina_cannon.py`).
- Prevention: for any new effect, first validate “neutral camera pass” against Rutt default before adding stylized channel operations; treat `.bgr` as opt-in, not default.

### [2026-03-01 02:47] Quick feasibility sweep of `/totry` shader candidates
- Goal: review all files in root `totry/` and estimate feasibility/difficulty for integration into current Retina Cannon pipeline.
- Actions taken: enumerated `totry/*.txt` (11 files), inspected each snippet and extracted technical dependencies (`iChannel*`, buffer passes, `iMouse`, Shadertoy keyboard texture). Cross-checked against current runtime constraints (`retina_cannon.py` + `rutt_etra.frag`): single-pass shader path, live camera on `iChannel0`, no active multi-buffer pipeline, no Shadertoy `iChannel3` keyboard map.
- Errors encountered: none.
- Fix: n/a (analysis-only pass).
- Concrete verification:
  - `totry` content discovered at root with files `1.txt`..`11.txt`.
  - Quick matrix:
    - `1.txt`: feasibility high, difficulty low (single-pass, `iChannel0` only).
    - `2.txt`: feasibility high, difficulty medium-low (single-pass halftone; replace `iMouse` with internal controls).
    - `3.txt`: feasibility medium, difficulty high (large tutorial shader; depends on font atlas + `iChannel1` video path and heavy refit).
    - `4.txt`: feasibility low/medium, difficulty very high (explicit Buffer A + image pass, requires ping-pong multipass).
    - `5.txt`: feasibility medium, difficulty high (depends on `iChannel1` plus Shadertoy keyboard `iChannel3` via `texelFetch`).
    - `6.txt`: feasibility medium, difficulty medium/high (dual-channel composition + external glitch texture assumptions).
    - `7.txt`: same shader core as `6.txt` (without prose lines), same estimate.
    - `8.txt`: feasibility medium/high, difficulty medium (single-pass but performance-sensitive loop on RPi).
    - `9.txt`: feasibility medium, difficulty medium (needs shift map channel or procedural substitute for `iChannel1`).
    - `10.txt`: feasibility medium, difficulty high (raymarch + optional shadow loops, strong FPS risk on target hardware).
    - `11.txt`: notes/spec list, not executable shader code.
- Prevention: before importing future Shadertoy snippets, classify upfront as `single-pass / multi-pass / multi-channel` to avoid underestimating integration cost.

### [2026-03-01 02:54] Totry shortlist frozen in memory
- Goal: capture a practical trial shortlist after excluding dependency-heavy and no-fallback FPS-risk candidates.
- Actions taken: wrote `Totry shortlist (2026-03-01)` section in `MEMORY.md` with explicit exclusions and remaining files.
- Errors encountered: none.
- Fix: n/a.
- Concrete verification: shortlist recorded as `1.txt`, `2.txt`, `8.txt`; exclusions recorded as `3.txt`, `4.txt`, `5.txt`, `6.txt`, `7.txt`, `9.txt`, `10.txt`.
- Prevention: when new snippets arrive, update shortlist first, then start implementation only from listed candidates.

### [2026-03-02 18:52] Lens Dot expansion pass + temporal delta mode tuning
- Goal: extend Lens Dot size control range significantly, add temporal growth mode driven by color-change threshold, then document behavior in README and Codex knowledge.
- Actions taken:
  - Extended Lens Dot detail range in Python controls to `0.20..14.0` (`step 0.25`), keeping the same left/right key flow.
  - Added `07.08 Spectral Delta Bloom` to Lens Dot color modes.
  - Added previous-frame shader input (`iChannel1`) by allocating and updating a second GL texture in `on_init`/`on_render`.
  - Implemented temporal delta growth in `rutt_etra.frag` for `uColorMode==7`:
    - growth activates only above 50% delta threshold,
    - growth amount scales with excess delta,
    - delta computed over center + 4 neighboring samples per dot for stronger motion pickup.
  - Added short previous-frame lag (3-frame update cadence) for clearer temporal response during camera movement.
  - Updated README Lens Dot catalog and notes with the new mode, extended range, and implementation caveat.
  - Updated `.codex/MEMORY.md` with current Lens Dot operational behavior and caveats.
- Errors encountered:
  - Initial temporal scaling was too subtle in live perception, so dots appeared static to the operator.
  - After stronger scaling, growth looked square-ish instead of purely circular at high delta.
- Fix:
  - Increased temporal sensitivity and radius multiplier for `07.08`.
  - Documented square-ish bloom as expected with current cell ownership model.
- Concrete verification:
  - `python3 -m py_compile retina_cannon.py` passes after changes.
  - Presence checks via `rg` confirm: `iChannel1` wiring, new mode name, and updated detail range.
- Prevention:
  - For temporal visuals, validate visibility with a purposeful frame lag and multi-sample delta before concluding effect strength.
  - When cell-based dot partitioning is used, document expected geometric artifacts (square-ish bloom) explicitly in README/KB.
