# Retina Cannon — Installation Guide

## Prerequisites

- Raspberry Pi 4 or Raspberry Pi 5
- Raspberry Pi OS (64-bit, Bookworm or later)
- IMX219-based camera module (any FOV: 77°, 120°, 160°, 200°)
- HDMI display connected
- SSH or direct terminal access

## 1. Camera setup

### Raspberry Pi 4

Connect the camera via 15-pin CSI ribbon cable. The default config should
work out of the box — verify `camera_auto_detect=1` is in
`/boot/firmware/config.txt`.

### Raspberry Pi 5

RPi5 uses smaller 22-pin FPC connectors. You need the official 15-to-22 pin
adapter cable. Connect to **CAM0** (the port nearest to Ethernet/USB).

**Important:** `camera_auto_detect=1` may fail to detect IMX219 on RPi5.
Add the explicit overlay:

```bash
echo 'dtoverlay=imx219,cam0' | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

### Verify camera

```bash
rpicam-hello --list-cameras
```

You should see the IMX219 sensor listed. If not, check:
- Flat cable orientation (contacts face the PCB)
- Try the other CSI port (CAM0 ↔ CAM1)
- `dmesg | grep -i cfe` — no output means the CSI driver didn't initialize

Quick test with 5-second preview on the display:

```bash
rpicam-hello -t 5000
```

## 2. System dependencies

```bash
sudo apt update
sudo apt install -y \
    git \
    gcc \
    make \
    python3-picamera2 \
    python3-numpy \
    libdrm-dev \
    libgbm-dev \
    libegl-dev \
    libgles-dev \
    libxcb-randr0-dev \
    i2c-tools
```

## 3. Build kms-glsl

kms-glsl is the DRM/KMS + OpenGL ES rendering engine. Clone it alongside
the retinacannon directory:

```bash
cd ~
git clone https://github.com/astefanutti/kms-glsl.git
cd kms-glsl
make
```

Verify the build produced `glsl.so`:

```bash
ls -l ~/kms-glsl/glsl.so
```

## 4. Clone Retina Cannon

```bash
cd ~
git clone https://github.com/nickvon/retinacannon.git
```

Expected directory layout:

```
~/kms-glsl/          ← kms-glsl (contains glsl.so, lib.py, gl.py)
~/retinacannon/      ← this repo
```

## 5. Run

```bash
cd ~/retinacannon
./start_cannon.sh
```

You should see the shader rendering live camera feed on your display.
Press `Space` to cycle effects, `Ctrl+C` to exit gracefully.

## Troubleshooting

| Problem | Solution |
|---|---|
| `kms-glsl not found` | Ensure `~/kms-glsl/glsl.so` exists, or set `KMS_GLSL_DIR=/path/to/kms-glsl` |
| `No cameras available` | Check cable, add `dtoverlay=imx219,cam0` to config.txt, reboot |
| Black screen / no output | Make sure HDMI is connected before boot, no desktop session is running |
| `Permission denied` on DRM | Run without a desktop session (from TTY or SSH), or add user to `video` group |
| Display stuck after crash | **Never** use `kill -9`. Use `kill -SIGINT $(pgrep -f retina_cannon.py)` |
