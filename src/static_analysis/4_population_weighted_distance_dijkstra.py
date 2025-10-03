# Import necessary libraries
import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
import math
import geonamescache
import requests
import os

warnings.simplefilter(action='ignore', category=FutureWarning)

# ==============================================================================
# 1. FILE PATHS FOR LOCAL DATA
# ==============================================================================
try:
    base_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(base_path))
    local_data_folder = "data"

    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
except NameError:
    local_data_folder = "../../data"
    LOCAL_ROUTES_PATH = os.path.join(local_data_folder, "local_data_routes.dat")

# ==============================================================================
# 2. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")

# --- Load base online datasets ---
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

# --- Load local datasets if they exist ---
local_routes_df = pd.DataFrame()
try:
    if os.path.exists(LOCAL_ROUTES_PATH):
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
except Exception as e:
    print(f"⚠️ Error reading local files: {e}. Continuing with online data only.")

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
    a = max(0, min(1, a)) # Clamp value
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==============================================================================
# 4. DATA CLEANING AND CONSOLIDATION
# ==============================================================================
airports_cols = ['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source']
routes_cols = ['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment']
airports = pd.read_csv('airports.dat', header=None, names=airports_cols, na_values='\\N')
base_routes = pd.read_csv('routes.dat', header=None, names=routes_cols, na_values='\\N')

airports.dropna(subset=['Latitude', 'Longitude', 'Airport ID'], inplace=True)
airport_coords = {row['Airport ID']: (row['Latitude'], row['Longitude']) for _, row in airports.iterrows()}
iata_to_id = airports.dropna(subset=['IATA', 'Airport ID']).set_index('IATA')['Airport ID'].to_dict()

base_routes.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
base_routes['Source airport ID'] = base_routes['Source airport ID'].astype(int)
base_routes['Destination airport ID'] = base_routes['Destination airport ID'].astype(int)
final_routes_set = set(zip(base_routes['Source airport ID'], base_routes['Destination airport ID']))

if not local_routes_df.empty:
    local_routes_df['Source airport ID'] = local_routes_df['from'].map(iata_to_id)
    local_routes_df['Destination airport ID'] = local_routes_df['to'].map(iata_to_id)
    local_routes_df.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
    local_routes_df['Source airport ID'] = local_routes_df['Source airport ID'].astype(int)
    local_routes_df['Destination airport ID'] = local_routes_df['Destination airport ID'].astype(int)
    for _, row in local_routes_df.iterrows():
        final_routes_set.add((row['Source airport ID'], row['Destination airport ID']))

print(f"Found {len(airports)} airports and {len(final_routes_set)} unique direct routes.")

# ==============================================================================
# 5. GET POPULATION DATA
# ==============================================================================
gc = geonamescache.GeonamesCache()
cities_data = gc.get_cities()
countries_data = gc.get_countries()
country_code_map = {code: data['name'] for code, data in countries_data.items()}
cities_df = pd.DataFrame.from_dict(cities_data.values())
cities_df['country_full'] = cities_df['countrycode'].map(country_code_map)
cities = cities_df[['name', 'country_full', 'population']]
cities.rename(columns={'name': 'City', 'country_full': 'Country', 'population': 'Population'}, inplace=True)
cities.dropna(inplace=True)

airports['city_lower'] = airports['City'].str.lower()
airports['country_lower'] = airports['Country'].str.lower()
cities['city_lower'] = cities['City'].str.lower()
cities['country_lower'] = cities['Country'].str.lower()

airports_with_pop = pd.merge(airports, cities, on=['city_lower', 'country_lower'], how='left')
default_population = 1000
airports_with_pop['Population'].fillna(default_population, inplace=True)
population_map = airports_with_pop.set_index('Airport ID')['Population'].to_dict()

# ==============================================================================
# 6. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
G_weighted = nx.DiGraph()
print("Building weighted graph...")
for source_id, dest_id in tqdm(final_routes_set, desc="Building Graph"):
    if source_id in airport_coords and dest_id in airport_coords:
        source_coords = airport_coords[source_id]
        dest_coords = airport_coords[dest_id]
        distance = haversine(source_coords[0], source_coords[1], dest_coords[0], dest_coords[1])
        G_weighted.add_edge(source_id, dest_id, weight=distance)

airport_nodes = list(G_weighted.nodes())
weights = [population_map.get(node, default_population) for node in airport_nodes]

print(f"Graph with {G_weighted.number_of_nodes()} airports (nodes) and {G_weighted.number_of_edges()} flights (edges).")

# ==============================================================================
# 7. DIJKSTRA'S ALGORITHM WITH POPULATION BIAS
# ==============================================================================
num_samples = 100000
path_distances = []
no_path_count = 0

print(f"Running simulation for {num_samples} population-weighted pairs using Dijkstra's algorithm...")
for _ in tqdm(range(num_samples), desc="Running Analysis 4"):
    if len(airport_nodes) < 2: break
    pair = random.choices(airport_nodes, weights=weights, k=2)
    source_airport, target_airport = pair[0], pair[1]
    while source_airport == target_airport:
        target_airport = random.choices(airport_nodes, weights=weights, k=1)[0]
    try:
        distance = nx.dijkstra_path_length(G_weighted, source=source_airport, target=target_airport, weight='weight')
        path_distances.append(distance)
    except nx.NetworkXNoPath:
        no_path_count += 1

# ==============================================================================
# 8. DATA ANALYSIS AND VISUALIZATION
# ==============================================================================
if path_distances:
    average_distance = sum(path_distances) / len(path_distances)
else:
    average_distance = 0

print("\nPopulation-Weighted Distance Analysis\n")
print(f"Number of random pairs tested: {num_samples}")
print(f"Pairs with a connecting route: {len(path_distances)}")
print(f"Pairs with no connecting route: {no_path_count}")
print(f"Average shortest travel distance: {average_distance:,.2f} km")
print("\n")

plt.style.use('seaborn-v0_8-talk')
plt.figure(figsize=(14, 8))
sns.histplot(path_distances, bins=50, kde=True, color='purple')
plt.axvline(average_distance, color='red', linestyle='--', linewidth=2, label=f'Average Distance: {average_distance:,.2f} km')
plt.title('Distribution of Shortest Flight Distances (Weighted by Population)', fontsize=20)
plt.xlabel('Total Travel Distance (km)', fontsize=15)
plt.ylabel('Frequency', fontsize=15)
plt.legend(fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.gca().get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
plt.xticks(rotation=45)

# --- Save the figure before showing it ---
output_dir = os.path.join(project_root, 'outputs')
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, '4_population_weighted_distance_distribution.png'), dpi=300, bbox_inches='tight')

plt.show()

