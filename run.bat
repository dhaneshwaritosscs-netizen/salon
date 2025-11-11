@echo off
echo Starting Pretty Saloon Management System...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server...
python app.py
pause

