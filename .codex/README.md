# .codex - guida breve

`MEMORY.md`: regole stabili, decisioni tecniche, checklist.

`SESSION_LOG.md`: diario append-only di errori/fix/verifiche.

Rituale inizio sessione:
1. Leggi `MEMORY.md`.
2. Leggi ultime 2 entry di `SESSION_LOG.md`.

Rituale fine sessione:
1. Appendi una nuova entry in `SESSION_LOG.md`.
2. Aggiorna `MEMORY.md` solo per regole davvero stabili.

Divieto assoluto:
- Non scrivere mai password/token/chiavi in `.codex/*`.
