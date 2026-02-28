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
