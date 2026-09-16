@echo off
chcp 65001 > nul
echo Setting up Python virtual environment...
py -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)
echo Activating virtual environment and installing requirements...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Setup complete!
pause
