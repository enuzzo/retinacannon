# Retina Cannon Performance Optimization Tracker

## Scope
- Goal: optimize FPS for each effect (`uEffectMode 0..9`) with measurable before/after evidence.
- Hardware context: Raspberry Pi + camera + `kms-glsl`.
- Method: one effect at a time, same benchmark protocol, log evidence preserved.

## Benchmark Protocol (Standard)
1. Run from repo root with fixed duration and selected effect:
```bash
timeout 35s env RETINA_BENCH_SECONDS=10 RETINA_BENCH_EFFECT=<ID> python3 retina_cannon.py --splash 0 2>&1 | tee /tmp/retina_perf_effect<ID>_<tag>.log
```
2. Read the line:
```text
[BENCH_RESULT] effect=<ID> name="<effect>" avg_fps=<value>
```
3. Record in table below:
- `baseline_fps`
- `after_fps`
- `delta_fps`
- notes on what worked / what failed

Notes:
- Benchmark support is in `retina_cannon.py` via env vars:
  - `RETINA_BENCH_SECONDS`
  - `RETINA_BENCH_EFFECT`
- Stable parser line: `BENCH_RESULT`.

## Action Plan by Blocks
### Block A (Core visuals)
- ID 00 `Rutt-Etra CRT`
- ID 01 `ASCII Cam`
- ID 02 `Pixel Art`
- ID 03 `Raster Vision`

### Block B (Heavy glitch stack)
- ID 04 `Digital Codec Corruption`
- ID 05 `VHS Tracking Burn`
- ID 06 `Posterize Glitch Comic`

### Block C (Experimental lineage)
- ID 07 `Lens Dot Bevel` (origin: totry 2)
- ID 08 `Mirror Zoom Tiles` (origin: totry 1)
- ID 09 `Chromatic Trails` (origin: totry 8)

### Block D (Cross-cutting)
- Shared helpers (`safeUV`, sampling paths, hash/noise usage)
- Uniform/update overhead sanity check in Python callback
- Optional quality/perf switches where needed

## Full Effect Inventory
| ID | Effect Name | Block | Status |
|---|---|---|---|
| 00 | Rutt-Etra CRT | A | In progress |
| 01 | ASCII Cam | A | Pending |
| 02 | Pixel Art | A | Pending |
| 03 | Raster Vision | A | Pending |
| 04 | Digital Codec Corruption | B | Pending |
| 05 | VHS Tracking Burn | B | Pending |
| 06 | Posterize Glitch Comic | B | Pending |
| 07 | Lens Dot Bevel | C | Pending |
| 08 | Mirror Zoom Tiles | C | Pending |
| 09 | Chromatic Trails | C | Pending |

## Performance Register
| ID | Effect | Baseline FPS | After FPS | Delta | Optimizations Applied | Evidence |
|---|---|---:|---:|---:|---|---|
| 00 | Rutt-Etra CRT | 10.00 | 10.25 | +0.25 | Reused center texture sample in `renderRutt` (removed one duplicate fetch) | `/tmp/retina_perf_effect00_before.log`, `/tmp/retina_perf_effect00_after.log` |
| 01 | ASCII Cam | - | - | - | - | - |
| 02 | Pixel Art | - | - | - | - | - |
| 03 | Raster Vision | - | - | - | - | - |
| 04 | Digital Codec Corruption | - | - | - | - | - |
| 05 | VHS Tracking Burn | - | - | - | - | - |
| 06 | Posterize Glitch Comic | - | - | - | - | - |
| 07 | Lens Dot Bevel | - | - | - | - | - |
| 08 | Mirror Zoom Tiles | - | - | - | - | - |
| 09 | Chromatic Trails | - | - | - | - | - |

## Effect Sheet 00 - Rutt-Etra CRT
### Baseline
- Command:
```bash
timeout 35s env RETINA_BENCH_SECONDS=10 RETINA_BENCH_EFFECT=0 python3 retina_cannon.py --splash 0 2>&1 | tee /tmp/retina_perf_effect00_before.log
```
- Result: `[BENCH_RESULT] ... avg_fps=10.00`

### Optimization Applied
- File: `rutt_etra.frag`
- Function: `renderRutt(...)`
- Change:
  - Added cached center sample:
    - `vec2 sampleUVC = safeUV(sampleUV);`
    - `vec3 sampleColC = texture(iChannel0, sampleUVC).rgb;`
  - Reused `sampleColC` for:
    - center luminance contribution
    - `camColor`
- Why:
  - same center texel was sampled twice per fragment
  - this removes one redundant texture fetch in a hot path

### After
- Command:
```bash
timeout 35s env RETINA_BENCH_SECONDS=10 RETINA_BENCH_EFFECT=0 python3 retina_cannon.py --splash 0 2>&1 | tee /tmp/retina_perf_effect00_after.log
```
- Result: `[BENCH_RESULT] ... avg_fps=10.25`
- Delta: `+0.25 FPS` (`+2.5%`)

### What Worked
- Micro-optimization was safe and measurable.
- Visual output behavior unchanged for the tested mode.
- Benchmark flow now supports autonomous run/stop and machine-readable output.

### What Did Not Work / Caveats
- Instant FPS line in first seconds can spike due smoothing warm-up; use `BENCH_RESULT` as canonical value.
- Terminal banner noise is high; always parse by `BENCH_RESULT`.

## Resume Checklist (for any AI)
1. Pick next pending ID from `Performance Register`.
2. Run baseline command with `RETINA_BENCH_EFFECT=<ID>`.
3. Implement one focused optimization at a time.
4. Re-run same benchmark command for after measurement.
5. Update:
- `Performance Register`
- corresponding `Effect Sheet <ID>`
- notes `What Worked / What Did Not Work`
6. If regression (`delta < 0`), rollback only that change and document failed attempt.
