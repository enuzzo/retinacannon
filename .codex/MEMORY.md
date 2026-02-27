# MEMORY - Retina Cannon

## Prime direttive
- Non salvare segreti in chiaro in file versionati, log, output o commit message.
- Inizio sessione: leggere questo file + ultime 2 entry di `SESSION_LOG.md`.
- Fare solo modifiche minime, verificabili, coerenti con il progetto.
- Non cambiare logica applicativa senza richiesta esplicita.

## Preferenze di lavoro
- Ispezione iniziale: struttura, sicurezza, stato git.
- Verifica concreta prima di chiudere (run/build/lint/grep).
- Patch piccole e con uno scopo chiaro.

## Decisioni tecniche consolidate
- Repo principale: `/home/enuzzo/retinacannon` (questa root).
- Stack runtime: shader `.frag` + script Python/shell.
- Dipendenza esterna: `glslViewer/` (gestita come repo separata locale).
- Comando run principale: `/home/enuzzo/retinacannon/start_cannon.sh`.

## Sicurezza e segreti
- Regola: segreti solo in file locali ignorati (`config.local.h`, `.env.local`, ecc).
- Template eventualmente versionati devono essere puliti (`config.example.h`, `.env.example`).
- `.codex/*` non deve contenere credenziali; usare placeholder come `<WIFI_PASSWORD>`.

## Gotcha ricorrenti
- Runtime grafico puo' fallire se manca piattaforma GLFW/display. (verificato)
- `glslViewer/` qui e' una repo annidata, non parte di questa repo root. (verificato)

## Checklist pre-flight
- [ ] Leggere `MEMORY.md`.
- [ ] Leggere ultime 2 entry di `SESSION_LOG.md`.
- [ ] Verificare `git status`.
- [ ] Cercare possibili segreti con scan mirata.
- [ ] Testare almeno un comando reale prima del commit.
- [ ] Append log di fine sessione.
