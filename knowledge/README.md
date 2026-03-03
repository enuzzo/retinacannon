# Knowledge Index

This folder is a human-friendly index for project knowledge.

Canonical operational memory remains in hidden Codex files:
- `../.codex/MEMORY.md` — durable decisions, pitfalls, runtime rules
- `../.codex/SESSION_LOG.md` — append-only session history

Runtime-critical files (keep in repo root):
- `retina_cannon.py`
- `rutt_etra.frag`
- `cam_passthrough.frag`
- `start_cannon.sh`, `run_rutt.sh`, `run_base.sh`

Experimental/legacy shaders were moved to:
- `../shaders/experiments/`

Color troubleshooting baseline:
- New effects must start from `texture(...).rgb` and be compared against Rutt.
- Use `.bgr` only intentionally per effect.

## Latest durable decisions (2026-03-03)
- Effect catalog now includes `uEffectMode=10` (`Vector Profile Scope`).
- `Vector Profile Scope` color modes:
  - `10.01` Scope Mono
  - `10.02` Camera Overlay
  - `10.03` Tint Overlay
  - `10.04` Thermal Overlay
- Operator-approved visual rule: modes `10.02..10.04` must render **trace-only color on black**, with no visible camera/video underlay.
- Scope density control baseline:
  - default `2.20`
  - range `0.8..3.4`
  - step `0.20`
