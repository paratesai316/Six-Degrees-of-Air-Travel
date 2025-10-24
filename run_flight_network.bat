@echo off
TITLE Global Flight Network Explorer - Launcher

:: Set the path to your application's source folder
set APP_PATH=src\flight_network

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

:: ==========================================================
:: STEP 2: CHECKING FOR PRE-PROCESSED DATA
:: ==========================================================
IF EXIST "processed_data\graph_unweighted.pkl" (
    echo ✅ Pre-processed data found. Skipping data processing.
    GOTO LAUNCH_APP
) ELSE (
    echo ⚠️ Pre-processed data not found.
    echo Running one-time pre-processing script...
    echo This may take several minutes.
    echo.
    python %APP_PATH%\preprocessor.py
    
    if errorlevel 1 (
        echo.
        echo ERROR: Data pre-processing failed.
        echo Please check the script and your data files.
        pause
        exit /b
    )
    echo ✅ Data pre-processing complete.
)
echo.

:: ==========================================================
:: STEP 3: CHOOSE LAUNCH MODE
:: ==========================================================
:LAUNCH_APP
echo.
echo How would you like to run the application?
echo.
echo   [1] Standard Web App (in your browser)
echo   [2] Standalone Desktop App (in its own window)
echo.

CHOICE /C 12 /N /M "Enter your choice (1 or 2): "

IF ERRORLEVEL 2 (
    GOTO STANDALONE
)
IF ERRORLEVEL 1 (
    GOTO BROWSER
)
GOTO LAUNCH_APP


:: ==========================================================
:: STEP 4: LAUNCH BASED ON CHOICE
:: ==========================================================
:BROWSER
echo.
echo Starting the web application...
echo Open your browser and go to http://127.0.0.1:8050/
echo.
python %APP_PATH%\app.py
GOTO END

:STANDALONE
echo.
echo Starting the standalone desktop application...
echo A new window will open shortly.
echo.
python %APP_PATH%\run_standalone.py
GOTO END

:END
echo.
pause

