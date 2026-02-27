#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve kms-glsl: KMS_GLSL_DIR env var > ../kms-glsl > ~/kms-glsl
if [ -z "${KMS_GLSL_DIR:-}" ]; then
    for _d in "$SCRIPT_DIR/../kms-glsl" "$HOME/kms-glsl"; do
        if [ -d "$_d/lib" ]; then
            KMS_GLSL_DIR="$(cd "$_d" && pwd)"
            break
        fi
    done
fi

if [ -z "${KMS_GLSL_DIR:-}" ]; then
    echo "[FATAL] kms-glsl not found. Set KMS_GLSL_DIR or place it at ../kms-glsl"
    exit 1
fi

cd "$KMS_GLSL_DIR"
PYTHONPATH="$KMS_GLSL_DIR" \
exec python3 "$SCRIPT_DIR/retina_cannon.py" "$SCRIPT_DIR/rutt_etra.frag"
