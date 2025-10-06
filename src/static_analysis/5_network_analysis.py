# ==============================================================================
# 1. SETUP AND IMPORTS
# ==============================================================================
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
import itertools
import tkinter as tk
from tkinter import ttk

# ==============================================================================
# 2. FILE PATHS FOR LOCAL DATA (USING RELATIVE PATHS)
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
# 3. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")
airports_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
routes_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"
airport_cols = ['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source']
route_cols = ['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment']
base_airports = pd.read_csv(airports_url, names=airport_cols, na_values='\\N')
base_routes = pd.read_csv(routes_url, names=route_cols, na_values='\\N')

local_airports_df = pd.DataFrame()
local_routes_df = pd.DataFrame()
if os.path.exists(LOCAL_AIRPORTS_PATH):
    try:
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'], engine='python', on_bad_lines='warn')
    except Exception as e:
        print(f"⚠️ Error reading local airports file: {e}")
if os.path.exists(LOCAL_ROUTES_PATH):
    try:
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
    except Exception as e:
        print(f"⚠️ Error reading local routes file: {e}")

# ==============================================================================
# 4. DATA CLEANING AND CONSOLIDATION
# ==============================================================================
active_base_airports = base_airports[(base_airports['Type'] == 'airport') & (base_airports['IATA'].notna())]
valid_iata_codes = set(active_base_airports['IATA'])
if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA'}, inplace=True)
    valid_iata_codes.update(set(local_airports_df['IATA'].dropna()))

valid_base_routes = base_routes[(base_routes['Stops'] == 0) & (base_routes['Source airport'].isin(valid_iata_codes)) & (base_routes['Destination airport'].isin(valid_iata_codes))]
all_routes_set = set(zip(valid_base_routes['Source airport'], valid_base_routes['Destination airport']))
if not local_routes_df.empty:
    valid_local_routes = local_routes_df[(local_routes_df['stops'] == 0) & (local_routes_df['from'].isin(valid_iata_codes)) & (local_routes_df['to'].isin(valid_iata_codes))]
    for _, row in valid_local_routes.iterrows():
        all_routes_set.add((row['from'], row['to']))

print(f"Found {len(valid_iata_codes)} total active airports and {len(all_routes_set)} unique direct routes.")

# ==============================================================================
# 5. AIRPORT NETWORK GRAPH CONSTRUCTION
# ==============================================================================
# FIX: Use a Directed Graph (DiGraph) for consistency with the web app
G = nx.DiGraph() 
G.add_edges_from(all_routes_set)
graph_nodes = list(G.nodes())
print(f"Constructed full directed graph with {G.number_of_nodes()} airports and {G.number_of_edges()} connections.")

# ==============================================================================
# 6. FULL SHORTEST PATH ANALYSIS
# ==============================================================================
print("\nCalculating shortest paths for all unique directed airport pairs... This will take a significant amount of time.")
path_lengths = []
long_paths = {}
unreachable_pairs = 0

# FIX: Use itertools.permutations to check all directed pairs (A->B and B->A)
node_pairs = itertools.permutations(graph_nodes, 2)
num_pairs = len(graph_nodes) * (len(graph_nodes) - 1)

for source, target in tqdm(node_pairs, total=num_pairs, desc="Analyzing all pairs"):
    try:
        length = nx.shortest_path_length(G, source=source, target=target)
        path_lengths.append(length)
        if length >= 10:
            if length not in long_paths:
                long_paths[length] = []
            # FIX: Show directed path
            long_paths[length].append(f"{source} → {target}") 
    except nx.NetworkXNoPath:
        unreachable_pairs += 1

# ==============================================================================
# 7. ANALYSIS AND VISUALIZATION
# ==============================================================================
if path_lengths:
    average_flights = sum(path_lengths) / len(path_lengths)
    print(f"\nFull Network Analysis Complete:")
    print(f"  Total unique directed pairs analyzed: {num_pairs:,}")
    print(f"  Reachable pairs found: {len(path_lengths):,}")
    print(f"  Unreachable pairs found: {unreachable_pairs:,}")
    print(f"  Average number of flights (for reachable pairs): {average_flights:.2f}")

    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(12, 7))
    counts, bins, patches = plt.hist(path_lengths, bins=range(1, max(path_lengths) + 2), align='left', rwidth=0.8, color='#007acc', edgecolor='black')
    plt.title('Complete Distribution of Flights to Connect Any Two Airports (Directed)', fontsize=16)
    plt.xlabel('Number of Flights (Degrees of Separation)', fontsize=12)
    plt.ylabel('Number of Airport Pairs', fontsize=12)
    plt.xticks(range(1, max(path_lengths) + 1))
    plt.grid(axis='y', alpha=0.75)
    for count, patch in zip(counts, patches):
        if count > 0:
            x = patch.get_x() + patch.get_width() / 2
            y = patch.get_height()
            plt.text(x, y + (counts.max() * 0.01), f'{int(count):,}', ha='center', va='bottom', fontsize=9, color='gray')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(os.path.join(OUTPUT_DIR, '5_full_analysis_distribution_directed.png'), dpi=300, bbox_inches='tight')
    plt.show()

# ==============================================================================
# 8. INTERACTIVE OUTLIER EXPLORER (Tkinter GUI)
# ==============================================================================
def show_long_paths_explorer():
    if not long_paths:
        print("\nNo paths with 10 or more flights were found.")
        return

    window = tk.Tk()
    window.title("Long-Path Route Explorer")
    window.geometry("400x500")

    main_frame = ttk.Frame(window, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    label = ttk.Label(main_frame, text="Select Number of Flights:")
    label.pack(pady=5)
    
    path_options = sorted(long_paths.keys())
    selected_length = tk.StringVar()
    
    dropdown = ttk.Combobox(main_frame, textvariable=selected_length, values=path_options, state="readonly")
    dropdown.pack(fill=tk.X, pady=5)
    if path_options:
        dropdown.set(path_options[0])

    list_frame = ttk.Frame(main_frame)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
    scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=listbox.xview)
    listbox.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def update_list(*args):
        listbox.delete(0, tk.END)
        try:
            length = int(selected_length.get())
            pairs = long_paths.get(length, [])
            for pair in pairs:
                listbox.insert(tk.END, pair)
        except (ValueError, TypeError):
            pass

    selected_length.trace_add("write", update_list)
    update_list()
    window.mainloop()

show_long_paths_explorer()

