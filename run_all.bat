@echo off
TITLE Flight Network Analysis Runner

:: This batch file installs all required Python packages and then
:: runs the four analysis scripts in sequence.

echo ==========================================================
echo  STEP 1: INSTALLING PYTHON DEPENDENCIES
echo ==========================================================
echo.
echo Installing pandas, networkx, matplotlib, seaborn, tqdm, requests, and geonamescache...
echo This may take a few minutes. Please wait.
echo.

:: Install all packages at once. The '> nul' part hides the verbose installation output for a cleaner look.
pip install pandas networkx matplotlib seaborn tqdm requests geonamescache > nul

:: Check if the installation was successful. 'errorlevel 1' means an error occurred.
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
python 1_basic_degrees_of_separation.py
echo.

echo --- (2/4) Running Unweighted Network Analysis ---
python 2_unweighted_network_analysis.py
echo.
echo --- (3/4) Running Population Weighted Flights ---
python 3_population_weighted_flights.py
echo.

echo --- (4/4) Running Population Weighted Distance (Dijkstra) ---
python 4_population_weighted_distance_dijkstra.py
echo.

echo ==========================================================
echo  All scripts have finished executing.
echo ==========================================================
echo.
pause