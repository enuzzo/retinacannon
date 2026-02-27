# MEMORY - Retina Cannon

## Core directives
- Never store plaintext secrets in versioned files, logs, output, or commit messages.
- Keep project-facing text in English (docs, comments, review notes, commit messages).
- Session start: read this file plus the last 2 entries in `SESSION_LOG.md`.
- Keep changes minimal, verifiable, and aligned with project goals.
- Do not change application logic without an explicit request.

## Working preferences
- Start with quick inspection: structure, security, git status.
- Run at least one concrete verification before closing (run/build/lint/grep).
- Keep patches small and single-purpose.

## Consolidated technical decisions
- Main repository: `/home/enuzzo/retinacannon` (this root).
- Runtime stack: `.frag` shaders + Python/shell scripts.
- External dependency: `glslViewer/` (managed as a separate local repo).
- Main run command: `/home/enuzzo/retinacannon/start_cannon.sh`.

## Security and secrets
- Rule: secrets live only in ignored local files (`config.local.h`, `.env.local`, etc.).
- Any versioned templates must stay clean (`config.example.h`, `.env.example`).
- `.codex/*` must not include credentials; use placeholders like `<WIFI_PASSWORD>`.

## Recurring gotchas
- Graphics runtime can fail when GLFW/display platform is unavailable. (verified)
- `glslViewer/` here is a nested repo, not part of this root repo history. (verified)

## Pre-flight checklist
- [ ] Read `MEMORY.md`.
- [ ] Read the last 2 entries in `SESSION_LOG.md`.
- [ ] Check `git status`.
- [ ] Run a targeted secret scan.
- [ ] Test at least one real command before commit.
- [ ] Append an end-of-session log entry.
