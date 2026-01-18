@echo off
set "PYTHON_CMD=python"
if exist "venv\Scripts\python.exe" (
    echo Using Virtual Environment...
    set "PYTHON_CMD=venv\Scripts\python.exe"
)

echo Starting Pocket TTS Web UI...
"%PYTHON_CMD%" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
pause
