#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

PYTHON_CMD="python"
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    "$SCRIPT_DIR/venv/bin/python" -c "import sys; print(sys.executable)" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Using Virtual Environment..."
        PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
    fi
fi

echo "Starting Pocket TTS Web UI..."
"$PYTHON_CMD" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

if [ $? -ne 0 ]; then
    echo
    echo "Failed to start the app. Make sure Python and the project dependencies are installed."
    exit 1
fi
