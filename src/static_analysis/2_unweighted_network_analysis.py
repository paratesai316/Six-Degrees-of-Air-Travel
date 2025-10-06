import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
import requests
import os

warnings.simplefilter(action='ignore', category=FutureWarning)

# ==============================================================================
# 1. FILE PATHS FOR LOCAL DATA (USING RELATIVE PATHS)
# ==============================================================================
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    local_data_folder = "Local database"
    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
    OUTPUT_DIR = os.path.join(project_root, "outputs")
except NameError:
    local_data_folder = "../../Local database"
    LOCAL_ROUTES_PATH = os.path.join(local_data_folder, "local_data_routes.dat")
    OUTPUT_DIR = "../../outputs"

# ==============================================================================
# 2. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")

files_to_download = {
    "routes.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
    "airports.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
}
for filename, url in files_to_download.items():
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)

local_routes_df = pd.DataFrame()

# ==============================================================================
# 3. DATA CLEANING AND CONSOLIDATION
# ==============================================================================
airports_cols = ['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source']
routes_cols = ['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment']
airports = pd.read_csv('airports.dat', header=None, names=airports_cols, na_values='\\N')
base_routes = pd.read_csv('routes.dat', header=None, names=routes_cols, na_values='\\N')

iata_to_id = airports.dropna(subset=['IATA', 'Airport ID']).set_index('IATA')['Airport ID'].to_dict()

base_routes.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
base_routes['Source airport ID'] = base_routes['Source airport ID'].astype(int)
base_routes['Destination airport ID'] = base_routes['Destination airport ID'].astype(int)
final_routes_set = set(zip(base_routes['Source airport ID'], base_routes['Destination airport ID']))
base_routes_count = len(final_routes_set)
print(f"Loaded {base_routes_count} unique routes from online data.")


if not local_routes_df.empty:
    local_routes_df['Source airport ID'] = local_routes_df['from'].map(iata_to_id)
    local_routes_df['Destination airport ID'] = local_routes_df['to'].map(iata_to_id)
    local_routes_df.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
    local_routes_df['Source airport ID'] = local_routes_df['Source airport ID'].astype(int)
    local_routes_df['Destination airport ID'] = local_routes_df['Destination airport ID'].astype(int)
    
    for _, row in local_routes_df.iterrows():
        final_routes_set.add((row['Source airport ID'], row['Destination airport ID']))

    new_routes_count = len(final_routes_set) - base_routes_count
    print(f"Added {new_routes_count} new unique routes from local data.")

print(f"\nFound a total of {len(airports)} airports and {len(final_routes_set)} unique direct routes.")

# ==============================================================================
# 4. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
G = nx.DiGraph()
G.add_edges_from(final_routes_set)

airport_nodes = list(G.nodes())
print(f"Graph with {G.number_of_nodes()} airports (nodes) and {G.number_of_edges()} flights (edges).")

# ==============================================================================
# 5. BREADTH-FIRST SEARCH TO FIND LEAST NUMBER OF FLIGHTS
# ==============================================================================
num_samples = 100000
path_lengths = []
no_path_count = 0

for _ in tqdm(range(num_samples), desc="Running Analysis 2"):
    if len(airport_nodes) < 2: break
    source_airport, target_airport = random.sample(airport_nodes, 2)
    try:
        length = nx.shortest_path_length(G, source=source_airport, target=target_airport)
        path_lengths.append(length)
    except nx.NetworkXNoPath:
        no_path_count += 1

# ==============================================================================
# 6. ANALYSIS AND VISUALIZATION
# ==============================================================================
if path_lengths:
    average_flights = sum(path_lengths) / len(path_lengths)
    most_common_flights = max(set(path_lengths), key=path_lengths.count)
else:
    average_flights = 0
    most_common_flights = 0

print("\nAnalysis Results")
print(f"Number of random pairs tested: {num_samples}")
print(f"Pairs with a connecting route: {len(path_lengths)}")
print(f"Pairs with no connecting route: {no_path_count}")
print(f"Average number of flights between connected airports: {average_flights:.2f}")
print(f"Most common number of flights needed: {most_common_flights}")
print("\n")

plt.style.use('seaborn-v0_8-talk')
plt.figure(figsize=(14, 8))

ax = sns.countplot(x=path_lengths, palette='viridis', order=sorted(set(path_lengths)))

plt.title('Distribution of Minimum Flights Between Random Airports (Combined Data)', fontsize=20)
plt.xlabel('Number of Flights (Path Length)', fontsize=15)
plt.ylabel('Frequency (Number of Airport Pairs)', fontsize=15)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

for p in ax.patches:
    ax.annotate(f'{p.get_height()}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', fontsize=11, color='gray', xytext=(0, 10),
                textcoords='offset points')

plt.grid(axis='y', linestyle='--', alpha=0.7)

os.makedirs(OUTPUT_DIR, exist_ok=True)
plt.savefig(os.path.join(OUTPUT_DIR, '2_unweighted_digraph_flight_distribution.png'), dpi=300, bbox_inches='tight')

plt.show()