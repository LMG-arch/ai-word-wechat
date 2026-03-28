@echo off
echo Starting web server...
echo Open http://localhost:8080 in your browser
echo.
cd /d "%~dp0"
python -m http.server 8080
pause
