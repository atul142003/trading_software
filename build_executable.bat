@echo off
echo ========================================
echo Building ASA Trading Executable
echo ========================================
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build the executable
echo Building executable with PyInstaller...
pyinstaller app.spec

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo The executable can be found in the 'dist' folder.
echo.
echo To run the application:
echo   1. Navigate to the dist folder
echo   2. Double-click ASA_Trading.exe
echo.
pause
