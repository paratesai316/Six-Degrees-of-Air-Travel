# ==============================================================================
# 1. SETUP AND IMPORTS
# ==============================================================================
import pandas as pd
import networkx as nx
import warnings
import math
import numpy as np
import os
import pickle

# Suppress pandas warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)

print("Starting pre-processing... This may take a few minutes.")

# ==============================================================================
# 2. FILE PATHS (RELATIVE TO THIS SCRIPT)
# ==============================================================================
try:
    # This script is in src/flight_network, so we go up two levels for the project root
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_path))
except NameError:
    project_root = "../.." # Fallback for interactive environments

local_data_folder = "Local database"
LOCAL_AIRPORTS_PATH = os.path.join(project_root, local_data_folder, "local_data_airports.dat")
LOCAL_AIRLINES_PATH = os.path.join(project_root, local_data_folder, "local_data_airlines.dat")
LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")

# Define where to save the processed data
PROCESSED_DATA_FOLDER = os.path.join(project_root, "processed_data")
os.makedirs(PROCESSED_DATA_FOLDER, exist_ok=True)
GRAPH_UNWEIGHTED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "graph_unweighted.pkl")
GRAPH_WEIGHTED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "graph_weighted.pkl")
AIRPORT_DICT_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airport_dict.pkl")
AIRPORTS_FILTERED_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airports_filtered.pkl")
DROPDOWN_OPTIONS_PATH = os.path.join(PROCESSED_DATA_FOLDER, "dropdown_options.pkl")
AIRLINE_MAP_PATH = os.path.join(PROCESSED_DATA_FOLDER, "airline_name_map.pkl")

# ==============================================================================
# 3. HELPER FUNCTION: HAVERSINE DISTANCE
# ==============================================================================
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the earth."""
    R = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    a = max(0, min(1, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==============================================================================
# 4. DATA LOADING AND MERGING
# ==============================================================================
print("Loading and pre-processing data...")
try:
    base_airports = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat",
                                header=None, na_values='\\N', names=['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source'])
    base_routes = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
                              header=None, na_values='\\N', names=['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment'])
except Exception as e:
    print(f"Error downloading base data: {e}. Please check your internet connection.")
    exit()

airline_name_map, local_routes_df, local_airports_df = {}, pd.DataFrame(), pd.DataFrame()
if os.path.exists(LOCAL_AIRLINES_PATH):
    try:
        local_airlines = pd.read_csv(LOCAL_AIRLINES_PATH, sep='\t', comment='#', names=['airline-id', 'airline-name'], index_col='airline-id')
        airline_name_map = local_airlines['airline-name'].to_dict()
        print(f"✅ Loaded {len(airline_name_map)} local airline names.")
    except Exception as e:
        print(f"⚠️ Error reading local airlines file: {e}. Airline names may be missing.")
else:
    print("⚠️ Local airlines file not found.")

if os.path.exists(LOCAL_AIRPORTS_PATH):
    try:
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'], engine='python', on_bad_lines='warn')
        print(f"✅ Loaded {len(local_airports_df)} local airports.")
    except Exception as e:
        print(f"⚠️ Error reading local airports file: {e}.")
else:
    print("⚠️ Local airports file not found.")

if os.path.exists(LOCAL_ROUTES_PATH):
    try:
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
    except Exception as e:
        print(f"⚠️ Error reading local routes file: {e}.")
else:
    print("⚠️ Local routes file not found.")

# --- Consolidate and clean airport data ---
base_airports_indexed = base_airports.set_index('IATA')
if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA', 'latitude': 'Latitude', 'longitude': 'Longitude', 'airport-name': 'Name'}, inplace=True)
    local_airports_indexed = local_airports_df.set_index('IATA')
    all_airports = local_airports_indexed.combine_first(base_airports_indexed).reset_index()
else:
    all_airports = base_airports.copy()

airports_filtered = all_airports.dropna(subset=['Latitude', 'Longitude', 'IATA']).copy()
airports_filtered['Airport ID'] = pd.to_numeric(airports_filtered['Airport ID'], errors='coerce')
max_id = airports_filtered['Airport ID'].max()
if pd.isna(max_id): max_id = 0
missing_id_mask = airports_filtered['Airport ID'].isna()
num_missing = missing_id_mask.sum()
if num_missing > 0:
    new_ids = range(int(max_id) + 1, int(max_id) + 1 + num_missing)
    airports_filtered.loc[missing_id_mask, 'Airport ID'] = new_ids
airports_filtered['Airport ID'] = airports_filtered['Airport ID'].astype(int)
airport_dict = airports_filtered.set_index('Airport ID').to_dict('index')
iata_to_id = airports_filtered.set_index('IATA')['Airport ID'].to_dict()

# --- Consolidate routes using a unified IATA-based approach ---
final_routes_iata = set()
base_routes.dropna(subset=['Source airport', 'Destination airport'], inplace=True)
for _, row in base_routes.iterrows():
    final_routes_iata.add((row['Source airport'], row['Destination airport'], row['Airline']))
if not local_routes_df.empty:
    local_routes_df.dropna(subset=['from', 'to'], inplace=True)
    for _, row in local_routes_df.iterrows():
        final_routes_iata.add((row['from'], row['to'], row['airline']))
final_routes = set()
for source_iata, dest_iata, airline in final_routes_iata:
    source_id, dest_id = iata_to_id.get(source_iata), iata_to_id.get(dest_iata)
    if source_id is not None and dest_id is not None:
        final_routes.add((source_id, dest_id, airline))
print(f"Combined into {len(final_routes)} unique routes.")

# ==============================================================================
# 5. BUILD THE NETWORK GRAPHS
# ==============================================================================
print("Building flight network graphs...")
G_unweighted = nx.DiGraph()
G_weighted = nx.DiGraph()
for source_id, dest_id, airline in final_routes:
    if source_id in airport_dict and dest_id in airport_dict:
        G_unweighted.add_edge(source_id, dest_id, airline=airline)
        distance = haversine(airport_dict[source_id]['Latitude'], airport_dict[source_id]['Longitude'], airport_dict[dest_id]['Latitude'], airport_dict[dest_id]['Longitude'])
        G_weighted.add_edge(source_id, dest_id, weight=distance)
degrees = dict(G_unweighted.out_degree())
airports_filtered['degree'] = airports_filtered['Airport ID'].map(degrees).fillna(0)
airports_filtered['size'] = np.log10(airports_filtered['degree'] + 1) * 8 + 3
print("✅ Graph construction complete.")

# ==============================================================================
# 6. PREPARE DATA FOR DASH APP
# ==============================================================================
print("Preparing data for visualization...")
dropdown_options = sorted(
    [{'label': f"{row['Name']} ({row['IATA']}) - {row['City']}, {row['Country']}", 'value': row['Airport ID']}
     for _, row in airports_filtered.iterrows() if pd.notna(row['Name']) and pd.notna(row['IATA'])],
    key=lambda x: x['label']
)
print("✅ Data preparation complete.")

# ==============================================================================
# 7. SAVE PRE-PROCESSED DATA
# ==============================================================================
print("Saving pre-processed data to files...")
try:
    with open(GRAPH_UNWEIGHTED_PATH, 'wb') as f:
        pickle.dump(G_unweighted, f)
    with open(GRAPH_WEIGHTED_PATH, 'wb') as f:
        pickle.dump(G_weighted, f)
    with open(AIRPORT_DICT_PATH, 'wb') as f:
        pickle.dump(airport_dict, f)
    with open(AIRPORTS_FILTERED_PATH, 'wb') as f:
        pickle.dump(airports_filtered, f)
    with open(DROPDOWN_OPTIONS_PATH, 'wb') as f:
        pickle.dump(dropdown_options, f)
    with open(AIRLINE_MAP_PATH, 'wb') as f:
        pickle.dump(airline_name_map, f)
    
    print(f"✅ All data saved to '{PROCESSED_DATA_FOLDER}' folder.")
    print("\nPreprocessing complete. You can now run 'python app.py'.")

except Exception as e:
    print(f"🔥 Error saving data: {e}")

