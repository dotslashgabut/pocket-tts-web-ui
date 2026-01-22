#!/bin/bash
echo "Setting up Virtual Environment..."



if [ ! -d "venv" ]; then
    echo "Creating venv..."
    python3 -m venv venv
else
    echo "venv already exists."
fi

echo "Activating venv and installing requirements..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Setup complete. You can now use ./run_app.sh"
