#!/bin/bash
# WoeUSB-ng launcher script with proper environment setup

# Source the environment
source /var/home/ben/code/WoeUSB-ng/env.bash

# Launch the tkinter GUI unprivileged; elevation happens via pkexec inside the app
export GDK_SCALE=${GDK_SCALE:-2}
export GDK_DPI_SCALE=${GDK_DPI_SCALE:-2}
export QT_SCALE_FACTOR=${QT_SCALE_FACTOR:-2}
export TKDPI=${TKDPI:-200}

/var/home/ben/dotfiles/local/xdgdata/mise/installs/python/3.13.6/bin/python3 /var/home/ben/code/WoeUSB-ng/WoeUSB/tkinter_gui.py
