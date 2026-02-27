#!/usr/bin/env python
import sys, os, glob, threading, select, termios, signal, subprocess, random
from ctypes import CFUNCTYPE, c_uint, c_uint64, c_float, byref
from pathlib import Path

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
    while _running:
        f = picam.capture_array()
        with _lock:
            global _frame
            _frame = f

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
loc_camera_aspect = -1
loc_pixelart_size = -1
current_rutt_color_mode = 2
current_ascii_color_mode = 0
current_pixelart_color_mode = 0
current_rutt_wave = 0.40
current_ascii_density = 3.00
current_pixelart_size = 8.0
current_effect_mode = 0
current_view_mode = 2
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
PIXELART_COLOR_MODE_NAMES = ['Full Color', 'Game Boy', 'CGA', 'Phosphor', 'Amber', 'Infrared']
EFFECT_MODE_NAMES = ['Rutt-Etra CRT', 'ASCII Cam', 'Pixel Art']
VIEW_MODE_NAMES = ['16:9', '4:3', 'Fisheye']

_quiet_stdin_w = None
_fps_last_frame = None
_fps_last_time = None
_fps_smoothed = 0.0
_fps_last_report_time = None
_ctrl_c_requested = False
_session_start = None
_shader_name = ''

_BOOT_QUOTES = [
    '"The map is not the territory."  — Korzybski',
    '"The medium is the message."  — McLuhan',
    '"Television is not the truth."  — Paddy Chayefsky, Network (1976)',
    '"Reality is merely an illusion, albeit a persistent one."  — Einstein',
    '"All models are wrong. Some are useful."  — George Box',
    '"We shape our tools, and thereafter our tools shape us."  — McLuhan',
    '"Seeing is forgetting the name of the thing one sees."  — Paul Valéry',
    '"The screen is the new canvas."  — Netmilk Studio',
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

def _print_retina_logo(offset=0):
    for i, line in enumerate(RETINA_CANNON_ASCII):
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
    if current_effect_mode == 0:
        return RUTT_COLOR_MODE_NAMES[current_rutt_color_mode]
    elif current_effect_mode == 1:
        return ASCII_COLOR_MODE_NAMES[current_ascii_color_mode]
    return PIXELART_COLOR_MODE_NAMES[current_pixelart_color_mode]

def _active_color_mode():
    if current_effect_mode == 0:
        return current_rutt_color_mode
    elif current_effect_mode == 1:
        return current_ascii_color_mode
    return current_pixelart_color_mode

def _set_active_color_mode(mode):
    global current_rutt_color_mode, current_ascii_color_mode, current_pixelart_color_mode
    if current_effect_mode == 0:
        current_rutt_color_mode = mode % len(RUTT_COLOR_MODE_NAMES)
    elif current_effect_mode == 1:
        current_ascii_color_mode = mode % len(ASCII_COLOR_MODE_NAMES)
    else:
        current_pixelart_color_mode = mode % len(PIXELART_COLOR_MODE_NAMES)

def _cycle_active_color_mode(step):
    _set_active_color_mode(_active_color_mode() + step)
    print(f'\r[COLOR] {_color_mode_name()}        ')

def _effect_param_label():
    if current_effect_mode == 0:
        return f'[RUTT] Wave {current_rutt_wave:.2f}x'
    elif current_effect_mode == 1:
        return f'[ASCII] Density {current_ascii_density:.2f}x'
    return f'[PIXEL] Size {int(current_pixelart_size)}px'

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
    print()

    # Logo with scan-line effect: each line appears with a brief delay
    for i, line in enumerate(RETINA_CANNON_ASCII):
        color = ANSI_RAINBOW[i % len(ANSI_RAINBOW)]
        print(_styled(line, color, bold=True))
        time.sleep(0.045)
    print(_styled('Copyright (c) Netmilk Studio sagl', ANSI_WHITE, dim=True))
    print(_styled('Licensed under the MIT License', ANSI_WHITE, dim=True))
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

    # Random nerd quote
    quote = random.choice(_BOOT_QUOTES)
    print(f'  {_styled(quote, ANSI_DIM)}')
    print()

    print(f'  {_styled("↑↓", ANSI_CYAN, bold=True)} color  '
          f'{_styled("←→", ANSI_CYAN, bold=True)} wave/density  '
          f'{_styled("Space", ANSI_CYAN, bold=True)} effect  '
          f'{_styled("V", ANSI_CYAN, bold=True)} view  '
          f'{_styled("F", ANSI_CYAN, bold=True)} fps  '
          f'{_styled("Ctrl+C", ANSI_CYAN, bold=True)} quit')
    print(_styled('  ' + '─' * 51, ANSI_DIM))

def _print_shutdown_banner(reason):
    print()

    # Logo corruption: each line degrades progressively
    amounts = [0.15, 0.35, 0.55, 0.75, 0.90, 1.0]
    for i, line in enumerate(RETINA_CANNON_ASCII):
        amount = amounts[min(i, len(amounts) - 1)]
        corrupted = _corrupt_line(line, amount)
        color = ANSI_RED if i >= 3 else ANSI_YELLOW
        print(_styled(corrupted, color, dim=(i >= 2)))
        time.sleep(0.035)
    print(_styled('░░░░░░░ signal lost ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░', ANSI_RED, dim=True))
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

    if reason in ('ctrl_c', 'signal'):
        print(f'  {_styled("▶", ANSI_CYAN, bold=True)} {_styled("Target lost. Cannon reloading.", ANSI_WHITE)}')
    elif reason.startswith('init_error') or reason.startswith('run_error'):
        print(f'  {_styled("▶", ANSI_RED, bold=True)} {_styled(f"Renderer exited with error: {reason}", ANSI_RED)}')
    else:
        print(f'  {_styled("▶", ANSI_GREEN, bold=True)} {_styled("Session closed cleanly. See you on the next visual test.", ANSI_WHITE)}')

    print(_styled('  ' + '─' * 51, ANSI_DIM))
    print()

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, loc_channel0, loc_color_mode, loc_rutt_wave, loc_ascii_density
    global loc_effect_mode, loc_view_mode, loc_camera_aspect, loc_pixelart_size

    loc_color_mode = glsl.glGetUniformLocation(program, b'uColorMode')
    loc_rutt_wave = glsl.glGetUniformLocation(program, b'uRuttWave')
    loc_ascii_density = glsl.glGetUniformLocation(program, b'uAsciiDensity')
    loc_effect_mode = glsl.glGetUniformLocation(program, b'uEffectMode')
    loc_view_mode = glsl.glGetUniformLocation(program, b'uViewMode')
    loc_camera_aspect = glsl.glGetUniformLocation(program, b'uCameraAspect')
    loc_pixelart_size = glsl.glGetUniformLocation(program, b'uPixelSize')

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
    if loc_camera_aspect >= 0:
        glsl.glUniform1f(loc_camera_aspect, c_float(CAM_W / CAM_H))
    if loc_pixelart_size >= 0:
        glsl.glUniform1f(loc_pixelart_size, c_float(current_pixelart_size))

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
        glsl.glUniform1f(loc_ascii_density, c_float(current_ascii_density))
    if loc_effect_mode >= 0:
        glsl.glUniform1i(loc_effect_mode, current_effect_mode)
    if loc_view_mode >= 0:
        glsl.glUniform1i(loc_view_mode, current_view_mode)
    if loc_camera_aspect >= 0:
        glsl.glUniform1f(loc_camera_aspect, c_float(CAM_W / CAM_H))
    if loc_pixelart_size >= 0:
        glsl.glUniform1f(loc_pixelart_size, c_float(current_pixelart_size))
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
    global current_effect_mode, current_view_mode, _ctrl_c_requested
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
            if ch in ('f', 'F'):
                _toggle_fps_logging()
                continue
            if ch in ('v', 'V'):
                current_view_mode = (current_view_mode + 1) % len(VIEW_MODE_NAMES)
                print(f'\r[VIEW] {VIEW_MODE_NAMES[current_view_mode]}        ')
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
                    else:
                        current_pixelart_size = min(PIXELART_SIZE_MAX, current_pixelart_size + PIXELART_SIZE_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif direction == 'left':
                    if current_effect_mode == 0:
                        current_rutt_wave = max(RUTT_WAVE_MIN, current_rutt_wave - RUTT_WAVE_STEP)
                    elif current_effect_mode == 1:
                        current_ascii_density = max(ASCII_DENSITY_MIN, current_ascii_density - ASCII_DENSITY_STEP)
                    else:
                        current_pixelart_size = max(PIXELART_SIZE_MIN, current_pixelart_size - PIXELART_SIZE_STEP)
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
args = parser.parse_args()
_shader_name = Path(args.shader).name

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
