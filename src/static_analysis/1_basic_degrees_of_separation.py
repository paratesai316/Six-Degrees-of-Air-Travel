import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
from tqdm import tqdm
import os

# ==============================================================================
# 1. FILE PATHS FOR LOCAL DATA
# ==============================================================================
try:
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from 'src/static_analysis' to the project root
    project_root = os.path.dirname(os.path.dirname(base_path))
    local_data_folder = "data" # Assumes 'data' folder is at the project root

    LOCAL_AIRPORTS_PATH = os.path.join(project_root, local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
except NameError:
    # Fallback for interactive environments
    local_data_folder = "../../data"
    LOCAL_AIRPORTS_PATH = os.path.join(local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(local_data_folder, "local_data_routes.dat")

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
try:
    if os.path.exists(LOCAL_AIRPORTS_PATH):
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'])
        print(f"✅ Loaded {len(local_airports_df)} local airports.")
    if os.path.exists(LOCAL_ROUTES_PATH):
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
except Exception as e:
    print(f"⚠️ Error reading local files: {e}. Continuing with online data only.")

# ==============================================================================
# 3. DATA CLEANING AND CONSOLIDATION
# ==============================================================================
# Combine all valid IATA codes from both datasets
active_base_airports = base_airports[(base_airports['Type'] == 'airport') & (base_airports['IATA'].notna())]
valid_iata_codes = set(active_base_airports['IATA'])

if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA'}, inplace=True)
    valid_local_iata = set(local_airports_df['IATA'].dropna())
    valid_iata_codes.update(valid_local_iata)

# Filter base routes
valid_base_routes = base_routes[
    (base_routes['Stops'] == 0) &
    (base_routes['Source airport'].isin(valid_iata_codes)) &
    (base_routes['Destination airport'].isin(valid_iata_codes))
]

# Combine routes from both sources
all_routes = []
for _, row in valid_base_routes.iterrows():
    all_routes.append({'source': row['Source airport'], 'dest': row['Destination airport']})

if not local_routes_df.empty:
    valid_local_routes = local_routes_df[
        (local_routes_df['stops'] == 0) &
        (local_routes_df['from'].isin(valid_iata_codes)) &
        (local_routes_df['to'].isin(valid_iata_codes))
    ]
    for _, row in valid_local_routes.iterrows():
        all_routes.append({'source': row['from'], 'dest': row['to']})

# Create a final DataFrame of unique routes
final_routes_df = pd.DataFrame(all_routes).drop_duplicates()

print(f"Found {len(valid_iata_codes)} active airports and {len(final_routes_df)} unique direct routes.")

# ==============================================================================
# 4. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
G = nx.Graph()
for _, row in final_routes_df.iterrows():
    G.add_edge(row['source'], row['dest'])

graph_nodes = list(G.nodes())
print(f"Graph with {G.number_of_nodes()} airports and {G.number_of_edges()} connections.")

# ==============================================================================
# 5. BREADTH-FIRST SEARCH TO FIND LEAST NUMBER OF FLIGHTS
# ==============================================================================
num_samples = 100000
path_lengths = []
unreachable_pairs = 0

for _ in tqdm(range(num_samples), desc="Running Analysis 1"):
    if len(graph_nodes) < 2: break # Avoid error if graph is too small
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
    print(f"\nAverage number of flights between any two airports: {average_flights:.2f}")
    print(f"   (Based on {len(path_lengths)} reachable pairs)")
    if unreachable_pairs > 0:
        print(f"   Found {unreachable_pairs} pairs that were not connected at all.")

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 7))
    plt.hist(path_lengths, bins=range(1, max(path_lengths) + 2), align='left', rwidth=0.8, color='#007acc', edgecolor='black')
    plt.title('Distribution of Flights Needed to Connect Two Random Airports', fontsize=16)
    plt.xlabel('Number of Flights (Degrees of Separation)', fontsize=12)
    plt.ylabel('Number of Airport Pairs', fontsize=12)
    plt.xticks(range(1, max(path_lengths) + 1))
    plt.grid(axis='y', alpha=0.75)

    # --- Save the figure before showing it ---
    output_dir = os.path.join(project_root, 'outputs')
    os.makedirs(output_dir, exist_ok=True) # Ensure the 'outputs' directory exists
    plt.savefig(os.path.join(output_dir, '1_unweighted_flight_distribution.png'), dpi=300, bbox_inches='tight')
    
    plt.show()
else:
    print("Could not find any connected paths in the samples.")

