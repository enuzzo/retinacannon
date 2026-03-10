#!/usr/bin/env python
import sys, os, re, glob, threading, select, termios, signal, subprocess, random, math, shutil
from ctypes import CFUNCTYPE, c_uint, c_uint64, c_float, byref
from pathlib import Path
from datetime import datetime

RETINA_DIR = Path(__file__).resolve().parent

# Resolve kms-glsl dependency: KMS_GLSL_DIR env var > ../kms-glsl > ~/kms-glsl
_kms_env = os.environ.get('KMS_GLSL_DIR', '')
KMS_GLSL_DIR = Path(_kms_env).resolve() if _kms_env else None

if KMS_GLSL_DIR is None or not (KMS_GLSL_DIR / 'glsl.so').is_file():
    KMS_GLSL_DIR = None
    for _candidate in [
        RETINA_DIR.parent / 'kms-glsl',
        Path.home() / 'kms-glsl',
    ]:
        if (_candidate / 'glsl.so').is_file():
            KMS_GLSL_DIR = _candidate.resolve()
            break

if KMS_GLSL_DIR is None:
    print('[FATAL] kms-glsl not found. Set KMS_GLSL_DIR or place it at ../kms-glsl')
    sys.exit(1)

os.chdir(str(KMS_GLSL_DIR))
sys.path.insert(0, str(KMS_GLSL_DIR))

from lib import glsl, options
from gl import *

# ---- Initialize picamera2 immediately ----
from picamera2 import Picamera2
import libcamera
import numpy as np
import ctypes
import time
try:
    from PIL import Image
except Exception:
    Image = None

WIDTH, HEIGHT = 1640, 1232
picam = Picamera2()
config = picam.create_preview_configuration(
    main={"size": (WIDTH, HEIGHT), "format": "BGR888"},
    raw={"size": (3280, 2464)},
    transform=libcamera.Transform(vflip=1)
)
picam.configure(config)
picam.start()
time.sleep(1)

first = picam.capture_array()
CAM_H, CAM_W = first.shape[:2]
print(f'[Camera] {CAM_W}x{CAM_H} ready')

_frame = first.copy()
_lock = threading.Lock()
_running = True

def _capture_loop():
    global _frame, _prev_luma_small, _motion_level, _presence_scale, _presence_cx, _presence_cy
    while _running:
        f = picam.capture_array()
        with _lock:
            _frame = f
        # Motion & presence detection — camera is BGR888, downsample to ~200×150
        try:
            S = 8
            small = f[::S, ::S]
            luma = (0.299 * small[:,:,2] + 0.587 * small[:,:,1]
                    + 0.114 * small[:,:,0]).astype(np.float32) / 255.0
            _presence_scale = float(np.mean(luma))
            if _prev_luma_small is not None and _prev_luma_small.shape == luma.shape:
                diff = np.abs(luma - _prev_luma_small)
                # Dead-zone: ignore camera sensor noise (< 3% per pixel)
                significant = np.where(diff > 0.03, diff - 0.03, 0.0)
                raw = float(np.clip(np.mean(significant) * 30.0, 0.0, 1.0))
                # Asymmetric smoothing: fast attack, slow decay
                if raw > _motion_level:
                    _motion_level = raw * 0.65 + _motion_level * 0.35
                else:
                    _motion_level = raw * 0.08 + _motion_level * 0.92
            # Weighted centroid of above-average regions
            thresh = max(_presence_scale * 1.25, 0.08)
            bright = np.where(luma > thresh, luma - thresh, 0.0)
            total = bright.sum()
            if total > 0.001:
                h, w = luma.shape
                ys, xs = np.mgrid[0:h, 0:w]
                _presence_cx = float((xs * bright).sum() / total / w)
                _presence_cy = 1.0 - float((ys * bright).sum() / total / h)
            _prev_luma_small = luma
        except Exception:
            pass

threading.Thread(target=_capture_loop, daemon=True).start()

# ---- Manual GL texture setup ----
tex_id = None
tex_prev_id = None
tex_unit = 0
loc_channel0 = -1
loc_channel1 = -1
loc_color_mode = -1
loc_rutt_wave = -1
loc_ascii_density = -1
loc_effect_mode = -1
loc_view_mode = -1
loc_mirror = -1
loc_camera_aspect = -1
loc_pixelart_size = -1
loc_motion_level = -1
loc_presence_scale = -1
loc_presence_cx = -1
loc_presence_cy = -1
current_rutt_color_mode = 0
current_ascii_color_mode = 0
current_pixelart_color_mode = 0
current_rutt_wave = 0.40
current_rutt_prismwarp_split = 1.0
current_rutt_phosphor_tint = 1.0
current_rutt_wiremono_contrast = 1.0
current_terrain_amp = 1.50
current_ascii_density = 3.00
current_ascii_contrast = 1.0
current_pixelart_size = 6.0
current_raster_color_mode = 0
current_raster_size = 12.0
current_datamosh_color_mode = 0
current_vhsburn_color_mode = 0
current_poster_color_mode = 0
current_lensdot_color_mode = 0
current_mirrorzoom_color_mode = 0
current_chromatrail_color_mode = 0
current_profilescope_color_mode = 0
current_datamosh_amount = 2.0
current_vhs_tracking = 1.5
current_poster_levels = 4.0
current_lensdot_detail = 2.6
current_mirrorzoom_amount = 0.80
current_chromatrail_intensity = 1.20
current_profilescope_grid = 2.20
DATAMOSH_AMOUNT_STEP = 0.25
DATAMOSH_AMOUNT_MIN = 0.5
DATAMOSH_AMOUNT_MAX = 6.0
VHS_TRACK_STEP = 0.20
VHS_TRACK_MIN = 0.5
VHS_TRACK_MAX = 5.0
POSTER_LEVEL_STEP = 1.0
POSTER_LEVEL_MIN = 2.0
POSTER_LEVEL_MAX = 12.0
LENSDOT_DETAIL_STEP = 0.25
LENSDOT_DETAIL_MIN = 0.20
LENSDOT_DETAIL_MAX = 14.0
MIRRORZOOM_AMOUNT_STEP = 0.10
MIRRORZOOM_AMOUNT_MIN = 0.2
MIRRORZOOM_AMOUNT_MAX = 1.6
CHROMATRAIL_INTENSITY_STEP = 0.25
CHROMATRAIL_INTENSITY_MIN = 0.5
CHROMATRAIL_INTENSITY_MAX = 2.4
PROFILESCOPE_GRID_STEP = 0.20
PROFILESCOPE_GRID_MIN = 0.8
PROFILESCOPE_GRID_MAX = 3.4
current_effect_mode = 0
current_view_mode = 0
current_mirror_view = 1
current_show_fps = 0
RUTT_WAVE_STEP = 0.10
RUTT_WAVE_MIN = 0.05
RUTT_WAVE_MAX = 3.80
RUTT_SPLIT_STEP = 0.20
RUTT_SPLIT_MIN = 0.1
RUTT_SPLIT_MAX = 5.0
RUTT_PHOSPHOR_STEP = 0.10
RUTT_PHOSPHOR_MIN = 0.0
RUTT_PHOSPHOR_MAX = 2.0
RUTT_CONTRAST_STEP = 0.10
RUTT_CONTRAST_MIN = 0.2
RUTT_CONTRAST_MAX = 3.0
TERRAIN_AMP_STEP = 0.25
TERRAIN_AMP_MIN = 0.5
TERRAIN_AMP_MAX = 5.0
ASCII_DENSITY_STEP = 0.20
ASCII_DENSITY_MIN = 1.00
ASCII_DENSITY_MAX = 6.00
ASCII_CONTRAST_STEP = 0.10
ASCII_CONTRAST_MIN = 0.20
ASCII_CONTRAST_MAX = 3.0
PIXELART_SIZE_STEP = 2.0
PIXELART_SIZE_MIN = 4.0
PIXELART_SIZE_MAX = 48.0

RUTT_COLOR_MODE_NAMES = ['Prism Warp', 'Phosphor', 'Wire Mono', 'v002 Terrain']
ASCII_COLOR_MODE_NAMES = ['Symbol Color', 'Symbol Mono', 'Dense Mono Mix', 'Dense Color Mix']
PIXELART_COLOR_MODE_NAMES = ['Game Boy', 'Pixel Native', 'Toxic Candy']
PIXELART_MODE_DEFAULT_SIZES = [6.0, 4.0, 8.0]
RASTER_COLOR_MODE_NAMES = ['Thermal Raster', 'Thermal Inverted', 'Comic Ink Mono', 'Comic Pastel', 'Vibrant Pop']
DATAMOSH_COLOR_MODE_NAMES = ['RGB Mosh', 'Thermal Glitch', 'Acid Trip', 'Void Codec']
VHSBURN_COLOR_MODE_NAMES  = ['Signal Melt', 'Night Tape']
POSTER_COLOR_MODE_NAMES   = ['Warhol Pop', 'Neon Cel', 'Acid Bloom', 'Plasma Burn']
LENSDOT_COLOR_MODE_NAMES = [
    'Soft Bevel',
    'Hard Bevel',
    'Specular Punch',
    'Toxic Candy Drift',
    'Warhol Drift',
    'Neon Flux Drift',
    'Thermal Drift',
    'Spectral Delta Bloom',
]
MIRRORZOOM_COLOR_MODE_NAMES = ['Pulse', 'Wide Pulse', 'Hyper Pulse']
CHROMATRAIL_COLOR_MODE_NAMES = ['RGB Trail', 'Neon Trail', 'Thermal Trail']
PROFILESCOPE_COLOR_MODE_NAMES = ['Scope Mono', 'Camera Overlay', 'Tint Overlay', 'Thermal Overlay']
EFFECT_MODE_NAMES = [
    'Rutt-Etra CRT',
    'ASCII Cam',
    'Pixel Art',
    'Raster Vision',
    'Digital Codec Corruption',
    'VHS Tracking Burn',
    'Posterize Glitch Comic',
    'Lens Dot Bevel',
    'Mirror Zoom Tiles',
    'Chromatic Trails',
    'Vector Profile Scope',
]
VIEW_MODE_NAMES = ['16:9', '4:3', 'Fisheye']

_quiet_stdin_w = None
_fps_last_frame = None
_fps_last_time = None
_fps_smoothed = 0.0
_fps_last_report_time = None
_ctrl_c_requested = False
_session_start = None
_shader_name = ''
_prev_luma_small = None
_motion_level = 0.0
_presence_scale = 0.0
_presence_cx = 0.5
_presence_cy = 0.5
_prev_frame_for_shader = None
_prev_frame_lag_counter = 0
_render_w = 0
_render_h = 0
_shot_deadline = None
_shot_last_seconds = None
SHOT_COUNTDOWN_SEC = 3.0
_splash_seconds = 5
_bench_seconds = max(0.0, float(os.environ.get('RETINA_BENCH_SECONDS', '0') or 0))
_bench_effect = os.environ.get('RETINA_BENCH_EFFECT', '')

_BOOT_LINES = [
    'GREETINGS TO: everyone who knows why the tracker crashed at 4AM. you know who you are.',
    'WARNING: side effects include compulsive pixel-staring and unexplained nostalgia for hardware you never owned.',
    'THIS RELEASE IS DEDICATED TO: the scene. the noise. the ones who stayed up until the display burned in.',
    'USE OF THIS SOFTWARE IMPLIES ACCEPTANCE OF: aesthetic chaos, raster bliss, and at least one accidental screenshot.',
    'CODED IN: a fever dream of OpenGL ES, Python, and unreasonable ambition.',
    'NO PROTECTION APPLIED. NO PROTECTION NEEDED. BEAUTY IS ITS OWN CRACK.',
    'ATTENTION: your retinas are about to be held hostage by a Raspberry Pi. resistance is futile.',
    'THE TRACKER IS FULL. THE PARTY IS OVER. THE CANNON IS JUST WARMING UP.',
    'THIS IS NOT ART. THIS IS NOT TECH. THIS IS THE SPACE IN BETWEEN WHERE THE GOOD STUFF LIVES.',
    'PIXEL CLOCK: LOCKED. SYNC: STABLE. VIBE: ILLEGAL.',
    'DO NOT ADJUST YOUR MONITOR. THIS IS INTENTIONAL. ALL OF IT.',
    'IF YOU CAN READ THIS THE SHADER COMPILED. AGAINST ALL ODDS.',
    'SCENE RULE #1: it\'s not broken if it looks like that on purpose.',
    'SOME EFFECTS MAY CAUSE INVOLUNTARY AWE. NETMILK ACCEPTS NO LIABILITY.',
    'ESTIMATED TIME TO OBSESSION: 4 minutes. estimated time to explaining this to someone: never.',
    'REAL-TIME. NO PRERENDER. NO TRICKS. JUST THE GPU AND YOUR FACE.',
    'THE COPPER BARS HAVE BEEN REPLACED BY CAMERA SHADERS. THE VIBE REMAINS.',
    'YOU ARE NOW LOOKING AT YOURSELF THROUGH A LENS GROUND FROM PURE MATHEMATICS.',
    'BOOTING. PLEASE HOLD. THE DEMO DOES NOT CARE ABOUT YOUR SCHEDULE.',
    'SIGNAL ACQUIRED. IDENTITY OPTIONAL. DISTORTION MANDATORY.',
]

_SHUTDOWN_LINES = [
    'DRM master released. Monitor returned to the void.',
    'Process terminated. The noise continues without you.',
    'Raster offline. The copper bars are cooling down.',
    'Signal lost. This was not a malfunction.',
    'Cannon silent. Memory of the glitch persists.',
    'Session closed. Your face has been returned to meatspace.',
    'Fade to black. Professional hazard.',
    'Transmission ended. The tracker was full anyway.',
    'Shutdown clean. Artifacts were saved to disk.',
    'GL context destroyed. Good session. Do not tell anyone how long you stared.',
    'The demo ends. The party does not.',
    'Pipe closed. Stdin reclaimed. Dignity optional.',
    'Exit code 0. The only clean thing about this.',
    'All threads joined. All ghosts released.',
    'Camera stopped. The pixel grid goes dark.',
    'Framebuffer cleared. Scene credits roll in your head.',
    'Until next run — keep the toolchain ugly and the output beautiful.',
    'The cannon sleeps. Reload when ready.',
    'Memory free. VRAM free. Mind: questionable.',
    'Grüße an alle. Tschüss.',
]

_BLOCK_CHARS = '░▒▓█▓▒░'

if _bench_effect.strip():
    try:
        _bench_idx = int(_bench_effect)
        if 0 <= _bench_idx < len(EFFECT_MODE_NAMES):
            current_effect_mode = _bench_idx
    except Exception:
        pass
if _bench_seconds > 0.0:
    current_show_fps = 1

ANSI_RESET = '\033[0m'
ANSI_BOLD = '\033[1m'
ANSI_DIM = '\033[2m'
ANSI_CYAN = '\033[36m'
ANSI_MAGENTA = '\033[35m'
ANSI_GREEN = '\033[32m'
ANSI_YELLOW = '\033[33m'
ANSI_RED = '\033[31m'
ANSI_WHITE = '\033[37m'

ANSI_RAINBOW = [
    '\033[38;5;196m',  # red
    '\033[38;5;208m',  # orange
    '\033[38;5;226m',  # yellow
    '\033[38;5;46m',   # green
    '\033[38;5;51m',   # cyan
    '\033[38;5;21m',   # blue
    '\033[38;5;201m',  # magenta
]

ANSI_VHS_RAINBOW = [
    '\033[38;5;213m',  # pink/magenta
    '\033[38;5;39m',   # electric cyan
    '\033[38;5;228m',  # warm tape yellow
    '\033[38;5;208m',  # orange
    '\033[38;5;45m',   # aqua
    '\033[38;5;201m',  # neon magenta
]

# NFO/warez splash colors
ANSI_ELEC_CYAN    = '\033[38;5;39m'   # electric cyan — box borders
ANSI_BRIGHT_GREEN = '\033[38;5;46m'   # bright green  — [OK] + bar fill
ANSI_DARK_GRAY    = '\033[38;5;237m'  # dark gray     — bar empty
ANSI_CYAN_DIM     = '\033[36m'        # cyan dim      — metadata labels

_ANSI_STRIP_RE = re.compile(r'\033\[[0-9;]*m')

def _visible_len(s):
    """Return printable length of a string (strip ANSI codes)."""
    return len(_ANSI_STRIP_RE.sub('', s))

RETINA_CANNON_ASCII = [
    '__________        __  .__                _________                                     ',
    '\\______   \\ _____/  |_|__| ____ _____    \\_   ___ \\_____    ____   ____   ____   ____  ',
    ' |       _// __ \\   __\\  |/    \\\\__  \\   /    \\  \\/\\__  \\  /    \\ /    \\ /  _ \\ /    \\ ',
    ' |    |   \\  ___/|  | |  |   |  \\/ __ \\_ \\     \\____/ __ \\|   |  \\   |  (  <_> )   |  \\',
    ' |____|_  /\\___  >__| |__|___|  (____  /  \\______  (____  /___|  /___|  /\\____/|___|  /',
    '        \\/     \\/             \\/     \\/          \\/     \\/     \\/     \\/            \\/ ',
]

def _sys_stat():
    s = {}
    try:
        s['host'] = open('/etc/hostname').read().strip()
    except Exception:
        pass
    try:
        raw = subprocess.check_output(['vcgencmd', 'measure_temp'], text=True, timeout=1)
        s['temp'] = raw.strip().replace('temp=', '')
    except Exception:
        pass
    try:
        mem = {}
        for line in open('/proc/meminfo'):
            k, v = line.split(':', 1)
            mem[k.strip()] = int(v.split()[0])
        s['ram_free'] = mem.get('MemAvailable', 0) // 1024
        s['ram_total'] = mem.get('MemTotal', 0) // 1024
    except Exception:
        pass
    try:
        secs = float(open('/proc/uptime').read().split()[0])
        h, m = int(secs // 3600), int((secs % 3600) // 60)
        s['uptime'] = f'{h}h {m:02d}m' if h else f'{m}m'
    except Exception:
        pass
    return s

def _corrupt_line(line, amount):
    chars = list(line)
    indices = [i for i, c in enumerate(chars) if c not in (' ', '\\')]
    n = int(len(indices) * amount)
    for i in random.sample(indices, min(n, len(indices))):
        chars[i] = random.choice(_BLOCK_CHARS)
    return ''.join(chars)

def _styled(text, color='', bold=False, dim=False):
    style = ''
    if bold:
        style += ANSI_BOLD
    if dim:
        style += ANSI_DIM
    style += color
    return f'{style}{text}{ANSI_RESET}' if style else text

def _term_size():
    return shutil.get_terminal_size(fallback=(100, 30))

def _center_text_line(line, width):
    if len(line) >= width:
        return line
    return (' ' * ((width - len(line)) // 2)) + line

def _vhs_rainbow_line(line, phase=0):
    out = []
    for i, ch in enumerate(line):
        if ch == ' ':
            out.append(' ')
            continue
        color = ANSI_VHS_RAINBOW[(i + phase) % len(ANSI_VHS_RAINBOW)]
        out.append(f'{color}{ch}{ANSI_RESET}')
    return ''.join(out)

def _clear_to_black():
    # Full clear + cursor home + hide cursor to make splash look intentional.
    print('\033[2J\033[H\033[?25l', end='', flush=True)

def _show_cursor():
    print('\033[?25h', end='', flush=True)

def _max_line_width(lines):
    return max((len(ln) for ln in lines), default=0)

def _figlet_title_lines(max_width=None):
    figlet_bin = shutil.which('figlet')
    best = None
    if figlet_bin:
        local_font_dir = RETINA_DIR / 'fonts'
        local_candidates = (
            ('Slant Relief', str(local_font_dir)),
            ('slantrelief', str(local_font_dir)),
        )
        system_candidates = (
            ('slantrelief', None),
            ('slant', None),
            ('standard', None),
            ('small', None),
            ('mini', None),
        )
        for font, font_dir in (local_candidates + system_candidates):
            try:
                cmd = [figlet_bin]
                if font_dir:
                    cmd += ['-d', font_dir]
                # Force wide render to prevent figlet's default 80-col wrapping.
                cmd += ['-w', '1000', '-f', font, 'Retina Cannon']
                out = subprocess.check_output(cmd, text=True, timeout=2.0)
                lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]
                if lines:
                    width = _max_line_width(lines)
                    if max_width is None or width <= max_width:
                        return lines
                    if best is None or width < _max_line_width(best):
                        best = lines
            except Exception:
                continue
    if best is not None:
        return best
    if max_width is None or _max_line_width(RETINA_CANNON_ASCII) <= max_width:
        return RETINA_CANNON_ASCII
    if len('RETINA CANNON') <= max_width:
        return ['RETINA CANNON']
    return RETINA_CANNON_ASCII

def _lolcat_py(text, freq=0.07, spread=3.0):
    """Pure-Python lolcat: smooth rainbow via 24-bit RGB ANSI codes (sine waves)."""
    seed = random.uniform(0, 255)
    out = []
    char_i = 0
    for line_i, line in enumerate(text.splitlines(keepends=True)):
        for ch in line:
            if ch == '\n':
                out.append(ch)
                continue
            x = seed + line_i / spread + char_i * freq
            r = int(math.sin(x + 0.000) * 127 + 128)
            g = int(math.sin(x + 2.094) * 127 + 128)  # 2π/3
            b = int(math.sin(x + 4.189) * 127 + 128)  # 4π/3
            out.append(f'\033[38;2;{r};{g};{b}m{ch}\033[0m')
            char_i += 1
    return ''.join(out)

def _lolcat_colorize(text):
    lolcat_bin = shutil.which('lolcat')
    if not lolcat_bin and os.path.isfile('/usr/games/lolcat'):
        lolcat_bin = '/usr/games/lolcat'
    if lolcat_bin:
        try:
            return subprocess.check_output(
                [lolcat_bin, '-f'],
                input=text,
                text=True,
                timeout=2.0,
            )
        except Exception:
            pass
    return _lolcat_py(text)

def _print_centered_lolcat_line(text, cols, fallback_color=ANSI_CYAN, dim=True):
    centered = _center_text_line(text, cols)
    colored = _lolcat_colorize(centered + '\n')
    if colored is not None:
        print(colored, end='')
    else:
        print(_styled(centered, fallback_color, dim=dim))

def _countdown_progress_line(current, start, cols):
    nums = list(range(start, -1, -1))
    plain = ' - '.join(str(v) for v in nums)
    pad = ' ' * max((cols - len(plain)) // 2, 0)
    gray_scale = [
        '\033[38;5;240m',  # dark gray
        '\033[38;5;244m',  # medium gray
        '\033[38;5;248m',  # light gray
        '\033[37m',        # white
    ]
    parts = []
    for i, v in enumerate(nums):
        if i > 0:
            parts.append(_styled('-', ANSI_DIM))
        if v > current:
            done = (start - v + 1)
            ratio = done / float(max(start, 1))
            idx = min(len(gray_scale) - 1, int(ratio * len(gray_scale)))
            parts.append(_styled(str(v), gray_scale[idx], bold=True))
        elif v == current:
            parts.append(_styled(str(v), '\033[38;5;252m', bold=True))
        else:
            parts.append(_styled(str(v), '\033[38;5;236m'))
    return pad + ' '.join(parts)

def _print_centered_title(title_lines, cols, phase=0):
    centered = [_center_text_line(ln, cols) for ln in title_lines]
    plain = '\n'.join(centered) + '\n'
    colored = _lolcat_colorize(plain)
    if colored is not None:
        print(colored, end='')
        return
    for ln in centered:
        print(_vhs_rainbow_line(ln, phase), flush=True)

def _wait_splash_release():
    # Optional hold mode: wait on /dev/tty so boot can be staged manually.
    try:
        fd = os.open('/dev/tty', os.O_RDONLY)
    except OSError:
        time.sleep(3.0)
        return
    old = None
    try:
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] &= ~(termios.ICANON | termios.ECHO)
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        os.read(fd, 1)
    finally:
        if old is not None:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except Exception:
                pass
        os.close(fd)

def _print_static_splash_frame(title, cols, base, credit_a, credit_b, quote, phase):
    _clear_to_black()
    print(base, end='')
    _print_centered_title(title, cols, phase=phase)
    print()
    print(_styled(_center_text_line(credit_a, cols), ANSI_WHITE, dim=True))
    print(_styled(_center_text_line(credit_b, cols), ANSI_DIM))
    print()
    print()
    _print_centered_lolcat_line(quote, cols, fallback_color=ANSI_CYAN, dim=True)
    print()

# ── NFO/warez box helpers ────────────────────────────────────────────────────

def _nfo_top(box_w):
    return _styled('╔' + '═' * (box_w - 2) + '╗', ANSI_ELEC_CYAN, bold=True)

def _nfo_sep(box_w):
    return _styled('╠' + '═' * (box_w - 2) + '╣', ANSI_ELEC_CYAN, bold=True)

def _nfo_bot(box_w):
    return _styled('╚' + '═' * (box_w - 2) + '╝', ANSI_ELEC_CYAN, bold=True)

def _nfo_box_line(content, box_w):
    """Wrap a content string (may contain ANSI) in ║ … ║, padding to box_w."""
    inner_w = box_w - 4  # 2 border chars + 2 space margins
    vis = _visible_len(content)
    pad = max(0, inner_w - vis)
    wall = _styled('║', ANSI_ELEC_CYAN, bold=True)
    return wall + ' ' + content + ' ' * pad + ' ' + wall

def _nfo_meta_line(la, va, lb, vb, box_w):
    """Two-column metadata row: LA : VA     LB : VB"""
    sep = _styled(' : ', ANSI_DIM)
    left  = _styled(la, ANSI_CYAN_DIM) + sep + _styled(va, ANSI_WHITE, bold=True)
    right = _styled(lb, ANSI_CYAN_DIM) + sep + _styled(vb, ANSI_WHITE, bold=True)
    inner_w = box_w - 4
    gap = max(1, inner_w - _visible_len(left) - _visible_len(right))
    return _nfo_box_line(left + ' ' * gap + right, box_w)

def _nfo_status_line(label, box_w):
    """>> label .........[OK]"""
    ok     = _styled('[OK]', ANSI_BRIGHT_GREEN, bold=True)
    prefix = _styled('>>', ANSI_YELLOW) + ' ' + _styled(label, ANSI_WHITE) + ' '
    inner_w = box_w - 4
    dots = max(1, inner_w - _visible_len(prefix) - _visible_len(ok))
    return _nfo_box_line(prefix + _styled('.' * dots, ANSI_DIM) + ok, box_w)

def _nfo_progress_line(n, max_n, cols):
    """LAUNCHING IN N  ████░░░ — returned as string for \\r rewrite."""
    label  = _styled(f'  LAUNCHING IN {n}  ', ANSI_YELLOW, bold=True)
    bar_w  = max(10, cols - _visible_len(label) - 4)
    filled = round(bar_w * (max_n - n) / max(max_n, 1))
    empty  = bar_w - filled
    bar = _styled('█' * filled, ANSI_BRIGHT_GREEN) + _styled('░' * empty, ANSI_DARK_GRAY)
    return label + bar

def _print_nfo_static(box_w, cols):
    """Print the static NFO box — title lives above, quote lives below (caller handles it)."""
    margin = ' ' * max(0, (cols - box_w) // 2)

    def pline(s):
        print(margin + s)

    # Box: top → 3 meta rows → sep → 5 status rows → bot
    pline(_nfo_top(box_w))

    pline(_nfo_meta_line('GRP',  'Netmilk Studio sagl',        'REL',  'v3.0 [FINAL]',                       box_w))
    pline(_nfo_meta_line('TYPE', 'Realtime GLSL Engine',        'DATE', datetime.now().strftime('%Y-%m-%d'),   box_w))
    pline(_nfo_meta_line('PLAT', 'Raspberry Pi / kms-glsl',     'EFXS', f'{len(EFFECT_MODE_NAMES)} x .frag',  box_w))

    pline(_nfo_sep(box_w))

    pline(_nfo_status_line('Acquiring DRM master',               box_w))
    pline(_nfo_status_line('Loading GLSL pipeline',              box_w))
    pline(_nfo_status_line(f'Calibrating Pi camera ({CAM_W}\u00d7{CAM_H})', box_w))
    pline(_nfo_status_line('Motion detection warmup',            box_w))
    pline(_nfo_status_line('Keyboard controller ready',          box_w))

    pline(_nfo_bot(box_w))

def _print_vhs_splash(countdown_seconds):
    cols, rows = _term_size()

    # Narrow terminal fallback → centered old-style splash
    if cols < 56:
        title = _figlet_title_lines(max_width=max(16, cols - 2))
        quote = random.choice(_BOOT_LINES)
        base = '\n' * max((rows - len(title) - 5) // 2, 1)
        _print_static_splash_frame(title, cols, base, 'Netmilk Studio sagl',
                                   'Retina Cannon', quote, 12)
        if countdown_seconds >= 0:
            start = max(1, int(countdown_seconds))
            for n in range(start, -1, -1):
                print('\r' + _countdown_progress_line(n, start, cols) + '\033[K',
                      end='', flush=True)
                time.sleep(1.0)
            print()
        _clear_to_black()
        _show_cursor()
        return

    # Wide terminal: figlet title FULL WIDTH above box, not inside
    box_w = min(cols, 80)
    title = _figlet_title_lines(max_width=cols)   # full terminal width
    quote = random.choice(_BOOT_LINES)

    title_h = len(title)
    # box=11, blank_above_quote=1, quote=1, blank_below_quote=1, countdown=1
    content_h = title_h + 1 + 11 + 1 + 1 + 1 + 1
    top_pad = max(1, (rows - content_h) // 2)

    _clear_to_black()
    print('\n' * top_pad, end='')
    _print_centered_title(title, cols)
    print()
    _print_nfo_static(box_w, cols)

    # Centered quote — glows from dark gray to bright white
    quote_short = quote[:cols - 4] if len(quote) > cols - 4 else quote
    centered_q = _center_text_line('\u201c' + quote_short + '\u201d', cols)
    _glow = ['\033[38;5;238m', '\033[38;5;243m', '\033[38;5;248m', '\033[38;5;253m', '\033[1;97m']
    print()   # blank line above quote
    print(_glow[0] + centered_q + ANSI_RESET, flush=True)
    for _gc in _glow[1:]:
        time.sleep(0.08)
        print('\033[1A\r' + _gc + centered_q + ANSI_RESET + '\033[K', flush=True)
    print()   # blank line below quote (spacing before countdown)

    if countdown_seconds < 0:
        print(_styled('  >> HOLD — press any key to continue', ANSI_YELLOW, bold=True))
        _wait_splash_release()
    else:
        start = max(1, int(countdown_seconds))
        bar_w = min(cols * 30 // 100, 40)
        for n in range(start, -1, -1):
            label = f'LAUNCHING IN {n} '
            filled = round(bar_w * (start - n) / max(start, 1))
            empty = bar_w - filled
            bar_str = _styled('█' * filled, ANSI_BRIGHT_GREEN) + _styled('░' * empty, ANSI_DARK_GRAY)
            content_str = _styled(label, ANSI_YELLOW, bold=True) + bar_str
            content_vis_w = len(label) + bar_w
            margin = ' ' * max(0, (cols - content_vis_w) // 2)
            print('\r' + margin + content_str + '\033[K', end='', flush=True)
            time.sleep(1.0)
        print()

    _clear_to_black()
    _show_cursor()

def _print_retina_logo(offset=0):
    cols, _ = _term_size()
    lines = _figlet_title_lines(max_width=max(16, cols - 2))
    plain = '\n'.join(lines) + '\n'
    colored = _lolcat_colorize(plain)
    if colored is not None:
        print(colored, end='')
    else:
        for i, line in enumerate(lines):
            color = ANSI_RAINBOW[(i + offset) % len(ANSI_RAINBOW)]
            print(_styled(line, color, bold=True))
    print(_styled('Copyright (c) Netmilk Studio sagl', ANSI_WHITE, dim=True))
    print(_styled('Licensed under the MIT License', ANSI_WHITE, dim=True))

def _detach_stdin_from_renderer():
    # kms-glsl treats any readable stdin as "user interrupted".
    # Keep fd 0 on an idle pipe and read controls from /dev/tty instead.
    global _quiet_stdin_w
    rfd, wfd = os.pipe()
    os.dup2(rfd, 0)
    os.close(rfd)
    _quiet_stdin_w = wfd

def _request_renderer_stop():
    # Prefer graceful stop through renderer stdin poll; fallback to pthread cancel.
    if _quiet_stdin_w is not None:
        try:
            os.write(_quiet_stdin_w, b'\n')
            return
        except OSError:
            pass
    glsl.stop()

def _color_mode_name():
    if current_effect_mode == 0:   return RUTT_COLOR_MODE_NAMES[current_rutt_color_mode]
    if current_effect_mode == 1:   return ASCII_COLOR_MODE_NAMES[current_ascii_color_mode]
    if current_effect_mode == 2:   return PIXELART_COLOR_MODE_NAMES[current_pixelart_color_mode]
    if current_effect_mode == 3:   return RASTER_COLOR_MODE_NAMES[current_raster_color_mode]
    if current_effect_mode == 4:   return DATAMOSH_COLOR_MODE_NAMES[current_datamosh_color_mode]
    if current_effect_mode == 5:   return VHSBURN_COLOR_MODE_NAMES[current_vhsburn_color_mode]
    if current_effect_mode == 6:   return POSTER_COLOR_MODE_NAMES[current_poster_color_mode]
    if current_effect_mode == 7:   return LENSDOT_COLOR_MODE_NAMES[current_lensdot_color_mode]
    if current_effect_mode == 8:   return MIRRORZOOM_COLOR_MODE_NAMES[current_mirrorzoom_color_mode]
    if current_effect_mode == 9:   return CHROMATRAIL_COLOR_MODE_NAMES[current_chromatrail_color_mode]
    return PROFILESCOPE_COLOR_MODE_NAMES[current_profilescope_color_mode]

def _active_color_mode():
    if current_effect_mode == 0:   return current_rutt_color_mode
    if current_effect_mode == 1:   return current_ascii_color_mode
    if current_effect_mode == 2:   return current_pixelart_color_mode
    if current_effect_mode == 3:   return current_raster_color_mode
    if current_effect_mode == 4:   return current_datamosh_color_mode
    if current_effect_mode == 5:   return current_vhsburn_color_mode
    if current_effect_mode == 6:   return current_poster_color_mode
    if current_effect_mode == 7:   return current_lensdot_color_mode
    if current_effect_mode == 8:   return current_mirrorzoom_color_mode
    if current_effect_mode == 9:   return current_chromatrail_color_mode
    return current_profilescope_color_mode

# Remap Python color-mode index → shader uColorMode value.
# Python arrays are ordered for user-facing logic (first = default at launch).
# The shader was written with a different index order; this table keeps the
# GLSL untouched while letting Python own the canonical order.
_SHADER_COLOR_REMAP = {
    0: [2, 1, 0, 5], # Rutt: Prism Warp(→2), Phosphor(→1), Wire Mono(→0), v002 Terrain(→5)
    2: [1, 0, 2],          # Pixel Art: Game Boy(→1), Pixel Native(→0), Toxic Candy(→2)
}

def _shader_color_mode():
    """Return the uColorMode value to send to the shader."""
    cm = _active_color_mode()
    remap = _SHADER_COLOR_REMAP.get(current_effect_mode)
    if remap and cm < len(remap):
        return remap[cm]
    return cm

def _effect_code():
    return f'{current_effect_mode:02d}'

def _subeffect_code(mode=None):
    m = _active_color_mode() if mode is None else int(mode)
    return f'{current_effect_mode:02d}.{m + 1:02d}'

def _effect_display_name():
    return f'{_effect_code()} {EFFECT_MODE_NAMES[current_effect_mode]}'

def _subeffect_display_name(mode=None):
    return f'{_subeffect_code(mode)} {_color_mode_name()}'

def _active_color_mode_count():
    if current_effect_mode == 0:   return len(RUTT_COLOR_MODE_NAMES)
    if current_effect_mode == 1:   return len(ASCII_COLOR_MODE_NAMES)
    if current_effect_mode == 2:   return len(PIXELART_COLOR_MODE_NAMES)
    if current_effect_mode == 3:   return len(RASTER_COLOR_MODE_NAMES)
    if current_effect_mode == 4:   return len(DATAMOSH_COLOR_MODE_NAMES)
    if current_effect_mode == 5:   return len(VHSBURN_COLOR_MODE_NAMES)
    if current_effect_mode == 6:   return len(POSTER_COLOR_MODE_NAMES)
    if current_effect_mode == 7:   return len(LENSDOT_COLOR_MODE_NAMES)
    if current_effect_mode == 8:   return len(MIRRORZOOM_COLOR_MODE_NAMES)
    if current_effect_mode == 9:   return len(CHROMATRAIL_COLOR_MODE_NAMES)
    return len(PROFILESCOPE_COLOR_MODE_NAMES)

def _set_active_color_mode(mode):
    global current_rutt_color_mode, current_ascii_color_mode, current_pixelart_size
    global current_pixelart_color_mode, current_raster_color_mode
    global current_datamosh_color_mode, current_vhsburn_color_mode, current_poster_color_mode
    global current_lensdot_color_mode, current_mirrorzoom_color_mode
    global current_chromatrail_color_mode, current_profilescope_color_mode
    if current_effect_mode == 0:   current_rutt_color_mode        = mode % len(RUTT_COLOR_MODE_NAMES)
    elif current_effect_mode == 1: current_ascii_color_mode       = mode % len(ASCII_COLOR_MODE_NAMES)
    elif current_effect_mode == 2:
        current_pixelart_color_mode = mode % len(PIXELART_COLOR_MODE_NAMES)
        current_pixelart_size = PIXELART_MODE_DEFAULT_SIZES[current_pixelart_color_mode]
    elif current_effect_mode == 3: current_raster_color_mode       = mode % len(RASTER_COLOR_MODE_NAMES)
    elif current_effect_mode == 4: current_datamosh_color_mode     = mode % len(DATAMOSH_COLOR_MODE_NAMES)
    elif current_effect_mode == 5: current_vhsburn_color_mode      = mode % len(VHSBURN_COLOR_MODE_NAMES)
    elif current_effect_mode == 6: current_poster_color_mode       = mode % len(POSTER_COLOR_MODE_NAMES)
    elif current_effect_mode == 7: current_lensdot_color_mode      = mode % len(LENSDOT_COLOR_MODE_NAMES)
    elif current_effect_mode == 8: current_mirrorzoom_color_mode   = mode % len(MIRRORZOOM_COLOR_MODE_NAMES)
    elif current_effect_mode == 9: current_chromatrail_color_mode  = mode % len(CHROMATRAIL_COLOR_MODE_NAMES)
    else:                          current_profilescope_color_mode  = mode % len(PROFILESCOPE_COLOR_MODE_NAMES)

def _cycle_active_color_mode(step):
    _set_active_color_mode(_active_color_mode() + step)
    print(f'\r[COLOR {_subeffect_code()}/{_active_color_mode_count():02d}] {_color_mode_name()} | {_effect_param_label()}        ')

def _effect_param_label():
    if current_effect_mode == 0:
        w = f'Wave {current_rutt_wave:.2f}x'
        if current_rutt_color_mode == 0:
            return f'[PRISM WARP] {w} | Split {current_rutt_prismwarp_split:.1f}x'
        if current_rutt_color_mode == 1:
            tname = 'Cyan' if current_rutt_phosphor_tint < 0.8 else ('Amber' if current_rutt_phosphor_tint > 1.3 else 'Green')
            return f'[PHOSPHOR] {w} | Tint {tname} {current_rutt_phosphor_tint:.1f}'
        if current_rutt_color_mode == 2:
            return f'[WIRE MONO] {w} | Contrast {current_rutt_wiremono_contrast:.1f}x'
        if current_rutt_color_mode == 3:
            return f'[TERRAIN] {w} | Interf {current_terrain_amp:.2f}x'
        return f'[RUTT] {w}'
    if current_effect_mode == 1:   return f'[ASCII] Density {current_ascii_density:.2f}x | Contrast {current_ascii_contrast:.2f}'
    if current_effect_mode == 2:   return f'[PIXEL] Block {int(current_pixelart_size)}px'
    if current_effect_mode == 3:   return f'[RASTER] Dot {int(current_raster_size)}px'
    if current_effect_mode == 4:   return f'[CODEC] Amount {current_datamosh_amount:.2f}x'
    if current_effect_mode == 5:   return f'[VHS] Tracking {current_vhs_tracking:.2f}x'
    if current_effect_mode == 6:   return f'[POSTER] Levels {int(current_poster_levels)}'
    if current_effect_mode == 7:   return f'[DOT] Detail {current_lensdot_detail:.2f}x'
    if current_effect_mode == 8:   return f'[MIRROR] Zoom {current_mirrorzoom_amount:.2f}x'
    if current_effect_mode == 9:   return f'[TRAIL] Intensity {current_chromatrail_intensity:.2f}x'
    return f'[SCOPE] Grid {current_profilescope_grid:.2f}x'

def _slugify(text):
    s = ''.join(ch.lower() if ch.isalnum() else '-' for ch in text)
    while '--' in s:
        s = s.replace('--', '-')
    s = s.strip('-')
    return s or 'mode'

def _save_screenshot_now():
    if _render_w <= 0 or _render_h <= 0:
        print('\r[SHOT] Failed: render size unavailable        ')
        return

    out_dir = RETINA_DIR / 'shots'
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    effect = f'{_effect_code()}-{_slugify(EFFECT_MODE_NAMES[current_effect_mode])}'
    variant = f'{_subeffect_code().replace(".", "-")}-{_slugify(_color_mode_name())}'
    view = _slugify(VIEW_MODE_NAMES[current_view_mode])
    mirror = 'mirror-on' if current_mirror_view else 'mirror-off'
    png_path = out_dir / f'{stamp}_{effect}_{variant}_{view}_{mirror}.png'

    # onRender is invoked before the engine draw. Force a one-off draw here
    # so glReadPixels captures a real rendered frame, not an empty backbuffer.
    try:
        glsl.glDrawArrays(GL_TRIANGLES, 0, 6)
    except Exception:
        pass
    try:
        glsl.glFinish()
    except Exception:
        pass
    try:
        glsl.glPixelStorei(GL_PACK_ALIGNMENT, 1)
    except Exception:
        pass

    pixels = (ctypes.c_ubyte * (_render_w * _render_h * 4))()
    glsl.glReadPixels(0, 0, _render_w, _render_h, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
    if glsl.glGetError() != GL_NO_ERROR:
        print('\r[SHOT] Failed: glReadPixels error        ')
        return

    rgba = np.ctypeslib.as_array(pixels).reshape((_render_h, _render_w, 4))
    frame = np.flipud(rgba[:, :, :3]).copy()

    if Image is not None:
        Image.fromarray(frame, 'RGB').save(str(png_path), format='PNG')
        print(f'\r[SHOT] Saved {png_path}        ')
        return

    ppm_path = png_path.with_suffix('.ppm')
    with open(ppm_path, 'wb') as f:
        f.write(f'P6\n{_render_w} {_render_h}\n255\n'.encode('ascii'))
        f.write(frame.tobytes())
    print(f'\r[SHOT] Saved {ppm_path} (Pillow missing)        ')

def _tick_screenshot_countdown():
    global _shot_deadline, _shot_last_seconds
    if _shot_deadline is None:
        return

    rem = _shot_deadline - time.monotonic()
    if rem <= 0.0:
        _shot_deadline = None
        _shot_last_seconds = None
        _save_screenshot_now()
        return

    secs = int(math.ceil(rem))
    if _shot_last_seconds != secs:
        _shot_last_seconds = secs
        print(f'\r[SHOT] {secs}...        ')

def _toggle_fps_logging():
    global current_show_fps, _fps_last_report_time
    current_show_fps = 0 if current_show_fps else 1
    _fps_last_report_time = None
    if current_show_fps:
        print(f'\r{_styled("[FPS]", ANSI_CYAN, bold=True)} LOG ON (terminal only)        ')
    else:
        print(f'\r{_styled("[FPS]", ANSI_CYAN, bold=True)} LOG OFF        ')

def _print_startup_banner():
    global _session_start
    _session_start = time.time()
    _print_vhs_splash(_splash_seconds)
    print()

    # System stats
    st = _sys_stat()
    sep = _styled('  ' + '·' * 48, ANSI_DIM)

    def stat_row(label, value, vcolor=ANSI_WHITE):
        dots = _styled('.' * (16 - len(label)), ANSI_DIM)
        return f'  {_styled(label, ANSI_CYAN)}{dots} {_styled(value, vcolor, bold=True)}'

    print(_styled('  ╔══ SYSTEM STATUS ' + '═' * 33 + '╗', ANSI_MAGENTA, bold=True))
    if 'host'     in st: print(stat_row('Host',    st["host"]))
    if 'temp'     in st:
        temp_c = float(st['temp'].replace("'C", ""))
        tc = ANSI_RED if temp_c > 70 else ANSI_YELLOW if temp_c > 55 else ANSI_GREEN
        print(stat_row('SoC temp', st['temp'], vcolor=tc))
    if 'ram_free' in st: print(stat_row('RAM free', f"{st['ram_free']} MB / {st['ram_total']} MB"))
    if 'uptime'   in st: print(stat_row('Uptime',  st['uptime']))
    print(stat_row('Camera',   f'{CAM_W} × {CAM_H} BGR888'))
    print(stat_row('Shader',   _shader_name or 'rutt_etra.frag'))
    print(stat_row('Effect',   f'{_effect_display_name()} · {_subeffect_display_name()}'))
    print(_styled('  ╚' + '═' * 51 + '╝', ANSI_MAGENTA, bold=True))
    print()

    # Random startup line
    line = random.choice(_BOOT_LINES)
    print(f'  {_styled(line, ANSI_DIM)}')
    print()

    print(f'  {_styled("↑↓", ANSI_CYAN, bold=True)} color  '
          f'{_styled("←→", ANSI_CYAN, bold=True)} wave/density  '
          f'{_styled("Space", ANSI_CYAN, bold=True)} effect  '
          f'{_styled("S", ANSI_CYAN, bold=True)} screenshot  '
          f'{_styled("V", ANSI_CYAN, bold=True)} view  '
          f'{_styled("M", ANSI_CYAN, bold=True)} mirror  '
          f'{_styled("F", ANSI_CYAN, bold=True)} fps  '
          f'{_styled("Ctrl+C", ANSI_CYAN, bold=True)} quit')
    print(_styled('  ' + '─' * 51, ANSI_DIM))

def _print_shutdown_banner(reason):
    print()
    _print_retina_logo(offset=3)
    print()

    # Session stats
    if _session_start is not None:
        elapsed = time.time() - _session_start
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        duration = f'{mins}m {secs:02d}s'
        est_frames = int(elapsed * max(_fps_smoothed, 0))
        print(f'  {_styled("Session", ANSI_DIM)} {_styled(duration, ANSI_WHITE, bold=True)}'
              f'  {_styled("  Frames ~", ANSI_DIM)}{_styled(str(est_frames), ANSI_WHITE, bold=True)}'
              f'  {_styled("  Avg FPS ~", ANSI_DIM)}{_styled(f"{_fps_smoothed:.1f}", ANSI_WHITE, bold=True)}')
        print()
    if _bench_seconds > 0.0:
        print(f'  [BENCH_RESULT] effect={_effect_code()} name="{EFFECT_MODE_NAMES[current_effect_mode]}" subeffect={_subeffect_code()} variant="{_color_mode_name()}" avg_fps={_fps_smoothed:.2f}')
        print()

    line = random.choice(_SHUTDOWN_LINES)
    colored_line = _lolcat_colorize(line + '\n')
    def _print_shutdown_line(bullet_color):
        bullet = _styled('▶', bullet_color, bold=True)
        if colored_line is not None:
            print(f'  {bullet} {colored_line}', end='')
        else:
            print(f'  {bullet} {_styled(line, ANSI_WHITE, bold=True)}')
    if reason.startswith('init_error') or reason.startswith('run_error'):
        print(f'  {_styled("▶", ANSI_RED, bold=True)} {_styled(f"Renderer error: {reason}", ANSI_RED)}')
        _print_shutdown_line(ANSI_MAGENTA)
    elif reason in ('ctrl_c', 'signal'):
        _print_shutdown_line(ANSI_CYAN)
    else:
        _print_shutdown_line(ANSI_GREEN)

    print(_styled('  ' + '─' * 51, ANSI_DIM))
    print()

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, tex_prev_id, loc_channel0, loc_channel1, loc_color_mode, loc_rutt_wave, loc_ascii_density
    global loc_effect_mode, loc_view_mode, loc_mirror, loc_camera_aspect, loc_pixelart_size
    global loc_motion_level, loc_presence_scale, loc_presence_cx, loc_presence_cy
    global _render_w, _render_h

    _render_w = int(width)
    _render_h = int(height)

    loc_color_mode = glsl.glGetUniformLocation(program, b'uColorMode')
    loc_rutt_wave = glsl.glGetUniformLocation(program, b'uRuttWave')
    loc_ascii_density = glsl.glGetUniformLocation(program, b'uAsciiDensity')
    loc_effect_mode = glsl.glGetUniformLocation(program, b'uEffectMode')
    loc_view_mode = glsl.glGetUniformLocation(program, b'uViewMode')
    loc_mirror = glsl.glGetUniformLocation(program, b'uMirror')
    loc_camera_aspect = glsl.glGetUniformLocation(program, b'uCameraAspect')
    loc_pixelart_size   = glsl.glGetUniformLocation(program, b'uPixelSize')
    loc_motion_level    = glsl.glGetUniformLocation(program, b'uMotionLevel')
    loc_presence_scale  = glsl.glGetUniformLocation(program, b'uPresenceScale')
    loc_presence_cx     = glsl.glGetUniformLocation(program, b'uPresenceCX')
    loc_presence_cy     = glsl.glGetUniformLocation(program, b'uPresenceCY')

    # Create the current camera texture.
    tid = c_uint(0)
    glsl.glGenTextures(1, ctypes.byref(tid))
    tex_id = tid.value

    glsl.glActiveTexture(GL_TEXTURE0)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_id)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    empty = (ctypes.c_ubyte * (CAM_W * CAM_H * 3))()
    glsl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, CAM_W, CAM_H, 0,
                      GL_RGB, GL_UNSIGNED_BYTE, empty)

    # Create the previous-frame texture (for temporal effects).
    tid_prev = c_uint(0)
    glsl.glGenTextures(1, ctypes.byref(tid_prev))
    tex_prev_id = tid_prev.value
    glsl.glActiveTexture(GL_TEXTURE1)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_prev_id)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glsl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glsl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, CAM_W, CAM_H, 0,
                      GL_RGB, GL_UNSIGNED_BYTE, empty)

    loc_channel0 = glsl.glGetUniformLocation(program, b'iChannel0')
    loc_channel1 = glsl.glGetUniformLocation(program, b'iChannel1')
    if loc_channel0 >= 0:
        glsl.glUniform1i(loc_channel0, 0)
    if loc_channel1 >= 0:
        glsl.glUniform1i(loc_channel1, 1)
    if loc_color_mode >= 0:
        glsl.glUniform1i(loc_color_mode, _shader_color_mode())
    if loc_rutt_wave >= 0:
        glsl.glUniform1f(loc_rutt_wave, c_float(current_rutt_wave))
    if loc_ascii_density >= 0:
        glsl.glUniform1f(loc_ascii_density, c_float(current_ascii_density))
    if loc_effect_mode >= 0:
        glsl.glUniform1i(loc_effect_mode, current_effect_mode)
    if loc_view_mode >= 0:
        glsl.glUniform1i(loc_view_mode, current_view_mode)
    if loc_mirror >= 0:
        glsl.glUniform1i(loc_mirror, current_mirror_view)
    if loc_camera_aspect >= 0:
        glsl.glUniform1f(loc_camera_aspect, c_float(CAM_W / CAM_H))
    if loc_pixelart_size >= 0:
        _ps = current_raster_size if current_effect_mode == 3 else current_pixelart_size
        glsl.glUniform1f(loc_pixelart_size, c_float(_ps))

    print(f'[GL] textures current={tex_id} prev={tex_prev_id} ready, loc_channel0={loc_channel0}, loc_channel1={loc_channel1}')

@CFUNCTYPE(None, c_uint64, c_float)
def on_render(frame, time):
    global _fps_last_frame, _fps_last_time, _fps_smoothed, _fps_last_report_time
    global _prev_frame_for_shader, _prev_frame_lag_counter
    with _lock:
        f = _frame

    need_delta_prev = (current_effect_mode == 7 and current_lensdot_color_mode == 7)
    if need_delta_prev:
        if _prev_frame_for_shader is None or _prev_frame_for_shader.shape != f.shape:
            _prev_frame_for_shader = f.copy()
            _prev_frame_lag_counter = 0
        prev_frame = _prev_frame_for_shader
    else:
        prev_frame = f

    prev_data = prev_frame.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
    data = f.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))

    glsl.glActiveTexture(GL_TEXTURE1)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_prev_id)
    glsl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, CAM_W, CAM_H,
                         GL_RGB, GL_UNSIGNED_BYTE, prev_data)

    glsl.glActiveTexture(GL_TEXTURE0)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_id)
    glsl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, CAM_W, CAM_H,
                         GL_RGB, GL_UNSIGNED_BYTE, data)
    if need_delta_prev:
        _prev_frame_lag_counter += 1
        # Keep a short temporal gap so camera movement yields a stronger delta signal.
        if _prev_frame_lag_counter >= 3:
            _prev_frame_for_shader = f.copy()
            _prev_frame_lag_counter = 0
    else:
        _prev_frame_for_shader = None
        _prev_frame_lag_counter = 0
    if loc_color_mode >= 0:
        glsl.glUniform1i(loc_color_mode, _shader_color_mode())
    if loc_rutt_wave >= 0:
        _wave = current_ascii_contrast if current_effect_mode == 1 else current_rutt_wave
        glsl.glUniform1f(loc_rutt_wave, c_float(_wave))
    if loc_ascii_density >= 0:
        if current_effect_mode == 0:
            if current_rutt_color_mode == 0:
                _d = current_rutt_prismwarp_split
            elif current_rutt_color_mode == 1:
                _d = current_rutt_phosphor_tint
            elif current_rutt_color_mode == 2:
                _d = current_rutt_wiremono_contrast
            elif current_rutt_color_mode == 3:
                _d = current_terrain_amp
            else:
                _d = 1.0
        elif current_effect_mode == 4:
            _d = current_datamosh_amount
        elif current_effect_mode == 5:
            _d = current_vhs_tracking
        elif current_effect_mode == 6:
            _d = current_poster_levels
        elif current_effect_mode == 7:
            _d = current_lensdot_detail
        elif current_effect_mode == 8:
            _d = current_mirrorzoom_amount
        elif current_effect_mode == 9:
            _d = current_chromatrail_intensity
        elif current_effect_mode == 10:
            _d = current_profilescope_grid
        else:
            _d = current_ascii_density
        glsl.glUniform1f(loc_ascii_density, c_float(_d))
    if loc_effect_mode >= 0:
        glsl.glUniform1i(loc_effect_mode, current_effect_mode)
    if loc_view_mode >= 0:
        glsl.glUniform1i(loc_view_mode, current_view_mode)
    if loc_mirror >= 0:
        glsl.glUniform1i(loc_mirror, current_mirror_view)
    if loc_camera_aspect >= 0:
        glsl.glUniform1f(loc_camera_aspect, c_float(CAM_W / CAM_H))
    if loc_pixelart_size >= 0:
        _ps = current_raster_size if current_effect_mode == 3 else current_pixelart_size
        glsl.glUniform1f(loc_pixelart_size, c_float(_ps))
    if loc_motion_level >= 0:
        glsl.glUniform1f(loc_motion_level, c_float(min(_motion_level, 1.0)))
    if loc_presence_scale >= 0:
        glsl.glUniform1f(loc_presence_scale, c_float(min(_presence_scale, 1.0)))
    if loc_presence_cx >= 0:
        glsl.glUniform1f(loc_presence_cx, c_float(_presence_cx))
    if loc_presence_cy >= 0:
        glsl.glUniform1f(loc_presence_cy, c_float(_presence_cy))
    if _fps_last_time is not None and time > _fps_last_time and frame >= _fps_last_frame:
        dt = time - _fps_last_time
        df = frame - _fps_last_frame
        if dt > 0.0:
            inst = float(df) / float(dt)
            if _fps_smoothed <= 0.0:
                _fps_smoothed = inst
            else:
                _fps_smoothed = _fps_smoothed * 0.86 + inst * 0.14
    _fps_last_frame = frame
    _fps_last_time = time
    if current_show_fps and _fps_smoothed > 0.0:
        if _fps_last_report_time is None or (time - _fps_last_report_time) >= 1.0:
            print(f'\r[FPS] {_fps_smoothed:5.1f} fps | {_effect_display_name()} | {_subeffect_display_name()}        ')
            _fps_last_report_time = time
    if _bench_seconds > 0.0 and time >= _bench_seconds:
        _request_renderer_stop()
    _tick_screenshot_countdown()

glsl.onInit(on_init)
glsl.onRender(on_render)

# ---- Keyboard thread ----
def _read_escape_sequence(fd, max_len=32, timeout=0.08):
    # Collect bytes that follow ESC, including CSI params/modifiers.
    seq = []
    while len(seq) < max_len:
        ready, _, _ = select.select([fd], [], [], timeout)
        if not ready:
            break
        b = os.read(fd, 1)
        if not b:
            break
        ch = b.decode('latin1', errors='ignore')
        seq.append(ch)
        if ch.isalpha() or ch == '~':
            break
    return ''.join(seq)

def _set_keyboard_mode(fd):
    # Keep output processing intact (avoid broken/newline-shifted logs),
    # while reading single keys and escape sequences from the terminal.
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSADRAIN, new)
    return old

def _decode_arrow(seq):
    if not seq:
        return None
    if seq == '[5~':
        return 'page_up'
    if seq == '[6~':
        return 'page_down'
    if seq[0] in ('[', 'O'):
        key = seq[-1]
    else:
        key = next((ch for ch in reversed(seq) if ch in 'ABCD'), None)
        if key is None:
            return None
    return {
        'A': 'up',
        'B': 'down',
        'C': 'right',
        'D': 'left',
    }.get(key)

def keyboard_thread():
    global current_rutt_wave, current_rutt_prismwarp_split, current_rutt_phosphor_tint
    global current_rutt_wiremono_contrast, current_terrain_amp
    global current_ascii_density, current_ascii_contrast, current_pixelart_size
    global current_raster_size
    global current_datamosh_amount, current_vhs_tracking, current_poster_levels
    global current_lensdot_detail, current_mirrorzoom_amount
    global current_chromatrail_intensity, current_profilescope_grid
    global current_effect_mode, current_view_mode, current_mirror_view, _ctrl_c_requested
    global _shot_deadline, _shot_last_seconds
    import termios
    try:
        fd = os.open('/dev/tty', os.O_RDONLY)
    except OSError:
        print('[Controls] /dev/tty unavailable, keyboard controls disabled')
        return
    if not os.isatty(fd):
        os.close(fd)
        print('[Controls] /dev/tty is not a TTY, keyboard controls disabled')
        return
    old = _set_keyboard_mode(fd)
    try:
        while _running:
            ready, _, _ = select.select([fd], [], [], 0.5)
            if not ready:
                continue
            b = os.read(fd, 1)
            if not b:
                continue
            ch = b.decode('latin1', errors='ignore')
            if ch == '\x03':  # Ctrl+C
                _ctrl_c_requested = True
                _request_renderer_stop()
                break
            if ch == ' ':
                current_effect_mode = (current_effect_mode + 1) % len(EFFECT_MODE_NAMES)
                print(f'\r[EFFECT {_effect_code()}] {EFFECT_MODE_NAMES[current_effect_mode]} | [COLOR {_subeffect_code()}/{_active_color_mode_count():02d}] {_color_mode_name()} | {_effect_param_label()}        ')
                continue
            if ch in ('s', 'S'):
                _shot_deadline = time.monotonic() + SHOT_COUNTDOWN_SEC
                _shot_last_seconds = int(SHOT_COUNTDOWN_SEC)
                print(f'\r[SHOT] {int(SHOT_COUNTDOWN_SEC)}...        ')
                continue
            if ch in ('f', 'F'):
                _toggle_fps_logging()
                continue
            if ch in ('v', 'V'):
                current_view_mode = (current_view_mode + 1) % len(VIEW_MODE_NAMES)
                print(f'\r[VIEW] {VIEW_MODE_NAMES[current_view_mode]}        ')
                continue
            if ch in ('m', 'M'):
                current_mirror_view = 0 if current_mirror_view else 1
                print(f'\r[MIRROR] {"ON" if current_mirror_view else "OFF"}        ')
                continue
            if ch == '\x1b':
                seq = _read_escape_sequence(fd)
                direction = _decode_arrow(seq)
                if direction == 'page_up':
                    _cycle_active_color_mode(+1)
                elif direction == 'page_down':
                    _cycle_active_color_mode(-1)
                elif direction == 'up':
                    if current_effect_mode == 0:
                        if current_rutt_color_mode == 0:
                            current_rutt_prismwarp_split = min(RUTT_SPLIT_MAX, current_rutt_prismwarp_split + RUTT_SPLIT_STEP)
                        elif current_rutt_color_mode == 1:
                            current_rutt_phosphor_tint = min(RUTT_PHOSPHOR_MAX, current_rutt_phosphor_tint + RUTT_PHOSPHOR_STEP)
                        elif current_rutt_color_mode == 2:
                            current_rutt_wiremono_contrast = min(RUTT_CONTRAST_MAX, current_rutt_wiremono_contrast + RUTT_CONTRAST_STEP)
                        elif current_rutt_color_mode == 3:
                            current_terrain_amp = min(TERRAIN_AMP_MAX, current_terrain_amp + TERRAIN_AMP_STEP)
                        print(f'\r{_effect_param_label()}        ')
                    elif current_effect_mode == 1:
                        current_ascii_contrast = min(ASCII_CONTRAST_MAX, current_ascii_contrast + ASCII_CONTRAST_STEP)
                        print(f'\r{_effect_param_label()}        ')
                elif direction == 'down':
                    if current_effect_mode == 0:
                        if current_rutt_color_mode == 0:
                            current_rutt_prismwarp_split = max(RUTT_SPLIT_MIN, current_rutt_prismwarp_split - RUTT_SPLIT_STEP)
                        elif current_rutt_color_mode == 1:
                            current_rutt_phosphor_tint = max(RUTT_PHOSPHOR_MIN, current_rutt_phosphor_tint - RUTT_PHOSPHOR_STEP)
                        elif current_rutt_color_mode == 2:
                            current_rutt_wiremono_contrast = max(RUTT_CONTRAST_MIN, current_rutt_wiremono_contrast - RUTT_CONTRAST_STEP)
                        elif current_rutt_color_mode == 3:
                            current_terrain_amp = max(TERRAIN_AMP_MIN, current_terrain_amp - TERRAIN_AMP_STEP)
                        print(f'\r{_effect_param_label()}        ')
                    elif current_effect_mode == 1:
                        current_ascii_contrast = max(ASCII_CONTRAST_MIN, current_ascii_contrast - ASCII_CONTRAST_STEP)
                        print(f'\r{_effect_param_label()}        ')

                elif direction == 'right':
                    if current_effect_mode == 0:
                        current_rutt_wave = min(RUTT_WAVE_MAX, current_rutt_wave + RUTT_WAVE_STEP)
                    elif current_effect_mode == 1:
                        current_ascii_density = min(ASCII_DENSITY_MAX, current_ascii_density + ASCII_DENSITY_STEP)
                    elif current_effect_mode == 2:
                        current_pixelart_size = min(PIXELART_SIZE_MAX, current_pixelart_size + PIXELART_SIZE_STEP)
                    elif current_effect_mode == 3:
                        current_raster_size = min(PIXELART_SIZE_MAX, current_raster_size + PIXELART_SIZE_STEP)
                    elif current_effect_mode == 4:
                        current_datamosh_amount = min(DATAMOSH_AMOUNT_MAX, current_datamosh_amount + DATAMOSH_AMOUNT_STEP)
                    elif current_effect_mode == 5:
                        current_vhs_tracking = min(VHS_TRACK_MAX, current_vhs_tracking + VHS_TRACK_STEP)
                    elif current_effect_mode == 6:
                        current_poster_levels = min(POSTER_LEVEL_MAX, current_poster_levels + POSTER_LEVEL_STEP)
                    elif current_effect_mode == 7:
                        current_lensdot_detail = min(LENSDOT_DETAIL_MAX, current_lensdot_detail + LENSDOT_DETAIL_STEP)
                    elif current_effect_mode == 8:
                        current_mirrorzoom_amount = min(MIRRORZOOM_AMOUNT_MAX, current_mirrorzoom_amount + MIRRORZOOM_AMOUNT_STEP)
                    elif current_effect_mode == 9:
                        current_chromatrail_intensity = min(CHROMATRAIL_INTENSITY_MAX, current_chromatrail_intensity + CHROMATRAIL_INTENSITY_STEP)
                    elif current_effect_mode == 10:
                        current_profilescope_grid = min(PROFILESCOPE_GRID_MAX, current_profilescope_grid + PROFILESCOPE_GRID_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif direction == 'left':
                    if current_effect_mode == 0:
                        current_rutt_wave = max(RUTT_WAVE_MIN, current_rutt_wave - RUTT_WAVE_STEP)
                    elif current_effect_mode == 1:
                        current_ascii_density = max(ASCII_DENSITY_MIN, current_ascii_density - ASCII_DENSITY_STEP)
                    elif current_effect_mode == 2:
                        current_pixelart_size = max(PIXELART_SIZE_MIN, current_pixelart_size - PIXELART_SIZE_STEP)
                    elif current_effect_mode == 3:
                        current_raster_size = max(PIXELART_SIZE_MIN, current_raster_size - PIXELART_SIZE_STEP)
                    elif current_effect_mode == 4:
                        current_datamosh_amount = max(DATAMOSH_AMOUNT_MIN, current_datamosh_amount - DATAMOSH_AMOUNT_STEP)
                    elif current_effect_mode == 5:
                        current_vhs_tracking = max(VHS_TRACK_MIN, current_vhs_tracking - VHS_TRACK_STEP)
                    elif current_effect_mode == 6:
                        current_poster_levels = max(POSTER_LEVEL_MIN, current_poster_levels - POSTER_LEVEL_STEP)
                    elif current_effect_mode == 7:
                        current_lensdot_detail = max(LENSDOT_DETAIL_MIN, current_lensdot_detail - LENSDOT_DETAIL_STEP)
                    elif current_effect_mode == 8:
                        current_mirrorzoom_amount = max(MIRRORZOOM_AMOUNT_MIN, current_mirrorzoom_amount - MIRRORZOOM_AMOUNT_STEP)
                    elif current_effect_mode == 9:
                        current_chromatrail_intensity = max(CHROMATRAIL_INTENSITY_MIN, current_chromatrail_intensity - CHROMATRAIL_INTENSITY_STEP)
                    elif current_effect_mode == 10:
                        current_profilescope_grid = max(PROFILESCOPE_GRID_MIN, current_profilescope_grid - PROFILESCOPE_GRID_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif seq and seq[-1] in ('F', 'f'):
                    # Fallback for terminals that emit ESC...F for this key.
                    _toggle_fps_logging()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        os.close(fd)

_detach_stdin_from_renderer()

# ---- Signal handlers — graceful shutdown from kill/SSH disconnect ----
def _handle_signal(signum, frame):
    global _ctrl_c_requested
    _ctrl_c_requested = True
    _request_renderer_stop()

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGHUP, _handle_signal)

threading.Thread(target=keyboard_thread, daemon=True).start()

# ---- Launch glsl ----
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('shader', nargs='?', default=str(RETINA_DIR / 'rutt_etra.frag'))
parser.add_argument(
    '--splash',
    type=int,
    default=5,
    help='Splash countdown in seconds before render starts (-1 = hold until keypress).',
)
args = parser.parse_args()
_shader_name = Path(args.shader).name
_splash_seconds = int(args.splash)

class FakeArgs:
    shader = [Path(args.shader)]
    async_page_flip = None
    atomic_drm_mode = None
    connector = None
    device = None
    mode = None
    frames = None
    keyboard = None

_print_startup_banner()
if _bench_seconds > 0.0:
    print(f'[BENCH] running effect {_effect_display_name()} ({_subeffect_display_name()}) for {_bench_seconds:.1f}s')
ret = glsl.init(bytes(args.shader, 'utf-8'), byref(options(FakeArgs())))
shutdown_reason = 'normal'
try:
    if ret != 0:
        shutdown_reason = f'init_error:{ret}'
    else:
        ret = glsl.run()
        if ret != 0:
            shutdown_reason = f'run_error:{ret}'
        else:
            try:
                glsl.join()
            except KeyboardInterrupt:
                _ctrl_c_requested = True
                _request_renderer_stop()
                glsl.join()
            if _ctrl_c_requested:
                shutdown_reason = 'ctrl_c'
finally:
    _running = False
    try:
        picam.stop()
        picam.close()
    except Exception:
        pass
    if _quiet_stdin_w is not None:
        os.close(_quiet_stdin_w)
    _print_shutdown_banner(shutdown_reason)

if ret != 0:
    sys.exit(ret)
