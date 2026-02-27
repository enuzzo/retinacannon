#!/usr/bin/env python
import sys, os, glob, threading, signal
from ctypes import CFUNCTYPE, c_uint, c_uint64, c_float, byref
from pathlib import Path

os.chdir('/home/enuzzo/kms-glsl')
sys.path.insert(0, '/home/enuzzo/kms-glsl')

from lib import glsl, options
from gl import *

# ---- Inizializza picamera2 subito, prima di tutto ----
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

# ---- Setup GL texture manuale ----
tex_id = None
tex_unit = 0
loc_channel0 = -1
loc_color_mode = -1
current_color_mode = 0

@CFUNCTYPE(None, c_uint, c_uint, c_uint)
def on_init(program, width, height):
    global tex_id, loc_channel0, loc_color_mode

    loc_color_mode = glsl.glGetUniformLocation(program, b'uColorMode')

    # Crea texture manualmente
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

    print(f'[GL] texture {tex_id} ready, loc_channel0={loc_channel0}')

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

glsl.onInit(on_init)
glsl.onRender(on_render)

# ---- Keyboard thread ----
def keyboard_thread():
    global current_color_mode
    import termios, tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch == '\x03':  # Ctrl+C
                glsl.stop()
                break
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    names = ['Bianco','Verde phosphor','Ambra CRT','Colori camera']
                    if ch3 == 'A':
                        current_color_mode = (current_color_mode + 1) % 4
                        print(f'\r[COLOR] {names[current_color_mode]}        ')
                    elif ch3 == 'B':
                        current_color_mode = (current_color_mode - 1) % 4
                        print(f'\r[COLOR] {names[current_color_mode]}        ')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

threading.Thread(target=keyboard_thread, daemon=True).start()

# ---- Lancia glsl ----
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
