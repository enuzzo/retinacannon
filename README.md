# Retina Cannon

Local project for shader/camera rendering with Python and shell scripts.

## Structure
- Runtime shaders and scripts are in this root (`*.frag`, `retina_cannon.py`, `start_cannon.sh`).
- `glslViewer/` is treated as an external local dependency (separate repo, not versioned here).
- `.codex/` stores operational memory and session logs.

## Quick start
1. Verify graphics/camera prerequisites on the host.
2. Run: `/home/enuzzo/retinacannon/start_cannon.sh`

## Security
- No secrets in versioned files.
- Secrets only in ignored local files (`config.local.h`, `.env.local`, etc.).
