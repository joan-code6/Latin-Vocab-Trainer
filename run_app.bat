@echo off
cd flask_app
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo Starting Flask App...
python app.py
pause
