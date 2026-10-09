@echo off
echo Installing/updating dependencies...
python -m pip install -r requirements.txt
echo.
echo Starting InterviewAI...
python app.py
pause
