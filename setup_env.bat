@echo off
echo Setting up Virtual Environment...

if not exist "venv" (
    echo Creating venv...
    python -m venv venv
) else (
    echo venv already exists.
)

echo Activating venv and installing requirements...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo Setup complete. You can now use run_app.bat
pause
