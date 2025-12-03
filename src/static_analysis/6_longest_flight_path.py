# ==============================================================================
# 1. SETUP AND IMPORTS
# ==============================================================================
import pandas as pd
import networkx as nx
import os
from tqdm import tqdm
import warnings

# Suppress pandas warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)

# ==============================================================================
# 2. FILE PATHS FOR LOCAL DATA (USING RELATIVE PATHS)
# ==============================================================================
try:
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Adjust this depending on where you save this script. 
    # Assuming it's in src/flight_network/ like the app.py
    project_root = os.path.dirname(os.path.dirname(base_path))
    local_data_folder = "Local database"
    
    LOCAL_AIRPORTS_PATH = os.path.join(project_root, local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
except NameError:
    # Fallback
    local_data_folder = "../../Local database"
    LOCAL_AIRPORTS_PATH = os.path.join(local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(local_data_folder, "local_data_routes.dat")

# ==============================================================================
# 3. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")

# --- Load base online datasets ---
try:
    airports = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat",
                           header=None, na_values='\\N', names=['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source'])
    routes = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
                         header=None, na_values='\\N', names=['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment'])
except Exception as e:
    print(f"Error downloading base data: {e}")
    exit()

# --- Load local datasets ---
local_airports_df = pd.DataFrame()
local_routes_df = pd.DataFrame()

if os.path.exists(LOCAL_AIRPORTS_PATH):
    try:
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'], engine='python', on_bad_lines='warn')
        print(f"✅ Loaded {len(local_airports_df)} local airports.")
    except Exception as e:
        print(f"⚠️ Error reading local airports file: {e}")

if os.path.exists(LOCAL_ROUTES_PATH):
    try:
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
    except Exception as e:
        print(f"⚠️ Error reading local routes file: {e}")

# --- Consolidate Data ---
# 1. Airports
all_airports = airports.copy()
if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA', 'latitude': 'Latitude', 'longitude': 'Longitude', 'airport-name': 'Name'}, inplace=True)
    # Fill missing cols with NA so concat works
    for col in all_airports.columns:
        if col not in local_airports_df:
            local_airports_df[col] = pd.NA
    # Merge
    all_airports = pd.concat([all_airports, local_airports_df]).drop_duplicates(subset=['IATA'], keep='last')

# Clean up airports
airports_filtered = all_airports.dropna(subset=['IATA']).copy()
# Ensure Airport ID exists
airports_filtered['Airport ID'] = pd.to_numeric(airports_filtered['Airport ID'], errors='coerce')
max_id = airports_filtered['Airport ID'].max()
if pd.isna(max_id): max_id = 0
missing_ids = airports_filtered['Airport ID'].isna()
if missing_ids.sum() > 0:
    new_ids = range(int(max_id) + 1, int(max_id) + 1 + missing_ids.sum())
    airports_filtered.loc[missing_ids, 'Airport ID'] = new_ids

airports_filtered['Airport ID'] = airports_filtered['Airport ID'].astype(int)
# Create lookups
airport_dict = airports_filtered.set_index('Airport ID').to_dict('index')
iata_to_id = airports_filtered.set_index('IATA')['Airport ID'].to_dict()
id_to_name = airports_filtered.set_index('Airport ID')['Name'].to_dict()
id_to_iata = airports_filtered.set_index('Airport ID')['IATA'].to_dict()

# 2. Routes
final_routes = set()

# Base routes
routes.dropna(subset=['Source airport', 'Destination airport'], inplace=True)
for _, row in routes.iterrows():
    src_id = iata_to_id.get(row['Source airport'])
    dest_id = iata_to_id.get(row['Destination airport'])
    if src_id and dest_id:
        final_routes.add((src_id, dest_id))

# Local routes
if not local_routes_df.empty:
    local_routes_df.dropna(subset=['from', 'to'], inplace=True)
    for _, row in local_routes_df.iterrows():
        src_id = iata_to_id.get(row['from'])
        dest_id = iata_to_id.get(row['to'])
        if src_id and dest_id:
            final_routes.add((src_id, dest_id))

print(f"Total Airports: {len(airports_filtered)}")
print(f"Total Routes: {len(final_routes)}")

# ==============================================================================
# 4. GRAPH ANALYSIS
# ==============================================================================
print("\nBuilding network graph...")
G = nx.DiGraph()
G.add_edges_from(final_routes)

print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
print("Calculating all-pairs shortest paths. This may take 1-3 minutes...")

# We need to find the maximum shortest path length (Diameter of the graph)
# Since the graph might not be strongly connected, we iterate over all nodes
max_length = 0
longest_path = []
start_node = None
end_node = None

# Use all_pairs_shortest_path_length (efficient generator)
# We wrap it in tqdm for a progress bar
for source, targets in tqdm(nx.all_pairs_shortest_path_length(G), total=G.number_of_nodes()):
    for target, length in targets.items():
        if length > max_length:
            max_length = length
            start_node = source
            end_node = target

# Reconstruct the actual path for the longest route found
if start_node is not None and end_node is not None:
    longest_path = nx.shortest_path(G, source=start_node, target=end_node)

# ==============================================================================
# 5. RESULTS
# ==============================================================================
print("\n" + "="*60)
print("LONGEST OPTIMAL FLIGHT PATH FOUND")
print("="*60)

if start_node and end_node:
    start_name = id_to_name.get(start_node, "Unknown")
    start_iata = id_to_iata.get(start_node, "N/A")
    end_name = id_to_name.get(end_node, "Unknown")
    end_iata = id_to_iata.get(end_node, "N/A")

    print(f"\nFrom: {start_name} ({start_iata})")
    print(f"To:   {end_name} ({end_iata})")
    print(f"\nTotal Flights Required: {max_length}")
    print("-" * 60)
    
    # Print the full itinerary
    print("Itinerary:")
    for i, node_id in enumerate(longest_path):
        name = id_to_name.get(node_id, "Unknown")
        iata = id_to_iata.get(node_id, "N/A")
        
        if i == 0:
            print(f"  Start: {name} ({iata})")
        else:
            print(f"  {i}. Fly to {name} ({iata})")
    print("-" * 60)
else:
    print("No paths found (Graph might be empty or disconnected).")

print("\nAnalysis complete.")

"""
### How to Run It

1.  Make sure your `Local database` folder is in the correct location (relative to where you save this script).
2.  Run the script from your terminal:

    ```bash
    python src/flight_network/7_longest_flight_path.py"""