# Matrix Reveal Splash Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Matrix-rain "reveal" animation to the startup splash and a "cover" animation before DRM takeover, using column-drop ANSI characters that unveil/conceal the terminal content cinematically.

**Architecture:** Three new functions (`_build_splash_lines`, `_matrix_reveal_animation`, `_matrix_cover_animation`) plus a refactor of `_print_vhs_splash` for the wide-terminal path. The narrow-terminal path (`cols < 56`) is unchanged. The cover animation runs after the countdown, immediately before `_clear_to_black()` + DRM.

**Tech Stack:** Pure Python, ANSI escape codes (24-bit color already in use), cursor positioning (`\033[row;colH`), `sys.stdout.write` for frame-by-frame rendering. No new imports needed (`sys`, `re`, `random`, `time` already imported).

---

## Chunk 1: Core helpers and reveal animation

### Task 1: Add `_build_splash_lines()`

Refactors the wide-terminal splash content into a data structure instead of printing directly, so the animation can consume it.

**Files:**
- Modify: `retina_cannon.py` — add after `_visible_len()` (around line 354)

- [ ] **Step 1: Add the function** after `_visible_len` in `retina_cannon.py`

```python
def _build_splash_lines(cols, rows):
    """Pre-compute wide-terminal splash as (plain_text, styled_text) line pairs.

    Returns (lines, quote_plain) where lines covers terminal rows 1..N.
    plain_text  = ANSI-stripped string, used during animation for char lookup.
    styled_text = full ANSI string, used for final repaint after reveal.
    """
    box_w = min(cols, 80)
    title = _figlet_title_lines(max_width=cols)
    quote_raw = random.choice(_BOOT_LINES)

    title_h = len(title)
    # box=11, blank_above_quote=1, quote=1, blank_below=1
    content_h = title_h + 1 + 11 + 1 + 1 + 1
    top_pad = max(1, (rows - content_h) // 2)

    lines = []

    # Vertical padding
    for _ in range(top_pad):
        lines.append(('', ''))

    # Title — lolcat colored
    centered_title = [_center_text_line(ln, cols) for ln in title]
    plain_title_block = '\n'.join(centered_title) + '\n'
    styled_title_block = _lolcat_colorize(plain_title_block)
    styled_title_lines = (
        styled_title_block.rstrip('\n').split('\n')
        if styled_title_block else centered_title
    )
    # Pad to same length as plain list (lolcat might drop trailing blank lines)
    while len(styled_title_lines) < len(centered_title):
        styled_title_lines.append('')
    for plain, styled in zip(centered_title, styled_title_lines):
        lines.append((plain, styled))

    # Blank after title
    lines.append(('', ''))

    # NFO box (11 lines)
    margin = ' ' * max(0, (cols - box_w) // 2)
    nfo_styled = [
        margin + _nfo_top(box_w),
        margin + _nfo_meta_line('GRP',  'Netmilk Studio sagl',
                                'REL',  'v3.0 [FINAL]',              box_w),
        margin + _nfo_meta_line('TYPE', 'Realtime GLSL Engine',
                                'DATE', datetime.now().strftime('%Y-%m-%d'), box_w),
        margin + _nfo_meta_line('PLAT', 'Raspberry Pi / kms-glsl',
                                'EFXS', f'{len(EFFECT_MODE_NAMES)} x .frag',  box_w),
        margin + _nfo_sep(box_w),
        margin + _nfo_status_line('Acquiring DRM master',                      box_w),
        margin + _nfo_status_line('Loading GLSL pipeline',                     box_w),
        margin + _nfo_status_line(f'Calibrating Pi camera ({CAM_W}\u00d7{CAM_H})', box_w),
        margin + _nfo_status_line('Motion detection warmup',                   box_w),
        margin + _nfo_status_line('Keyboard controller ready',                 box_w),
        margin + _nfo_bot(box_w),
    ]
    for styled in nfo_styled:
        lines.append((_ANSI_STRIP_RE.sub('', styled), styled))

    # Blank above quote
    lines.append(('', ''))

    # Quote — full brightness (skip glow animation; reveal IS the entrance)
    quote_short = quote_raw[:cols - 4] if len(quote_raw) > cols - 4 else quote_raw
    centered_q  = _center_text_line('\u201c' + quote_short + '\u201d', cols)
    lines.append((centered_q, '\033[1;97m' + centered_q + ANSI_RESET))

    # Blank below quote
    lines.append(('', ''))

    return lines, quote_raw
```

- [ ] **Step 2: Syntax check**

```bash
python3 -m py_compile retina_cannon.py && echo OK
```
Expected: `OK`

---

### Task 2: Add `_matrix_reveal_animation()`

Column-drop reveal: each column has a drop head + fading trail; cells behind the trail are permanently revealed in their styled color.

**Files:**
- Modify: `retina_cannon.py` — add after `_build_splash_lines()`

- [ ] **Step 1: Add the function**

```python
# Drop-trail color sequence: head → bright green → green → dim → dark → very dark
_MATRIX_TRAIL_COLORS = [
    '\033[1;97m',      # 0 head  — bright white flash
    '\033[1;92m',      # 1       — bright green
    '\033[32m',        # 2       — green
    '\033[2;32m',      # 3       — dim green
    '\033[38;5;22m',   # 4       — dark green
    '\033[38;5;22m',   # 5       — dark green (extra fade step)
]
_MATRIX_TRAIL_CHARS  = ['▓', '▓', '▒', '░', '·', ' ']
_MATRIX_HEAD_CHARS   = '▓█▒'

def _matrix_reveal_animation(content_lines, cols):
    """Reveal content_lines with a matrix rain drop animation.

    content_lines : list of (plain_text, styled_text) tuples.
                    Each tuple maps to terminal row (index+1).
    cols          : terminal column count.
    Screen must already be cleared to black before calling.
    Cursor is left at row len(content_lines)+1, col 1 on return.
    """
    n_rows   = len(content_lines)
    trail    = len(_MATRIX_TRAIL_COLORS)      # 6 rows of fading trail
    frame_dt = 0.033                          # 30 fps — safe for local display (no SSH latency)

    # Per-column state
    stagger  = max(2, n_rows // 4)
    speeds   = [random.choice([1, 2, 2, 2]) for _ in range(cols)]
    drop_row = [random.randint(-stagger, 0)  for _ in range(cols)]

    # Track which cells have had their final styled char written
    revealed = [[False] * cols for _ in range(n_rows)]

    out = sys.stdout

    def _write(row_0, col_0, ch, color=''):
        out.write(f'\033[{row_0 + 1};{col_0 + 1}H')
        if color:
            out.write(color + ch + '\033[0m')
        else:
            out.write(ch)

    def _reveal_cell(row, col):
        if revealed[row][col]:
            return
        revealed[row][col] = True
        plain, styled = content_lines[row]
        ch = plain[col] if col < len(plain) else ' '
        if not ch.strip():
            # Whitespace: just write a space (no ANSI needed)
            _write(row, col, ' ')
            return
        # Write the full styled line at this row when revealing first char in row
        # — cheaper than per-character ANSI reconstruction; overwrites the entire row
        # once the drop has passed it.  We track per-cell to avoid double-writes but
        # the actual draw is the whole styled line (done once per row).
        # Mark all cols in this row as revealed to avoid redundant full-line rewrites.
        for c in range(cols):
            revealed[row][c] = True
        out.write(f'\033[{row + 1};1H' + styled + '\033[K')

    active = list(range(cols))
    while active:
        next_active = []
        for c in active:
            drop_row[c] += speeds[c]
            r = drop_row[c]

            # Draw drop head + trail
            for t in range(trail):
                tr = r - t
                if 0 <= tr < n_rows:
                    ch = (random.choice(_MATRIX_HEAD_CHARS) if t == 0
                          else _MATRIX_TRAIL_CHARS[t])
                    _write(tr, c, ch, _MATRIX_TRAIL_COLORS[t])

            # Reveal rows that the full trail has passed
            reveal_r = r - trail
            if 0 <= reveal_r < n_rows:
                _reveal_cell(reveal_r, c)

            if r < n_rows + trail + 2:
                next_active.append(c)
            else:
                # Column finished — reveal any cells not yet written
                for row in range(n_rows):
                    if not revealed[row][c]:
                        _reveal_cell(row, c)

        active = next_active
        out.flush()
        time.sleep(frame_dt)

    # Final repaint pass: ensure every row has its proper styled text
    # (handles edge cases where _reveal_cell was called per-char then overwritten)
    for row_idx, (plain, styled) in enumerate(content_lines):
        out.write(f'\033[{row_idx + 1};1H' + styled + '\033[K')
    out.write(f'\033[{n_rows + 1};1H')
    out.flush()
```

**Note on `_reveal_cell` strategy:** Rather than reconstruct per-character ANSI from `styled_text` (which may contain multi-char escape sequences making column indexing hard), we reveal the entire row at once when the drop first reaches any character in it. All cols in that row are marked revealed immediately. This gives a clean "line lights up as drop passes" aesthetic — the drop sweeps across and each row flashes on as a whole. Visually indistinguishable from per-char reveal at 20 fps.

- [ ] **Step 2: Syntax check**

```bash
python3 -m py_compile retina_cannon.py && echo OK
```
Expected: `OK`

---

### Task 3: Add `_matrix_cover_animation()`

Reverse: drops fall and erase content back to black. Called just before `_clear_to_black()` + DRM handoff.

**Files:**
- Modify: `retina_cannon.py` — add after `_matrix_reveal_animation()`

- [ ] **Step 1: Add the function**

```python
def _matrix_cover_animation(n_rows, cols):
    """Cover terminal rows 1..n_rows back to black with matrix rain drops.

    Used as exit transition before DRM takes the display.
    Faster than reveal (higher speeds, shorter stagger).
    """
    trail    = 5
    frame_dt = 0.025  # 40 fps — fast cover on local display
    cover_colors = [
        '\033[1;92m',      # head   — bright green
        '\033[32m',        # t-1    — green
        '\033[2;32m',      # t-2    — dim green
        '\033[38;5;22m',   # t-3    — dark green
        '\033[38;5;232m',  # t-4    — near-black
    ]
    cover_chars = ['▓', '▒', '░', '·', ' ']

    stagger  = max(1, n_rows // 6)
    speeds   = [random.choice([2, 2, 3]) for _ in range(cols)]
    drop_row = [random.randint(-stagger, 0) for _ in range(cols)]
    erased   = [[False] * cols for _ in range(n_rows)]

    out = sys.stdout

    def _erase_row(row):
        if all(erased[row]):
            return
        for c in range(cols):
            erased[row][c] = True
        out.write(f'\033[{row + 1};1H\033[2K')   # erase entire terminal line

    active = list(range(cols))
    while active:
        next_active = []
        for c in active:
            drop_row[c] += speeds[c]
            r = drop_row[c]

            # Draw trailing glow
            for t in range(trail):
                tr = r - t
                if 0 <= tr < n_rows:
                    ch = random.choice('▓▒') if t == 0 else cover_chars[t]
                    out.write(f'\033[{tr + 1};{c + 1}H{cover_colors[t]}{ch}\033[0m')

            # Erase row once fully behind the trail
            erase_r = r - trail
            if 0 <= erase_r < n_rows:
                _erase_row(erase_r)

            if r < n_rows + trail + 2:
                next_active.append(c)
            else:
                for row in range(n_rows):
                    _erase_row(row)

        active = next_active
        out.flush()
        time.sleep(frame_dt)

    # Hard clear to guarantee black (belt + suspenders)
    for row in range(n_rows):
        out.write(f'\033[{row + 1};1H\033[2K')
    out.flush()
```

- [ ] **Step 2: Syntax check**

```bash
python3 -m py_compile retina_cannon.py && echo OK
```

---

## Chunk 2: Wire into `_print_vhs_splash`

### Task 4: Refactor `_print_vhs_splash()` wide-terminal path

Replace the existing wide-terminal print sequence with: build → reveal → countdown → cover.

**Files:**
- Modify: `retina_cannon.py:660-727` (the `_print_vhs_splash` function)

- [ ] **Step 1: Replace the wide-terminal block (lines ~681–727)**

Locate the comment `# Wide terminal: figlet title FULL WIDTH above box, not inside` and replace everything from there to the end of the function with:

```python
    # Wide terminal: build content, animate reveal, then cover before DRM.
    content_lines, _quote = _build_splash_lines(cols, rows)
    n_content = len(content_lines)

    _clear_to_black()
    _matrix_reveal_animation(content_lines, cols)

    # Position cursor at the countdown row (one below the last content line)
    sys.stdout.write(f'\033[{n_content + 1};1H')
    sys.stdout.flush()

    if countdown_seconds < 0:
        print(_styled('  >> HOLD — press any key to continue', ANSI_YELLOW, bold=True))
        _wait_splash_release()
    else:
        start   = max(1, int(countdown_seconds))
        bar_w   = min(cols * 30 // 100, 40)
        for n in range(start, -1, -1):
            label         = f'LAUNCHING IN {n} '
            filled        = round(bar_w * (start - n) / max(start, 1))
            empty         = bar_w - filled
            bar_str       = (_styled('█' * filled, ANSI_BRIGHT_GREEN)
                             + _styled('░' * empty, ANSI_DARK_GRAY))
            content_str   = _styled(label, ANSI_YELLOW, bold=True) + bar_str
            content_vis_w = len(label) + bar_w
            margin        = ' ' * max(0, (cols - content_vis_w) // 2)
            print('\r' + margin + content_str + '\033[K', end='', flush=True)
            time.sleep(1.0)
        print()

    # Cover transition: matrix rain erases screen before DRM takes display.
    _matrix_cover_animation(rows, cols)
    _clear_to_black()
    _show_cursor()
```

- [ ] **Step 2: Syntax check**

```bash
python3 -m py_compile retina_cannon.py && echo OK
```

- [ ] **Step 3: Verify the narrow-terminal fallback is untouched**

Read lines 663–679 and confirm the `if cols < 56:` block still ends with `return` before the new wide-terminal code. No changes should have touched it.

- [ ] **Step 4: Commit**

```bash
git add retina_cannon.py docs/superpowers/plans/2026-03-10-matrix-reveal-splash.md
git commit -m "feat: matrix rain reveal/cover animation for startup splash"
```

---

## Quick reference: what changed

| Function | Status | Purpose |
|---|---|---|
| `_build_splash_lines(cols, rows)` | NEW | Build splash as `(plain, styled)` line pairs |
| `_matrix_reveal_animation(content_lines, cols)` | NEW | Matrix rain reveals content from black |
| `_matrix_cover_animation(n_rows, cols)` | NEW | Matrix rain covers content back to black |
| `_print_vhs_splash()` wide path | MODIFIED | Uses the three functions above |
| `_print_vhs_splash()` narrow path | UNCHANGED | `cols < 56` fallback untouched |

## Validation on Pi

1. `python3 -m py_compile retina_cannon.py` — must pass
2. `./start_cannon.sh` — watch:
   - Matrix rain reveals title + NFO box + quote (~1.5s)
   - Countdown bar runs normally below content
   - Matrix rain covers screen before camera feed appears
3. Ctrl+C quit — shutdown banner appears normally (matrix cover is only on the splash path)
4. Test narrow terminal: `COLUMNS=50 ./start_cannon.sh` — should skip animation, use old static splash
