# ==============================================================================
# 1. SETUP AND IMPORTS
# ==============================================================================
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.colors # Added for color handling
import os
import math
from tqdm import tqdm
import warnings

# Suppress pandas warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)

# ==============================================================================
# 2. FILE PATHS FOR LOCAL DATA
# ==============================================================================
try:
    # Get the directory of the current script (src/static_analysis)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate two levels up to the project root
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    local_data_folder = "Local database"
    LOCAL_AIRPORTS_PATH = os.path.join(project_root, local_data_folder, "local_data_airports.dat")
    LOCAL_ROUTES_PATH = os.path.join(project_root, local_data_folder, "local_data_routes.dat")
    OUTPUT_DIR = os.path.join(project_root, "outputs")
except NameError:
    # Fallback for interactive environments
    LOCAL_AIRPORTS_PATH = "../../Local database/local_data_airports.dat"
    LOCAL_ROUTES_PATH = "../../Local database/local_data_routes.dat"
    OUTPUT_DIR = "../../outputs"

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance (in km) between two points."""
    R = 6371.0
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    a = max(0, min(1, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==============================================================================
# 4. DATA LOADING AND MERGING
# ==============================================================================
print("Loading airport and route data...")

# --- Load base online datasets ---
try:
    airports = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat",
                           header=None, na_values='\\N', names=['Airport ID', 'Name', 'City', 'Country', 'IATA', 'ICAO', 'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST', 'Tz database time zone', 'Type', 'Source'])
    routes = pd.read_csv("https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat",
                         header=None, na_values='\\N', names=['Airline', 'Airline ID', 'Source airport', 'Source airport ID', 'Destination airport', 'Destination airport ID', 'Codeshare', 'Stops', 'Equipment'])
except Exception as e:
    print(f"Error downloading base data: {e}")
    exit()

# --- Load local datasets ---
local_airports_df = pd.DataFrame()
local_routes_df = pd.DataFrame()

if os.path.exists(LOCAL_AIRPORTS_PATH):
    try:
        local_airports_df = pd.read_csv(LOCAL_AIRPORTS_PATH, sep='\t', comment='#', names=['airport-id', 'latitude', 'longitude', 'airport-name'], engine='python', on_bad_lines='warn')
        print(f"✅ Loaded {len(local_airports_df)} local airports.")
    except Exception as e:
        print(f"⚠️ Error reading local airports file: {e}")

if os.path.exists(LOCAL_ROUTES_PATH):
    try:
        local_routes_df = pd.read_csv(LOCAL_ROUTES_PATH, sep='\t', comment='#', names=['airline', 'from', 'to', 'codeshare', 'stops', 'equipment'])
        print(f"✅ Loaded {len(local_routes_df)} local routes.")
    except Exception as e:
        print(f"⚠️ Error reading local routes file: {e}")

# --- Consolidate Data ---
all_airports = airports.copy()
if not local_airports_df.empty:
    local_airports_df.rename(columns={'airport-id': 'IATA', 'latitude': 'Latitude', 'longitude': 'Longitude', 'airport-name': 'Name'}, inplace=True)
    for col in all_airports.columns:
        if col not in local_airports_df:
            local_airports_df[col] = pd.NA
    all_airports = pd.concat([all_airports, local_airports_df]).drop_duplicates(subset=['IATA'], keep='last')

airports_filtered = all_airports.dropna(subset=['Latitude', 'Longitude', 'IATA']).copy()
airports_filtered['Airport ID'] = pd.to_numeric(airports_filtered['Airport ID'], errors='coerce')
max_id = airports_filtered['Airport ID'].max()
if pd.isna(max_id): max_id = 0
missing_ids = airports_filtered['Airport ID'].isna()
if missing_ids.sum() > 0:
    airports_filtered.loc[missing_ids, 'Airport ID'] = range(int(max_id) + 1, int(max_id) + 1 + missing_ids.sum())

airports_filtered['Airport ID'] = airports_filtered['Airport ID'].astype(int)
airport_dict = airports_filtered.set_index('Airport ID').to_dict('index')
iata_to_id = airports_filtered.set_index('IATA')['Airport ID'].to_dict()

# --- Consolidate Routes ---
final_routes = set()
routes.dropna(subset=['Source airport', 'Destination airport'], inplace=True)
for _, row in routes.iterrows():
    src_id = iata_to_id.get(row['Source airport'])
    dest_id = iata_to_id.get(row['Destination airport'])
    if src_id and dest_id:
        final_routes.add((src_id, dest_id))

if not local_routes_df.empty:
    local_routes_df.dropna(subset=['from', 'to'], inplace=True)
    for _, row in local_routes_df.iterrows():
        src_id = iata_to_id.get(row['from'])
        dest_id = iata_to_id.get(row['to'])
        if src_id and dest_id:
            final_routes.add((src_id, dest_id))

print(f"Total Airports: {len(airports_filtered)}")
print(f"Total Unique Routes: {len(final_routes)}")

# ==============================================================================
# 5. GRAPH CONSTRUCTION & MST CALCULATION
# ==============================================================================
print("\nBuilding weighted graph and calculating MST...")
G = nx.Graph() # MST requires an Undirected Graph

# Add edges with distance as weight
for u, v in tqdm(final_routes, desc="Adding edges"):
    if u in airport_dict and v in airport_dict:
        dist = haversine(airport_dict[u]['Latitude'], airport_dict[u]['Longitude'], 
                         airport_dict[v]['Latitude'], airport_dict[v]['Longitude'])
        G.add_edge(u, v, weight=dist)

# Extract Largest Connected Component (MST is only defined for connected graphs)
largest_cc = max(nx.connected_components(G), key=len)
G_connected = G.subgraph(largest_cc).copy()
print(f"Calculating MST for largest connected component ({G_connected.number_of_nodes()} airports)...")

# Compute Minimum Spanning Tree
T = nx.minimum_spanning_tree(G_connected, weight='weight')

print(f"\nMST Computed:")
print(f"  Nodes (Airports): {T.number_of_nodes()}")
print(f"  Edges (Essential Routes): {T.number_of_edges()}")

# ==============================================================================
# 6. VISUALIZATION (PLOTLY MAP)
# ==============================================================================
print("Generating interactive map with distance-based coloring...")

fig = go.Figure()

# 1. Collect edge data and weights
edges_data = []
distances = []
for u, v, d in T.edges(data=True):
    dist = d['weight']
    edges_data.append((u, v, dist))
    distances.append(dist)

if not distances:
    print("No edges to display.")
    exit()

min_dist = min(distances)
max_dist = max(distances)

# 2. Configure Color Scale (e.g., Turbo, Plasma, Viridis)
# We'll use 'Turbo' for high contrast between short and long flights
colorscale_name = 'Turbo'
NUM_BINS = 20
color_list = plotly.colors.sample_colorscale(colorscale_name, [n/(NUM_BINS-1) for n in range(NUM_BINS)])

# 3. Bin edges by distance to create colored traces
# This groups lines of similar length so we don't have to create thousands of traces (which is slow)
bins_lons = [[] for _ in range(NUM_BINS)]
bins_lats = [[] for _ in range(NUM_BINS)]

for u, v, dist in tqdm(edges_data, desc="Grouping edges by length"):
    if max_dist == min_dist:
        norm = 0
    else:
        norm = (dist - min_dist) / (max_dist - min_dist)
    
    bin_idx = int(norm * (NUM_BINS - 1))
    start = airport_dict[u]
    end = airport_dict[v]
    
    # Plotly Scattergeo automatically draws great circles for long lines
    bins_lons[bin_idx].extend([start['Longitude'], end['Longitude'], None])
    bins_lats[bin_idx].extend([start['Latitude'], end['Latitude'], None])

# 4. Add traces for each color bin
for i in range(NUM_BINS):
    if not bins_lons[i]: continue
    
    fig.add_trace(go.Scattergeo(
        lon=bins_lons[i],
        lat=bins_lats[i],
        mode='lines',
        line=dict(width=1.5, color=color_list[i]),
        opacity=0.8,
        hoverinfo='skip',
        showlegend=False
    ))

# 5. Add Nodes (Airports)
node_lons = [airport_dict[n]['Longitude'] for n in T.nodes()]
node_lats = [airport_dict[n]['Latitude'] for n in T.nodes()]
# Updated hover text to include connection count (degree in MST)
node_text = [f"{airport_dict[n]['Name']} ({airport_dict[n]['IATA']})<br>Connections in MST: {T.degree[n]}" for n in T.nodes()]

fig.add_trace(go.Scattergeo(
    lon=node_lons,
    lat=node_lats,
    mode='markers',
    marker=dict(size=3, color='#ffffff', opacity=0.8),
    text=node_text,
    name='Airport',
    hoverinfo='text'
))

# 6. Add an invisible marker trace just to show the Color Bar
fig.add_trace(go.Scattergeo(
    lon=[0], lat=[0],
    mode='markers',
    marker=dict(
        size=0,
        color=[min_dist, max_dist],
        colorscale=colorscale_name,
        cmin=min_dist,
        cmax=max_dist,
        showscale=True,
        colorbar=dict(
            title=dict(text="Flight Distance (km)", side="right"),
            thickness=15,
            len=0.5,
            xanchor="left",
            x=1.02
        )
    ),
    showlegend=False,
    hoverinfo='none',
    visible=True
))

fig.update_layout(
    title_text='Global Flight Network: Minimum Spanning Tree (Colored by Distance)',
    showlegend=False,
    geo=dict(
        projection_type='equirectangular',
        showland=True,
        landcolor='rgb(20, 20, 20)',
        showocean=True,
        oceancolor='rgb(10, 10, 10)',
        showcountries=True,
        countrycolor='rgb(40, 40, 40)',
        bgcolor='rgb(0, 0, 0)'
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    paper_bgcolor='rgb(0,0,0)',
    font=dict(color='white')
)

# Save to file
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_file = os.path.join(OUTPUT_DIR, '7_mst_map.html')
fig.write_html(output_file)

print(f"\n✅ Map saved successfully to: {output_file}")
print("Open this file in your web browser to view the MST.")