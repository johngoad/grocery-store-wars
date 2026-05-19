#!/bin/bash
# Install chromium browsers for Playwright
PY=/Library/Developer/CommandLineTools/usr/bin/python3
echo "Using: $PY"
$PY -m playwright install chromium 2>&1
echo "Exit: $?"
