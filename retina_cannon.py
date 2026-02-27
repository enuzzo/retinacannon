#!/usr/bin/env python
import sys, os, glob, threading, signal, select
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
loc_distortion = -1
current_color_mode = 0
current_distortion = 1.0
DISTORTION_STEP = 0.05
DISTORTION_MIN = 0.10
DISTORTION_MAX = 3.00

COLOR_MODE_NAMES = ['White', 'Green phosphor', 'Amber CRT', 'Camera colors']

_quiet_stdin_w = None

def _detach_stdin_from_renderer():
    # kms-glsl treats any readable stdin as "user interrupted".
    # Keep fd 0 on an idle pipe and read controls from /dev/tty instead.
    global _quiet_stdin_w
    rfd, wfd = os.pipe()
    os.dup2(rfd, 0)
    os.close(rfd)
    _quiet_stdin_w = wfd

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, loc_channel0, loc_color_mode, loc_distortion

    loc_color_mode = glsl.glGetUniformLocation(program, b'uColorMode')
    loc_distortion = glsl.glGetUniformLocation(program, b'uDistortion')

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
    if loc_distortion >= 0:
        glsl.glUniform1f(loc_distortion, c_float(current_distortion))

    print(f'[GL] texture {tex_id} ready, loc_channel0={loc_channel0}')
    print('[Controls] Arrow Up/Down: color mode | Arrow Left/Right: distortion')

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
    if loc_distortion >= 0:
        glsl.glUniform1f(loc_distortion, c_float(current_distortion))

glsl.onInit(on_init)
glsl.onRender(on_render)

# ---- Keyboard thread ----
def _read_escape_sequence(fd, max_len=16, timeout=0.02):
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
    if not seq or seq[0] not in ('[', 'O'):
        return None
    return {
        'A': 'up',
        'B': 'down',
        'C': 'right',
        'D': 'left',
    }.get(seq[-1])

def keyboard_thread():
    global current_color_mode, current_distortion
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
                glsl.stop()
                break
            if ch == '\x1b':
                seq = _read_escape_sequence(fd)
                direction = _decode_arrow(seq)
                if direction == 'up':
                    current_color_mode = (current_color_mode + 1) % 4
                    print(f'\r[COLOR] {COLOR_MODE_NAMES[current_color_mode]}        ')
                elif direction == 'down':
                    current_color_mode = (current_color_mode - 1) % 4
                    print(f'\r[COLOR] {COLOR_MODE_NAMES[current_color_mode]}        ')
                elif direction == 'right':
                    current_distortion = min(DISTORTION_MAX, current_distortion + DISTORTION_STEP)
                    print(f'\r[DISTORTION] {current_distortion:.2f}x        ')
                elif direction == 'left':
                    current_distortion = max(DISTORTION_MIN, current_distortion - DISTORTION_STEP)
                    print(f'\r[DISTORTION] {current_distortion:.2f}x        ')
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

stopped = threading.Event()
threading.Thread(target=lambda: (glsl.join(), stopped.set()), daemon=True).start()
glsl.run()

signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGCONT])
from signal import sigwait
if sigwait({signal.SIGINT, signal.SIGCONT}) == signal.SIGINT:
    glsl.stop()
    stopped.wait(timeout=30)

_running = False
picam.stop()
picam.close()
if _quiet_stdin_w is not None:
    os.close(_quiet_stdin_w)
