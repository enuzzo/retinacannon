#!/bin/bash
# Forziamo il traduttore della telecamera
export LD_PRELOAD=/usr/libexec/aarch64-linux-gnu/libcamera/v4l2-compat.so
export XDG_RUNTIME_DIR=/run/user/0

# Lanciamo glslViewer a tutto schermo
# Usiamo -c 0 che indica al programma di usare la prima camera disponibile
/usr/local/bin/glslViewer /home/enuzzo/retinacannon/camera_test.frag -c 0 -f
