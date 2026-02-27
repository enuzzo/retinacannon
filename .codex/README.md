# .codex - quick guide

`MEMORY.md`: stable rules, technical decisions, and checklist.

`SESSION_LOG.md`: append-only diary for errors/fixes/verifications.

Session start ritual:
1. Read `MEMORY.md`.
2. Read the last 2 entries of `SESSION_LOG.md`.

Session end ritual:
1. Append a new entry to `SESSION_LOG.md`.
2. Update `MEMORY.md` only for truly stable rules.

Absolute prohibition:
- Never write passwords/tokens/keys in `.codex/*`.
