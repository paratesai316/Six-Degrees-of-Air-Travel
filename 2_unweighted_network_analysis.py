# Import necessary libraries
import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings


warnings.simplefilter(action='ignore', category=FutureWarning)

import requests

# List of files to download
files_to_download = {
    "routes.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
    "airports.dat": "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
}

for filename, url in files_to_download.items():
    try:
        response = requests.get(url)
        response.raise_for_status()  
        with open(filename, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {filename}: {e}")
        exit()



#Data loading
airports_cols = [
    'Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO',
    'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST',
    'Tz database time zone', 'Type', 'Source'
]
routes_cols = [
    'Airline', 'Airline ID', 'Source airport', 'Source airport ID',
    'Destination airport', 'Destination airport ID', 'Codeshare',
    'Stops', 'Equipment'
]
airports = pd.read_csv('airports.dat', header=None, names=airports_cols, na_values='\\N')
routes = pd.read_csv('routes.dat', header=None, names=routes_cols, na_values='\\N')

#Data cleaning
routes.dropna(subset=['Source airport ID', 'Destination airport ID'], inplace=True)

routes['Source airport ID'] = routes['Source airport ID'].astype(int)
routes['Destination airport ID'] = routes['Destination airport ID'].astype(int)

print(f"Found {len(airports)} airports and {len(routes)} routes.")

#Airport network graph construction
G = nx.from_pandas_edgelist(
    routes,
    source='Source airport ID',
    target='Destination airport ID',
    create_using=nx.DiGraph()
)

airport_nodes = list(G.nodes())

print(f"Graph with {G.number_of_nodes()} airports (nodes) and {G.number_of_edges()} flights (edges).")

#Breadth-first search to find least number of flights
num_samples = 100000
path_lengths = []
no_path_count = 0

for _ in tqdm(range(num_samples)):
    source_airport, target_airport = random.sample(airport_nodes, 2)

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

plt.title('Distribution of Minimum Flights Between Random Airports', fontsize=20)
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