# Totry Directive (Clean Session Start)

Keep scope strict: only shortlisted shaders remain.

## Allowed candidates
1. `2.txt` (priority 1)
2. `1.txt` (priority 2)
3. `8.txt` (priority 3, only with FPS guardrails)

## Execution order
1. Port `2.txt` into a dedicated experimental effect path first.
2. Port `1.txt` as a fast fallback/win.
3. Attempt `8.txt` only after baseline FPS is measured and accepted.

## Non-goals in this phase
- Do not reintroduce removed files.
- Do not add multi-pass/buffer architecture now.
- Do not add extra channel dependencies (`iChannel1+`) unless explicitly requested.

## Performance guardrails
- Test runtime FPS after each port.
- If FPS drops materially from baseline, stop and simplify the effect.
- Prefer visual character with stable frame pacing over heavier math.

## Definition of done for each candidate
- Integrated behind existing controls.
- No regressions in current effects.
- Screenshot flow still works.
- README/docs update only after visual + FPS verification.
