@echo off
TITLE Flight Network Analysis Runner

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

echo --- (1/4) Running Basic Degrees of Separation ---
python src/static_analysis/1_basic_degrees_of_separation.py
echo.

echo --- (2/4) Running Unweighted Network Analysis ---
python src/static_analysis/2_unweighted_network_analysis.py
echo.

echo --- (3/4) Running Population Weighted Flights ---
python src/static_analysis/3_population_weighted_flights.py
echo.

echo --- (4/4) Running Population Weighted Distance (Dijkstra) ---
python src/static_analysis/4_population_weighted_distance_dijkstra.py
echo.


echo ==========================================================
echo  All scripts have finished executing.
echo ==========================================================
echo.
pause
