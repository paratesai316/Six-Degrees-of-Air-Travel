@echo off
TITLE Multi Modal Flight Map

:: This batch file installs all required Python packages and then
:: runs the four static analysis scripts in sequence.

echo ==========================================================
echo  STEP 1: INSTALLING PYTHON DEPENDENCIES
echo ==========================================================
echo.
echo Installing all packages from requirements.txt...
echo This may take a few minutes. Please wait.
echo.

:: Install all packages from the requirements file.
pip install -r requirements.txt > nul

:: Check if the installation was successful.
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python packages.
    echo Please check your internet connection and ensure Python/pip are installed correctly.
    pause
    exit /b
)

echo ✅ Dependencies installed successfully.
echo.
echo ==========================================================
echo  STEP 2: RUNNING ANALYSIS SCRIPTS
echo ==========================================================
echo.

echo --- Running: Multi Modal Flight Map ---
:: Open the webpage in the default web browser.
start http://127.0.0.1:8050/
python multi_modal_flight_map.py



echo Click "http://127.0.0.1:8050/" to open the webpage
echo.

pause
