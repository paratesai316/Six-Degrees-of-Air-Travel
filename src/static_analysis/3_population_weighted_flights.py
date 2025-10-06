# Import necessary libraries
import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings
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
    local_data_folder = "Local database"

    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
except NameError:
    local_data_folder = "../../Local database"
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
# 4. GET POPULATION DATA
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
# 5. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
G = nx.DiGraph()
G.add_edges_from(final_routes_set)
airport_nodes = list(G.nodes())
weights = [population_map.get(node, default_population) for node in airport_nodes]

print(f"Graph with {G.number_of_nodes()} airports (nodes) and {G.number_of_edges()} flights (edges).")

# ==============================================================================
# 6. BREADTH-FIRST SEARCH WITH POPULATION BIAS
# ==============================================================================
num_samples = 100000
path_lengths = []
no_path_count = 0

for _ in tqdm(range(num_samples), desc="Running Analysis 3"):
    if len(airport_nodes) < 2: break
    pair = random.choices(airport_nodes, weights=weights, k=2)
    source_airport, target_airport = pair[0], pair[1]
    while source_airport == target_airport:
        target_airport = random.choices(airport_nodes, weights=weights, k=1)[0]
    try:
        length = nx.shortest_path_length(G, source=source_airport, target=target_airport)
        path_lengths.append(length)
    except nx.NetworkXNoPath:
        no_path_count += 1

# ==============================================================================
# 7. ANALYSIS AND VISUALIZATION
# ==============================================================================
if path_lengths:
    average_flights = sum(path_lengths) / len(path_lengths)
    most_common_flights = max(set(path_lengths), key=path_lengths.count)
else:
    average_flights = 0
    most_common_flights = 0

print("\nPopulation-Weighted Analysis Results\n")
print(f"Number of random pairs tested: {num_samples}")
print(f"Pairs with a connecting route: {len(path_lengths)}")
print(f"Pairs with no connecting route: {no_path_count}")
print(f"Average number of flights between connected airports: {average_flights:.2f}")
print(f"Most common number of flights needed: {most_common_flights}")
print("\n")

plt.style.use('seaborn-v0_8-talk')
plt.figure(figsize=(14, 8))
ax = sns.countplot(x=path_lengths, palette='viridis', order=sorted(set(path_lengths)))
plt.title('Distribution of Minimum Flights (Weighted by Population)', fontsize=20)
plt.xlabel('Number of Flights (Path Length)', fontsize=15)
plt.ylabel('Frequency (Number of Airport Pairs)', fontsize=15)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
for p in ax.patches:
    ax.annotate(f'{p.get_height()}', (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', fontsize=11, color='gray', xytext=(0, 10), textcoords='offset points')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# --- Save the figure before showing it ---
output_dir = os.path.join(project_root, 'outputs')
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, '3_population_weighted_flight_distribution.png'), dpi=300, bbox_inches='tight')

plt.show()

