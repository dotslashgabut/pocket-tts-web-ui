#!/bin/bash
PYTHON_CMD="python"
if [ -f "venv/bin/python" ]; then
    echo "Using Virtual Environment..."
    PYTHON_CMD="venv/bin/python"
fi

echo "Downloading models..."
"$PYTHON_CMD" setup_offline_models.py
echo "Done!"
