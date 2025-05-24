#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

rm -rf build dist
pyinstaller \
  --onefile \
  --windowed \
  --name TrupathConverter \
  --add-data "src/trupath_analyser.py:src" \
  --add-data "src/trupath_gui.py:src" \
  src/trupath_gui.py
