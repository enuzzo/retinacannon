#!/usr/bin/env python
import sys, os, glob, threading, select, termios
from ctypes import CFUNCTYPE, c_uint, c_uint64, c_float, byref
from pathlib import Path

RETINA_DIR = Path(__file__).resolve().parent

# Resolve kms-glsl dependency: KMS_GLSL_DIR env var > ../kms-glsl > ~/kms-glsl
_kms_env = os.environ.get('KMS_GLSL_DIR', '')
KMS_GLSL_DIR = Path(_kms_env).resolve() if _kms_env else None

if KMS_GLSL_DIR is None or not (KMS_GLSL_DIR / 'lib').is_dir():
    KMS_GLSL_DIR = None
    for _candidate in [
        RETINA_DIR.parent / 'kms-glsl',
        Path.home() / 'kms-glsl',
    ]:
        if (_candidate / 'lib').is_dir():
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
current_rutt_color_mode = 2
current_ascii_color_mode = 0
current_rutt_wave = 0.40
current_ascii_density = 3.00
current_effect_mode = 0
current_view_mode = 2
current_show_fps = 0
RUTT_WAVE_STEP = 0.10
RUTT_WAVE_MIN = 0.40
RUTT_WAVE_MAX = 3.80
ASCII_DENSITY_STEP = 0.20
ASCII_DENSITY_MIN = 1.00
ASCII_DENSITY_MAX = 6.00

RUTT_COLOR_MODE_NAMES = ['B/W', 'Colors', 'Prism Warp', 'Acid Melt']
ASCII_COLOR_MODE_NAMES = ['Color symbols', 'Monochrome symbols', 'Inverted mono letters', 'Inverted color letters']
EFFECT_MODE_NAMES = ['Rutt-Etra CRT', 'ASCII Cam']
VIEW_MODE_NAMES = ['16:9', '4:3', 'Fisheye']

_quiet_stdin_w = None
_fps_last_frame = None
_fps_last_time = None
_fps_smoothed = 0.0
_fps_last_report_time = None
_ctrl_c_requested = False

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
    return RUTT_COLOR_MODE_NAMES[current_rutt_color_mode] if current_effect_mode == 0 else ASCII_COLOR_MODE_NAMES[current_ascii_color_mode]

def _active_color_mode():
    return current_rutt_color_mode if current_effect_mode == 0 else current_ascii_color_mode

def _set_active_color_mode(mode):
    global current_rutt_color_mode, current_ascii_color_mode
    if current_effect_mode == 0:
        current_rutt_color_mode = mode % len(RUTT_COLOR_MODE_NAMES)
    else:
        current_ascii_color_mode = mode % len(ASCII_COLOR_MODE_NAMES)

def _cycle_active_color_mode(step):
    _set_active_color_mode(_active_color_mode() + step)
    print(f'\r[COLOR] {_color_mode_name()}        ')

def _effect_param_label():
    if current_effect_mode == 0:
        return f'[RUTT] Wave {current_rutt_wave:.2f}x'
    return f'[ASCII] Density {current_ascii_density:.2f}x'

def _toggle_fps_logging():
    global current_show_fps, _fps_last_report_time
    current_show_fps = 0 if current_show_fps else 1
    _fps_last_report_time = None
    if current_show_fps:
        print(f'\r{_styled("[FPS]", ANSI_CYAN, bold=True)} LOG ON (terminal only)        ')
    else:
        print(f'\r{_styled("[FPS]", ANSI_CYAN, bold=True)} LOG OFF        ')

def _print_startup_banner():
    print()
    _print_retina_logo(offset=0)
    print(_styled('=== RETINA CANNON // BOOT SEQUENCE ===', ANSI_MAGENTA, bold=True))
    print(f'{_styled("[Startup]", ANSI_GREEN, bold=True)} Camera: {CAM_W}x{CAM_H} | View: {VIEW_MODE_NAMES[current_view_mode]}')
    print(f'{_styled("[Startup]", ANSI_GREEN, bold=True)} Rutt default: {RUTT_COLOR_MODE_NAMES[current_rutt_color_mode]} | ASCII default: {ASCII_COLOR_MODE_NAMES[current_ascii_color_mode]}')
    print(f'{_styled("[Controls]", ANSI_CYAN, bold=True)} Arrow Up/Down: cycle color mode | Arrow Left/Right: Rutt wave / ASCII density | Space: effect mode | V: view | F: fps log | Ctrl+C: quit')
    print(_styled('======================================', ANSI_MAGENTA, bold=True))

def _print_shutdown_banner(reason):
    print()
    _print_retina_logo(offset=3)
    print(_styled('=== RETINA CANNON // SHUTDOWN ===', ANSI_YELLOW, bold=True))
    print(f'{_styled("[Shutdown]", ANSI_YELLOW, bold=True)} Renderer stop requested.')
    print(f'{_styled("[Shutdown]", ANSI_YELLOW, bold=True)} Camera stream offline.')
    if reason == 'ctrl_c':
        print(f'{_styled("[Goodbye]", ANSI_CYAN, bold=True)} Target lost, cannon reloading. See you on the next run.')
    elif reason.startswith('init_error') or reason.startswith('run_error'):
        print(f'{_styled("[Goodbye]", ANSI_RED, bold=True)} Exit with error ({reason}).')
    else:
        print(f'{_styled("[Goodbye]", ANSI_GREEN, bold=True)} Session closed. See you on the next visual test.')
    print(_styled('================================', ANSI_YELLOW, bold=True))

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, loc_channel0, loc_color_mode, loc_rutt_wave, loc_ascii_density
    global loc_effect_mode, loc_view_mode, loc_camera_aspect

    loc_color_mode = glsl.glGetUniformLocation(program, b'uColorMode')
    loc_rutt_wave = glsl.glGetUniformLocation(program, b'uRuttWave')
    loc_ascii_density = glsl.glGetUniformLocation(program, b'uAsciiDensity')
    loc_effect_mode = glsl.glGetUniformLocation(program, b'uEffectMode')
    loc_view_mode = glsl.glGetUniformLocation(program, b'uViewMode')
    loc_camera_aspect = glsl.glGetUniformLocation(program, b'uCameraAspect')

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
    global current_rutt_wave, current_ascii_density
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
        while True:
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
                    else:
                        current_ascii_density = min(ASCII_DENSITY_MAX, current_ascii_density + ASCII_DENSITY_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif direction == 'left':
                    if current_effect_mode == 0:
                        current_rutt_wave = max(RUTT_WAVE_MIN, current_rutt_wave - RUTT_WAVE_STEP)
                    else:
                        current_ascii_density = max(ASCII_DENSITY_MIN, current_ascii_density - ASCII_DENSITY_STEP)
                    print(f'\r{_effect_param_label()}        ')
                elif seq and seq[-1] in ('F', 'f'):
                    # Fallback for terminals that emit ESC...F for this key.
                    _toggle_fps_logging()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        os.close(fd)

_detach_stdin_from_renderer()
threading.Thread(target=keyboard_thread, daemon=True).start()

# ---- Launch glsl ----
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('shader', nargs='?', default=str(RETINA_DIR / 'rutt_etra.frag'))
args = parser.parse_args()

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
