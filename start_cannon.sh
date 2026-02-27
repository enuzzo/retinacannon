#!/bin/bash
set -euo pipefail

cd /home/enuzzo/kms-glsl
PYTHONPATH=/home/enuzzo/kms-glsl \
exec python3 /home/enuzzo/retinacannon/retina_cannon.py /home/enuzzo/retinacannon/rutt_etra.frag
