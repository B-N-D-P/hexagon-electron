#!/bin/bash
# HEXAGON Structural Health - Simple Launcher

cd "$(dirname "$0")"
source ui_env_new/bin/activate
python3 ui_cli.py
