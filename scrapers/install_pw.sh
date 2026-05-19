#!/bin/bash
set -e
echo "=== Python path ==="
which python3
python3 --version

echo ""
echo "=== Install playwright browsers ==="
python3 -m playwright install chromium 2>&1

echo ""
echo "=== Verify ==="
python3 -c "from playwright.async_api import async_playwright; print('OK: playwright module loads')"
