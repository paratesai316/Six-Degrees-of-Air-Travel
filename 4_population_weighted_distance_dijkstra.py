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

warnings.simplefilter(action='ignore', category=FutureWarning)

files_to_download = {
    "routes.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
    "airports.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
}
print("Downloading required data files...")
for filename, url in files_to_download.items():
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {filename}: {e}")
        exit()


#Haversine distance between 2 coordinates function
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the earth."""
    R = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


#Data loading and cleaning
airports_cols = [
    'Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude',
    'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source'
]
routes_cols = [
    'Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport',
    'Destination airport ID', 'Codeshare', 'Stops', 'Equipment'
]
airports = pd.read_csv('airports.dat', header=None, names=airports_cols, na_values='\\N')
routes = pd.read_csv('routes.dat', header=None, names=routes_cols, na_values='\\N')

airports.dropna(subset=['Latitude', 'Longitude', 'Airport ID'], inplace=True)
routes.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
airports['Airport ID'] = airports['Airport ID'].astype(int)
routes['Source airport ID'] = routes['Source airport ID'].astype(int)
routes['Destination airport ID'] = routes['Destination airport ID'].astype(int)

airport_coords = {row['Airport ID']: (row['Latitude'], row['Longitude']) for _, row in airports.iterrows()}

#Get population data and merge with airport location data
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

#Airport network graph construction and bias weightage added
G_weighted = nx.DiGraph()
for _, route in tqdm(routes.iterrows(), total=routes.shape[0]):
    source_id = route['Source airport ID']
    dest_id = route['Destination airport ID']
    if source_id in airport_coords and dest_id in airport_coords:
        source_coords = airport_coords[source_id]
        dest_coords = airport_coords[dest_id]
        distance = haversine(source_coords[0], source_coords[1], dest_coords[0], dest_coords[1])
        G_weighted.add_edge(source_id, dest_id, weight=distance)

airport_nodes = list(G_weighted.nodes())
weights = [population_map.get(node, default_population) for node in airport_nodes]

#Run dijkstra's algorithm to find least distance between airports with weighted bias for random selection of airport
num_samples = 100000
path_distances = []
no_path_count = 0

print(f"Simulation for {num_samples} population-weighted pairs using Dijkstra's algorithm")
for _ in tqdm(range(num_samples)):
    pair = random.choices(airport_nodes, weights=weights, k=2)
    source_airport, target_airport = pair[0], pair[1]
    while source_airport == target_airport:
        target_airport = random.choices(airport_nodes, weights=weights, k=1)[0]

    try:
        distance = nx.dijkstra_path_length(G_weighted, source=source_airport, target=target_airport, weight='weight')
        path_distances.append(distance)
    except nx.NetworkXNoPath:
        no_path_count += 1

#Data analysis and visualization
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
plt.show()