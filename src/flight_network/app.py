# ==============================================================================
# 1. SETUP AND IMPORTS
# ==============================================================================
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pickle
import os
import plotly.graph_objects as go
import networkx as nx 
import numpy as np 
import math 
import pandas as pd # Make sure all necessary libraries are imported

# Import the layout and callback functions from our new files
from layout import create_layout
from callbacks import register_callbacks

# ==============================================================================
# 2. DEFINE FILE PATHS
# ==============================================================================
try:
    # This script is in src/flight_network, so we go up two levels for the project root
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_path))
except NameError:
    project_root = "../.." # Fallback for interactive environments

PROCESSED_DATA_FOLDER = os.path.join(project_root, "processed_data")
GRAPH_UNWEIGHTED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "graph_unweighted.pkl")
GRAPH_WEIGHTED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "graph_weighted.pkl")
AIRPORT_DICT_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airport_dict.pkl")
AIRPORTS_FILTERED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airports_filtered.pkl")
DROPDOWN_OPTIONS_PATH = os.path.join(PROCESSED_DATA_FOLDER, "dropdown_options.pkl")
AIRLINE_MAP_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airline_name_map.pkl")
ASSETS_PATH = os.path.join(project_root, "assets")

# ==============================================================================
# 3. LOAD PRE-PROCESSED DATA
# ==============================================================================
print("Loading pre-processed data...")
try:
    with open(GRAPH_UNWEIGHTED_PATH, 'rb') as f:
        G_unweighted = pickle.load(f)
    with open(GRAPH_WEIGHTED_PATH, 'rb') as f:
        G_weighted = pickle.load(f)
    with open(AIRPORT_DICT_PATH, 'rb') as f:
        airport_dict = pickle.load(f)
    with open(AIRPORTS_FILTERED_PATH, 'rb') as f:
        airports_filtered = pickle.load(f)
    with open(DROPDOWN_OPTIONS_PATH, 'rb') as f:
        dropdown_options = pickle.load(f)
    with open(AIRLINE_MAP_PATH, 'rb') as f:
        airline_name_map = pickle.load(f)
    print("✅ Pre-processed data loaded successfully.")
except FileNotFoundError:
    print("="*50)
    print("⚠️ ERROR: Pre-processed data not found.")
    print(f"Please run 'python preprocessor.py' first to generate the necessary data files.")
    print("="*50)
    exit()
except Exception as e:
    print(f"Error loading processed data: {e}")
    exit()

# ==============================================================================
# 4. CREATE AND CONFIGURE THE DASH APP
# ==============================================================================
# Dash automatically serves files from a folder named 'assets' in the same directory as the app
app = dash.Dash(__name__, assets_folder=ASSETS_PATH) 
server = app.server
app.title = "Global Flight Network Explorer"

# Set the layout by calling the function from layout.py
# We pass an empty list for options; the callback will populate them
app.layout = create_layout(app, [])

# Register all callbacks
register_callbacks(app, G_unweighted, G_weighted, airport_dict, airports_filtered, airline_name_map, dropdown_options)

# ==============================================================================
# 5. RUN THE APPLICATION
# ==============================================================================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(
        host="0.0.0.0",
        port=port,
        debug=False
    )

