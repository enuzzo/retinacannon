#!/usr/bin/env python
import sys, os, glob, threading, select
from ctypes import CFUNCTYPE, c_uint, c_uint64, c_float, byref
from pathlib import Path

os.chdir('/home/enuzzo/kms-glsl')
sys.path.insert(0, '/home/enuzzo/kms-glsl')

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
current_color_mode = 0
current_rutt_wave = 0.40
current_ascii_density = 3.00
current_effect_mode = 0
current_view_mode = 2
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
        return RUTT_COLOR_MODE_NAMES[current_color_mode]
    return ASCII_COLOR_MODE_NAMES[current_color_mode]

def _effect_param_label():
    if current_effect_mode == 0:
        return f'[RUTT] Wave {current_rutt_wave:.2f}x'
    return f'[ASCII] Density {current_ascii_density:.2f}x'

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
    print('[Controls] Arrow Up/Down: color mode | Arrow Left/Right: Rutt wave / ASCII density | Space: effect mode | F: view')

@CFUNCTYPE(None, c_uint64, c_float)
def on_render(frame, time):
    with _lock:
        f = _frame
    data = f.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
    glsl.glActiveTexture(GL_TEXTURE0)
    glsl.glBindTexture(GL_TEXTURE_2D, tex_id)
    glsl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, CAM_W, CAM_H,
                         GL_RGB, GL_UNSIGNED_BYTE, data)
    if loc_color_mode >= 0:
        glsl.glUniform1i(loc_color_mode, current_color_mode)
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
    global current_color_mode, current_rutt_wave, current_ascii_density
    global current_effect_mode, current_view_mode
    import termios, tty
    try:
        fd = os.open('/dev/tty', os.O_RDONLY)
    except OSError:
        print('[Controls] /dev/tty unavailable, keyboard controls disabled')
        return
    if not os.isatty(fd):
        os.close(fd)
        print('[Controls] /dev/tty is not a TTY, keyboard controls disabled')
        return
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            b = os.read(fd, 1)
            if not b:
                continue
            ch = b.decode('latin1', errors='ignore')
            if ch == '\x03':  # Ctrl+C
                _request_renderer_stop()
                break
            if ch == ' ':
                current_effect_mode = (current_effect_mode + 1) % len(EFFECT_MODE_NAMES)
                print(f'\r[EFFECT] {EFFECT_MODE_NAMES[current_effect_mode]} | [COLOR] {_color_mode_name()} | {_effect_param_label()}        ')
                continue
            if ch in ('f', 'F'):
                current_view_mode = (current_view_mode + 1) % len(VIEW_MODE_NAMES)
                print(f'\r[VIEW] {VIEW_MODE_NAMES[current_view_mode]}        ')
                continue
            if ch == '\x1b':
                seq = _read_escape_sequence(fd)
                direction = _decode_arrow(seq)
                if direction == 'up':
                    current_color_mode = (current_color_mode + 1) % 4
                    print(f'\r[COLOR] {_color_mode_name()}        ')
                elif direction == 'down':
                    current_color_mode = (current_color_mode - 1) % 4
                    print(f'\r[COLOR] {_color_mode_name()}        ')
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
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        os.close(fd)

_detach_stdin_from_renderer()
threading.Thread(target=keyboard_thread, daemon=True).start()

# ---- Launch glsl ----
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('shader', nargs='?', default='/home/enuzzo/retinacannon/rutt_etra.frag')
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
if ret != 0:
    sys.exit(ret)

ret = glsl.run()
if ret != 0:
    sys.exit(ret)
try:
    glsl.join()
except KeyboardInterrupt:
    _request_renderer_stop()
    glsl.join()

_running = False
picam.stop()
picam.close()
if _quiet_stdin_w is not None:
    os.close(_quiet_stdin_w)
