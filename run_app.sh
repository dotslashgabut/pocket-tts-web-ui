#!/bin/bash
PYTHON_CMD="python"
if [ -f "venv/bin/python" ]; then
    echo "Using Virtual Environment..."
    PYTHON_CMD="venv/bin/python"
fi

echo "Starting Pocket TTS Web UI..."
"$PYTHON_CMD" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
