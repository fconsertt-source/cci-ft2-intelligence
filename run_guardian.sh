#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH=. python3 src/presentation/cli/gui_main.py > pipeline.log 2>&1 &
disown
