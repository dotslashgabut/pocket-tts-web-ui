@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD=python"
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -c "import sys; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 (
        echo Using Virtual Environment...
        set "PYTHON_CMD=%~dp0venv\Scripts\python.exe"
    )
)

echo Starting Pocket TTS Web UI...
"%PYTHON_CMD%" -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
if errorlevel 1 (
    echo.
    echo Failed to start the app. Make sure Python and the project dependencies are installed.
    pause
)
