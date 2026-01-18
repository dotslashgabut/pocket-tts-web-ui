@echo off
set "PYTHON_CMD=python"
if exist "venv\Scripts\python.exe" (
    echo Using Virtual Environment...
    set "PYTHON_CMD=venv\Scripts\python.exe"
)

echo Downloading models...
"%PYTHON_CMD%" setup_offline_models.py
echo Done!
pause
