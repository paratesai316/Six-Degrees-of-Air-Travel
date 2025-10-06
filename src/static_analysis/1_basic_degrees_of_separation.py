import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

# ==============================================================================
# 1. FILE PATHS FOR LOCAL DATA (USING RELATIVE PATHS)
# ==============================================================================
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    local_data_folder = "Local database"
    LOCAL_AIRPORTS_PATH = os.path.join(project_root, local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
    OUTPUT_DIR = os.path.join(project_root, "outputs")
except NameError:
    local_data_folder = "../../Local database"
    LOCAL_AIRPORTS_PATH = os.path.join(local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(local_data_folder, "local_data_routes.dat")
    OUTPUT_DIR = "../../outputs"

# ==============================================================================
# 2. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")

# --- Load base online datasets ---
airports_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
routes_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"
airport_cols = ['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source']
route_cols = ['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment']
base_airports = pd.read_csv(airports_url, names=airport_cols, na_values='\\N')
base_routes = pd.read_csv(routes_url, names=route_cols, na_values='\\N')

# --- Load local datasets if they exist ---
local_airports_df = pd.DataFrame()
local_routes_df = pd.DataFrame()

if os.path.exists(LOCAL_AIRPORTS_PATH):
    try:
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'])
        print(f"✅ Loaded {len(local_airports_df)} local airports.")
    except Exception as e:
        print(f"⚠️ Error reading local airports file: {e}. This file will be skipped.")
else:
    print("ℹ️ Local airports file not found. Continuing with online data only.")

if os.path.exists(LOCAL_ROUTES_PATH):
    try:
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
    except Exception as e:
        print(f"⚠️ Error reading local routes file: {e}. This file will be skipped.")
else:
    print("ℹ️ Local routes file not found. Continuing with online data only.")

# ==============================================================================
# 3. DATA CLEANING AND CONSOLIDATION
# ==============================================================================
# Combine all valid IATA codes from both datasets to create a master list of airports
active_base_airports = base_airports[(base_airports['Type'] == 'airport') & (base_airports['IATA'].notna())]
valid_iata_codes = set(active_base_airports['IATA'])
base_airport_count = len(valid_iata_codes)

if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA'}, inplace=True)
    valid_local_iata = set(local_airports_df['IATA'].dropna())
    new_airports_count = len(valid_local_iata - valid_iata_codes)
    valid_iata_codes.update(valid_local_iata)
    print(f"Added {new_airports_count} new unique airports from local data.")

# Filter base routes
valid_base_routes = base_routes[(base_routes['Stops'] == 0) & (base_routes['Source airport'].isin(valid_iata_codes)) & (base_routes['Destination airport'].isin(valid_iata_codes))]
all_routes_set = set(zip(valid_base_routes['Source airport'], valid_base_routes['Destination airport']))
base_routes_count = len(all_routes_set)
print(f"Loaded {base_routes_count} unique routes from online data.")

# Filter and merge local routes
if not local_routes_df.empty:
    valid_local_routes = local_routes_df[(local_routes_df['stops'] == 0) & (local_routes_df['from'].isin(valid_iata_codes)) & (local_routes_df['to'].isin(valid_iata_codes))]
    for _, row in valid_local_routes.iterrows():
        all_routes_set.add((row['from'], row['to']))
    
    new_routes_count = len(all_routes_set) - base_routes_count
    print(f"Added {new_routes_count} new unique routes from local data.")

print(f"\nFound a total of {len(valid_iata_codes)} active airports and {len(all_routes_set)} unique direct routes.")

# ==============================================================================
# 4. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
G = nx.Graph()
G.add_edges_from(all_routes_set)
graph_nodes = list(G.nodes())
print(f"Graph with {G.number_of_nodes()} airports and {G.number_of_edges()} connections.")

# ==============================================================================
# 5. BREADTH-FIRST SEARCH
# ==============================================================================
num_samples = 100000
path_lengths, unreachable_pairs = [], 0
for _ in tqdm(range(num_samples), desc="Running Analysis 1"):
    if len(graph_nodes) < 2: break
    start_node, end_node = random.sample(graph_nodes, 2)
    try:
        length = nx.shortest_path_length(G, source=start_node, target=end_node)
        path_lengths.append(length)
    except nx.NetworkXNoPath:
        unreachable_pairs += 1

# ==============================================================================
# 6. ANALYSIS AND VISUALIZATION
# ==============================================================================
if path_lengths:
    average_flights = sum(path_lengths) / len(path_lengths)
    print(f"\nAverage number of flights: {average_flights:.2f}")

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 7))
    counts, bins, patches = plt.hist(path_lengths, bins=range(1, max(path_lengths) + 2), align='left', rwidth=0.8, color='#007acc', edgecolor='black')
    
    plt.title('Distribution of Flights to Connect Two Random Airports', fontsize=16)
    plt.xlabel('Number of Flights (Degrees of Separation)', fontsize=12)
    plt.ylabel('Number of Airport Pairs', fontsize=12)
    plt.xticks(range(1, max(path_lengths) + 1))
    plt.grid(axis='y', alpha=0.75)

    for count, patch in zip(counts, patches):
        x = patch.get_x() + patch.get_width() / 2
        y = patch.get_height()
        if y > 0:
            plt.text(x, y + (counts.max() * 0.01), f'{int(count)}', ha='center', va='bottom', fontsize=10, color='gray')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(os.path.join(OUTPUT_DIR, '1_unweighted_flight_distribution.png'), dpi=300, bbox_inches='tight')
    plt.show()
else:
    print("Could not find any connected paths.")

