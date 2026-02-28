#!/usr/bin/env python
import sys, os, glob, threading, select, termios, signal, subprocess, random, math, shutil
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
tex_unit = 0
loc_channel0 = -1
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
current_rutt_color_mode = 2
current_ascii_color_mode = 0
current_pixelart_color_mode = 1
current_rutt_wave = 0.40
current_ascii_density = 3.00
current_pixelart_size = 16.0
current_ghost_color_mode = 0
current_ghost_density = 2.0
current_raster_color_mode = 0
current_raster_size = 12.0
GHOST_DENSITY_STEP = 0.25
GHOST_DENSITY_MIN = 0.5
GHOST_DENSITY_MAX = 5.0
current_effect_mode = 0
current_view_mode = 0
current_mirror_view = 1
current_show_fps = 0
RUTT_WAVE_STEP = 0.10
RUTT_WAVE_MIN = 0.40
RUTT_WAVE_MAX = 3.80
ASCII_DENSITY_STEP = 0.20
ASCII_DENSITY_MIN = 1.00
ASCII_DENSITY_MAX = 6.00
PIXELART_SIZE_STEP = 2.0
PIXELART_SIZE_MIN = 4.0
PIXELART_SIZE_MAX = 48.0

RUTT_COLOR_MODE_NAMES = ['B/W', 'Colors', 'Prism Warp', 'Acid Melt']
ASCII_COLOR_MODE_NAMES = ['Color symbols', 'Monochrome symbols', 'Inverted mono letters', 'Inverted color letters']
PIXELART_COLOR_MODE_NAMES = [
    'Full Color',
    'Game Boy',
    'CMYK Melt',
    'Toxic Candy',
]
PIXELART_MODE_DEFAULT_SIZES = [12.0, 16.0, 22.0, 8.0]
GHOST_COLOR_MODE_NAMES = ['Void', 'Matrix', 'Ghost Cam', 'Neon', 'Thermal', 'Chromatic']
RASTER_COLOR_MODE_NAMES = ['Thermal Raster', 'Thermal Inverted', 'Comic B/W', 'Comic Pastel', 'Vibrant Pop']
EFFECT_MODE_NAMES = ['Rutt-Etra CRT', 'ASCII Cam', 'Pixel Art', 'Signal Ghost', 'Raster Vision']
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
_render_w = 0
_render_h = 0
_shot_deadline = None
_shot_last_seconds = None
SHOT_COUNTDOWN_SEC = 3.0
_splash_seconds = 10

_BOOT_LINES = [
    'Tracking lock acquired. Keep your face in frame and pretend this was planned.',
    'Analog ghosts detected. Digitizing in 3...2...none.',
    'Signal aligned. Distortion budget approved.',
    'No menu. No mercy. Just shaders.',
    'Tape hiss at nominal level. Visual noise online.',
    'Bootleg aesthetics engaged. Copyright lawyers asleep.',
    'CRT mood loaded. Reality set to unstable.',
    'Luma channel hungry. Feed it movement.',
    'Scanlines warming up. Please remain dramatic.',
    'Camera armed. Ego unarmed.',
    'Broadcast override accepted. Party standards lowered.',
    'Late-night lab protocol active. Keep lights ugly.',
    'Vector fever rising. Stay in the blast radius.',
    'Old-school pixels, new-school attitude.',
    'Magnetic tape vibes: immaculate. Sync pulse: feral.',
    'Raster lock achieved. Proceed with chaos.',
    'Warez soul, museum output.',
    'Frame pipeline hot. Art excuses ready.',
    'Underground TV station online.',
    'Unauthorized beauty mode enabled.',
]

_SHUTDOWN_LINES = [
    'Target lost. Rewind the tape and try again.',
    'Signal dropped. Night shift over.',
    'Transmission cut. Keep the noise alive.',
    'Raster collapsed. Good chaos session.',
    'Camera cool-down initiated. VHS dreams pending.',
    'Broadcast ended. Applause optional.',
    'Shutdown clean. Scene still illegal.',
    'No survivors, only screenshots.',
    'Tape ejected. Mood preserved.',
    'Visual feed terminated. Memories corrupted.',
    'Sync pulse gone. Heartbeat remains.',
    'End of transmission. Stay weird.',
    'Static wins tonight.',
    'Render lights out. See you in the next glitch.',
    'The cannon sleeps. The ghosts do not.',
    'Party closed. Artifact levels still critical.',
    'Output muted. Legend inflated.',
    'Video noise archived. Reality restored.',
    'Good hunt. Bring more faces next run.',
    'Channel closed. Keep it underground.',
]

_BLOCK_CHARS = '░▒▓█▓▒░'

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
    if max_width is not None and len('RETINA CANNON') <= max_width:
        return ['RETINA CANNON']
    return RETINA_CANNON_ASCII

def _lolcat_colorize(text):
    lolcat_bin = shutil.which('lolcat')
    if not lolcat_bin and os.path.isfile('/usr/games/lolcat'):
        lolcat_bin = '/usr/games/lolcat'
    if not lolcat_bin:
        return None
    try:
        return subprocess.check_output(
            [lolcat_bin, '-f'],
            input=text,
            text=True,
            timeout=2.0,
        )
    except Exception:
        return None

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

def _print_vhs_splash(countdown_seconds):
    cols, rows = _term_size()
    title = _figlet_title_lines(max_width=max(16, cols - 2))
    credit_a = 'Netmilk Studio sagl'
    credit_b = 'Retina Cannon // VHS night build'
    quote = random.choice(_BOOT_LINES)

    text_h = len(title) + 5
    top_pad = max((rows - text_h) // 2, 1)
    base = '\n' * top_pad

    # Single stable frame: no flashing during pre-countdown.
    _print_static_splash_frame(title, cols, base, credit_a, credit_b, quote, 12)

    if countdown_seconds < 0:
        _print_static_splash_frame(title, cols, base, credit_a, credit_b, quote, 12)
        print(_styled(_center_text_line('[HOLD] Press any key to SHOOT', cols), ANSI_YELLOW, bold=True))
        _wait_splash_release()
    else:
        start = max(1, int(countdown_seconds))
        _print_static_splash_frame(title, cols, base, credit_a, credit_b, quote, 12)
        for n in range(start, -1, -1):
            print('\r' + _countdown_progress_line(n, start, cols) + '\033[K', end='', flush=True)
            time.sleep(1.0)
        print()

    _clear_to_black()
    print(base, end='')
    _print_centered_title(title, cols, phase=14)
    print()
    print(_styled(_center_text_line(credit_a, cols), ANSI_WHITE, dim=True))
    print(_styled(_center_text_line('SHOOTING', cols), ANSI_RED, bold=True))
    time.sleep(0.45)
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
    if current_effect_mode == 3:   return GHOST_COLOR_MODE_NAMES[current_ghost_color_mode]
    return RASTER_COLOR_MODE_NAMES[current_raster_color_mode]

def _active_color_mode():
    if current_effect_mode == 0:   return current_rutt_color_mode
    if current_effect_mode == 1:   return current_ascii_color_mode
    if current_effect_mode == 2:   return current_pixelart_color_mode
    if current_effect_mode == 3:   return current_ghost_color_mode
    return current_raster_color_mode

def _set_active_color_mode(mode):
    global current_rutt_color_mode, current_ascii_color_mode, current_pixelart_size
    global current_pixelart_color_mode, current_ghost_color_mode, current_raster_color_mode
    if current_effect_mode == 0:   current_rutt_color_mode        = mode % len(RUTT_COLOR_MODE_NAMES)
    elif current_effect_mode == 1: current_ascii_color_mode       = mode % len(ASCII_COLOR_MODE_NAMES)
    elif current_effect_mode == 2:
        current_pixelart_color_mode = mode % len(PIXELART_COLOR_MODE_NAMES)
        # Give each pixel preset a useful default block size while keeping live tweak on arrows.
        current_pixelart_size = PIXELART_MODE_DEFAULT_SIZES[current_pixelart_color_mode]
    elif current_effect_mode == 3: current_ghost_color_mode        = mode % len(GHOST_COLOR_MODE_NAMES)
    else:                          current_raster_color_mode       = mode % len(RASTER_COLOR_MODE_NAMES)

def _cycle_active_color_mode(step):
    _set_active_color_mode(_active_color_mode() + step)
    print(f'\r[COLOR] {_color_mode_name()} | {_effect_param_label()}        ')

def _effect_param_label():
    if current_effect_mode == 0:   return f'[RUTT] Wave {current_rutt_wave:.2f}x'
    if current_effect_mode == 1:   return f'[ASCII] Density {current_ascii_density:.2f}x'
    if current_effect_mode == 2:   return f'[PIXEL] Block {int(current_pixelart_size)}px'
    if current_effect_mode == 3:   return f'[GHOST] Density {current_ghost_density:.2f}x'
    return f'[RASTER] Dot {int(current_raster_size)}px'

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
    effect = _slugify(EFFECT_MODE_NAMES[current_effect_mode])
    variant = _slugify(_color_mode_name())
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
    print(stat_row('Effect',   f'{EFFECT_MODE_NAMES[current_effect_mode]} · {_color_mode_name()}'))
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

    line = random.choice(_SHUTDOWN_LINES)
    if reason.startswith('init_error') or reason.startswith('run_error'):
        print(f'  {_styled("▶", ANSI_RED, bold=True)} {_styled(f"Renderer error: {reason}", ANSI_RED)}')
        print(f'  {_styled("▶", ANSI_MAGENTA, bold=True)} {_styled(line, ANSI_WHITE)}')
    elif reason in ('ctrl_c', 'signal'):
        print(f'  {_styled("▶", ANSI_CYAN, bold=True)} {_styled(line, ANSI_WHITE)}')
    else:
        print(f'  {_styled("▶", ANSI_GREEN, bold=True)} {_styled(line, ANSI_WHITE)}')

    print(_styled('  ' + '─' * 51, ANSI_DIM))
    print()

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, loc_channel0, loc_color_mode, loc_rutt_wave, loc_ascii_density
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

    # Create the texture manually
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

    loc_channel0 = glsl.glGetUniformLocation(program, b'iChannel0')
    if loc_channel0 >= 0:
        glsl.glUniform1i(loc_channel0, 0)
    if loc_color_mode >= 0:
        glsl.glUniform1i(loc_color_mode, _active_color_mode())
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
        _ps = current_raster_size if current_effect_mode == 4 else current_pixelart_size
        glsl.glUniform1f(loc_pixelart_size, c_float(_ps))

    print(f'[GL] texture {tex_id} ready, loc_channel0={loc_channel0}')
    _print_startup_banner()

@CFUNCTYPE(None, c_uint64, c_float)
def on_render(frame, time):
    global _fps_last_frame, _fps_last_time, _fps_smoothed, _fps_last_report_time
    with _lock:
        f = _frame
    data = f.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
    glsl.glActiveTexture(GL_TEXTURE0)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_id)
    glsl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, CAM_W, CAM_H,
                         GL_RGB, GL_UNSIGNED_BYTE, data)
    if loc_color_mode >= 0:
        glsl.glUniform1i(loc_color_mode, _active_color_mode())
    if loc_rutt_wave >= 0:
        glsl.glUniform1f(loc_rutt_wave, c_float(current_rutt_wave))
    if loc_ascii_density >= 0:
        _d = current_ghost_density if current_effect_mode == 3 else current_ascii_density
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
        _ps = current_raster_size if current_effect_mode == 4 else current_pixelart_size
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
            print(f'\r[FPS] {_fps_smoothed:5.1f} fps | {EFFECT_MODE_NAMES[current_effect_mode]} | {_color_mode_name()}        ')
            _fps_last_report_time = time
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
    global current_rutt_wave, current_ascii_density, current_pixelart_size
    global current_ghost_density, current_raster_size
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
                print(f'\r[EFFECT] {EFFECT_MODE_NAMES[current_effect_mode]} | [COLOR] {_color_mode_name()} | {_effect_param_label()}        ')
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
                if direction == 'up':
                    _cycle_active_color_mode(+1)
                elif direction == 'down':
                    _cycle_active_color_mode(-1)
                elif direction == 'right':
                    if current_effect_mode == 0:
                        current_rutt_wave = min(RUTT_WAVE_MAX, current_rutt_wave + RUTT_WAVE_STEP)
                    elif current_effect_mode == 1:
                        current_ascii_density = min(ASCII_DENSITY_MAX, current_ascii_density + ASCII_DENSITY_STEP)
                    elif current_effect_mode == 2:
                        current_pixelart_size = min(PIXELART_SIZE_MAX, current_pixelart_size + PIXELART_SIZE_STEP)
                    elif current_effect_mode == 3:
                        current_ghost_density = min(GHOST_DENSITY_MAX, current_ghost_density + GHOST_DENSITY_STEP)
                    else:
                        current_raster_size = min(PIXELART_SIZE_MAX, current_raster_size + PIXELART_SIZE_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif direction == 'left':
                    if current_effect_mode == 0:
                        current_rutt_wave = max(RUTT_WAVE_MIN, current_rutt_wave - RUTT_WAVE_STEP)
                    elif current_effect_mode == 1:
                        current_ascii_density = max(ASCII_DENSITY_MIN, current_ascii_density - ASCII_DENSITY_STEP)
                    elif current_effect_mode == 2:
                        current_pixelart_size = max(PIXELART_SIZE_MIN, current_pixelart_size - PIXELART_SIZE_STEP)
                    elif current_effect_mode == 3:
                        current_ghost_density = max(GHOST_DENSITY_MIN, current_ghost_density - GHOST_DENSITY_STEP)
                    else:
                        current_raster_size = max(PIXELART_SIZE_MIN, current_raster_size - PIXELART_SIZE_STEP)
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
    default=10,
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
