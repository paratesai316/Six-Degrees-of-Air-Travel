import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm  # Use the standard tqdm for .py files
import warnings
import geonamescache
import requests

warnings.simplefilter(action='ignore', category=FutureWarning)

#Download the files
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
routes.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)
routes['Source airport ID'] = routes['Source airport ID'].astype(int)
routes['Destination airport ID'] = routes['Destination airport ID'].astype(int)

#retreive population data from geonamescache library
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
G = nx.from_pandas_edgelist(
    routes,
    source='Source airport ID',
    target='Destination airport ID',
    create_using=nx.DiGraph()
)
airport_nodes = list(G.nodes())

weights = [population_map.get(node, default_population) for node in airport_nodes]

#Run simulation
num_samples = 100000
path_lengths = []
no_path_count = 0

print(f"Simulation for {num_samples} random airport pairs")
for _ in tqdm(range(num_samples)):
    pair = random.choices(airport_nodes, weights=weights, k=2)
    source_airport, target_airport = pair[0], pair[1]

    while source_airport == target_airport:
        target_airport = random.choices(airport_nodes, weights=weights, k=1)[0]

    try:
        length = nx.shortest_path_length(G, source=source_airport, target=target_airport)
        path_lengths.append(length)
    except nx.NetworkXNoPath:
        no_path_count += 1

#Analysis and vizualization
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
    ax.annotate(f'{p.get_height()}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center', fontsize=11, color='gray', xytext=(0, 10),
                textcoords='offset points')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()