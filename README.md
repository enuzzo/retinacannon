# Retina Cannon

Progetto locale per rendering shader/camera con script Python e shell.

## Struttura
- Shader e script runtime in questa root (`*.frag`, `retina_cannon.py`, `start_cannon.sh`).
- `glslViewer/` e' trattata come dipendenza esterna locale (repo separata, non versionata qui).
- `.codex/` contiene memoria operativa e diario sessioni.

## Avvio rapido
1. Verifica prerequisiti grafici/camera su host.
2. Esegui: `/home/enuzzo/retinacannon/start_cannon.sh`

## Sicurezza
- Nessun segreto in file versionati.
- Segreti solo in file locali ignorati (`config.local.h`, `.env.local`, ecc).
