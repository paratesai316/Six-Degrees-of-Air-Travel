import pandas as pd
import networkx as nx
import random
import matplotlib.pyplot as plt
from tqdm import tqdm

#Data loading
print("Loading airport and route data")

airports_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
routes_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"

airport_cols = ['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source']
route_cols = ['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment']

airports = pd.read_csv(airports_url, names=airport_cols, na_values='\\N')
routes = pd.read_csv(routes_url, names=route_cols, na_values='\\N')

#Data cleaning
active_airports = airports[(airports['Type'] == 'airport') & (airports['IATA'].notna())]
valid_iata_codes = set(active_airports['IATA'])

valid_routes = routes[
    (routes['Stops'] == 0) &
    (routes['Source airport'].isin(valid_iata_codes)) &
    (routes['Destination airport'].isin(valid_iata_codes))
]

print(f"Found {len(valid_iata_codes)} active airports and {len(valid_routes)} direct routes.")

#Airport network graph construction

G = nx.Graph()

for index, row in valid_routes.iterrows():
    source = row['Source airport']
    dest = row['Destination airport']
    G.add_edge(source, dest)

graph_nodes = list(G.nodes())
print(f"Graph with {G.number_of_nodes()} airports and {G.number_of_edges()} connections.")

#Breadth-first search to find least number of flights
num_samples = 100000

path_lengths = []
unreachable_pairs = 0

for _ in tqdm(range(num_samples)):
    start_node, end_node = random.sample(graph_nodes, 2)

    try:
        length = nx.shortest_path_length(G, source=start_node, target=end_node)
        path_lengths.append(length)
    except nx.NetworkXNoPath:
        unreachable_pairs += 1

#Analysis and vizualization

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
    plt.show()
else:
    print("Could not find any connected paths in the samples.")