#!/bin/bash
# WoeUSB-ng launcher script with proper environment setup

# Source the environment
source /var/home/ben/code/WoeUSB-ng/env.bash

# Launch with all necessary environment variables
sudo env \
  LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  GTK_DATA_PREFIX="$GTK_DATA_PREFIX" \
  GTK_EXE_PREFIX="$GTK_EXE_PREFIX" \
  GTK_PATH="$GTK_PATH" \
  GTK_THEME="$GTK_THEME" \
  GI_TYPELIB_PATH="$GI_TYPELIB_PATH" \
  XDG_DATA_DIRS="$XDG_DATA_DIRS" \
  GSETTINGS_SCHEMA_DIR="$GSETTINGS_SCHEMA_DIR" \
  GTK_CSD="$GTK_CSD" \
  GTK_USE_PORTAL="$GTK_USE_PORTAL" \
  NO_AT_BRIDGE="$NO_AT_BRIDGE" \
  WX_USE_GENERIC_FILEDIALOG="$WX_USE_GENERIC_FILEDIALOG" \
  GTK_OVERLAY_SCROLLING="$GTK_OVERLAY_SCROLLING" \
  GTK_MODULES="$GTK_MODULES" \
  XDG_CACHE_HOME="$XDG_CACHE_HOME" \
  GTK_IM_MODULE_FILE="$GTK_IM_MODULE_FILE" \
  WXSUPPRESS_SIZER_FLAGS_CHECK="$WXSUPPRESS_SIZER_FLAGS_CHECK" \
  $(which woeusbgui) 2>&1 | grep --line-buffered -v "gtk_widget_hide: assertion 'GTK_IS_WIDGET (widget)' failed" | sed -u '/^[[:space:]]*$/d'
  # Temporarily disable filtering to see installation progress
  # | grep -v -E "(gtk_widget_hide: assertion|Unable to load resource for composite template|_gtk_css_provider_load_named: assertion|gtk_widget_class_bind_template|gtk_container_|gtk_box_|gtk_button_box_|gtk_label_|gtk_widget_init_template|gtk_widget_get_parent|gtk_widget_set_)" | grep -v "^\s*$"
  # G_MESSAGES_DEBUG="" \
  # GTK_DEBUG="" \
