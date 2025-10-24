import dash
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import networkx as nx
import math
import numpy as np

# ==============================================================================
# 1. HELPER FUNCTIONS (Copied from main app)
# ==============================================================================
def get_great_circle_arc(lon1, lat1, lon2, lat2, num_points=15):
    """Generate intermediate points for a great-circle arc."""
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    x1, y1, z1 = math.cos(lat1_rad) * math.cos(lon1_rad), math.cos(lat1_rad) * math.sin(lon1_rad), math.sin(lat1_rad)
    x2, y2, z2 = math.cos(lat2_rad) * math.cos(lon2_rad), math.cos(lat2_rad) * math.sin(lon2_rad), math.sin(lat2_rad)
    dot_product = max(-1.0, min(1.0, x1 * x2 + y1 * y2 + z1 * z2))
    d = math.acos(dot_product)
    arc_lons, arc_lats = [], []
    for i in range(num_points + 1):
        f = i / num_points
        if d == 0: A, B = 1 - f, f
        else: A, B = math.sin((1 - f) * d) / math.sin(d), math.sin(f * d) / math.sin(d)
        x, y, z = A * x1 + B * x2, A * y1 + B * y2, A * z1 + B * z2
        lat = math.atan2(z, math.sqrt(x**2 + y**2))
        lon = math.atan2(y, x)
        arc_lats.append(math.degrees(lat))
        arc_lons.append(math.degrees(lon))
    return arc_lons, arc_lats

def split_antimeridian(lons, lats):
    """Splits a line path that crosses the antimeridian."""
    new_lons, new_lats = [], []
    for i in range(len(lons) - 1):
        new_lons.append(lons[i])
        new_lats.append(lats[i])
        if abs(lons[i+1] - lons[i]) > 180:
            new_lons.append(None)
            new_lats.append(None)
    new_lons.append(lons[-1])
    new_lats.append(lats[-1])
    return new_lons, new_lats

# ==============================================================================
# 2. MAIN CALLBACK REGISTRATION
# ==============================================================================
def register_callbacks(app, G_unweighted, G_weighted, airport_dict, airports_filtered, airline_name_map, dropdown_options):

    @app.callback(
        [Output('flight-map', 'figure'), Output('output-message', 'children'),
         Output('network-controls', 'style'), Output('route-controls', 'style'),
         Output('all-routes-controls', 'style'), Output('single-airport-controls', 'style'),
         # Outputs to dynamically load options
         Output('source-airport-dropdown', 'options'),
         Output('destination-airport-dropdown', 'options'),
         Output('all-routes-source-dropdown', 'options'),
         Output('all-routes-dest-dropdown', 'options'),
         Output('single-airport-dropdown', 'options')],
        [Input('mode-switcher', 'value'), Input('find-route-button', 'n_clicks'),
         Input('find-all-routes-button', 'n_clicks'), Input('show-flights-button', 'n_clicks'),
         Input('degree-slider', 'value')],
        [State('source-airport-dropdown', 'value'), State('destination-airport-dropdown', 'value'),
         State('all-routes-source-dropdown', 'value'), State('all-routes-dest-dropdown', 'value'), State('num-flights-input', 'value'),
         State('single-airport-dropdown', 'value')]
    )
    def update_view(mode, find_route_clicks, find_all_clicks, show_flights_clicks, slider_value,
                    source_id, dest_id, all_source_id, all_dest_id, num_flights, single_airport_id):
        
        fig = go.Figure()
        fig.update_layout(mapbox_style="carto-positron", margin={"r":0, "t":0, "l":0, "b":0}, showlegend=False, mapbox_zoom=1.5, mapbox_center={"lat": 20, "lon": 0}, mapbox_pitch=0)
        message = ""
        
        styles = { 'network': {'display': 'none'}, 'route': {'display': 'none'}, 'all_routes': {'display': 'none'}, 'single_airport': {'display': 'none'} }
        
        # Initialize all dropdown options as empty to prevent loading lag
        route_opts, all_routes_opts, single_opts = [], [], []
        
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'No trigger'
        
        if not ctx.triggered:
            current_mode = 'network'
        else:
            current_mode = mode
        
        styles[current_mode] = {'display': 'block'}
        
        if current_mode == 'network':
            slider_val = slider_value if slider_value is not None else 50
            filtered_airports = airports_filtered[airports_filtered['degree'] >= slider_val]
            visible_airport_ids = set(filtered_airports['Airport ID'])
            lons, lats = [], []
            for source, dest in G_unweighted.edges():
                if source in visible_airport_ids and dest in visible_airport_ids:
                    arc_lons, arc_lats = get_great_circle_arc(airport_dict[source]['Longitude'], airport_dict[source]['Latitude'], airport_dict[dest]['Longitude'], airport_dict[dest]['Latitude'])
                    split_lons, split_lats = split_antimeridian(arc_lons, arc_lats)
                    lons.extend(split_lons + [None])
                    lats.extend(split_lats + [None])
            fig.add_trace(go.Scattermapbox(mode="lines", lon=lons, lat=lats, line=dict(width=0.5, color="#005ab5"), opacity=0.1, hoverinfo='none'))
            fig.add_trace(go.Scattermapbox(
                lat=filtered_airports["Latitude"], lon=filtered_airports["Longitude"], mode='markers',
                marker=go.scattermapbox.Marker(size=filtered_airports['size'], color=filtered_airports['degree'], colorscale='YlOrRd', showscale=True, colorbar_title_text='Destinations'),
                text=filtered_airports.apply(lambda r: f"{r['Name']} ({r['IATA']})<br>Destinations: {int(r['degree'])}", axis=1), hoverinfo='text'))
            message = f"Showing {len(filtered_airports)} airports with {slider_val}+ destinations and their interconnecting routes."

        elif current_mode == 'route':
            route_opts = dropdown_options # Load options for this tab
            if find_route_clicks > 0:
                if not source_id or not dest_id: message = "⚠️ Please select both airports."
                elif not G_unweighted.has_node(source_id) or not G_unweighted.has_node(dest_id):
                    message = "⚠️ One or both selected airports have no flight routes in the dataset."
                else:
                    try:
                        path_bfs = nx.shortest_path(G_unweighted, source=source_id, target=dest_id)
                        dist_bfs = nx.path_weight(G_weighted, path_bfs, weight='weight')
                        path_dijkstra = nx.dijkstra_path(G_weighted, source=source_id, target=dest_id)
                        def plot_path(p, color, name):
                            details = [airport_dict[n] for n in p]
                            path_lats, path_lons = [d['Latitude'] for d in details], [d['Longitude'] for d in details]
                            arc_lons_full, arc_lats_full = [], []
                            for i in range(len(p) - 1):
                                arc_lons, arc_lats = get_great_circle_arc(path_lons[i], path_lats[i], path_lons[i+1], path_lats[i+1])
                                split_lons, split_lats = split_antimeridian(arc_lons, arc_lats)
                                arc_lons_full.extend(split_lons + [None])
                                arc_lats_full.extend(split_lats + [None])
                            fig.add_trace(go.Scattermapbox(mode="lines", lon=arc_lons_full, lat=arc_lats_full, line=dict(width=2, color=color), opacity=0.9, name=name, hoverinfo='none'))
                            fig.add_trace(go.Scattermapbox(mode="markers", lon=path_lons, lat=path_lats, marker=dict(size=12, color=color), name=name, text=[f"{d['Name']} ({d['IATA']})" for d in details], hoverinfo="text"))

                        fig.update_layout(showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.7)', font=dict(color='black')))
                        if len(path_bfs) == len(path_dijkstra): plot_path(path_dijkstra, "#0066cc", "Shortest & Fewest Flights")
                        else: plot_path(path_bfs, "#0066cc", "Least Flights"); plot_path(path_dijkstra, "#00cc66", "Shortest Distance")
                        
                        message = html.Table([
                            html.Tr([html.Th("Metric"), html.Th("Least Flights (BFS)"), html.Th("Shortest Distance (Dijkstra)")]),
                            html.Tr([html.Td("Num. Flights"), html.Td(f"{len(path_bfs) - 1}"), html.Td(f"{len(path_dijkstra) - 1}")]),
                            html.Tr([html.Td("Total Distance"), html.Td(f"{dist_bfs:,.0f} km"), html.Td(f"{nx.path_weight(G_weighted, path_dijkstra, weight='weight'):,.0f} km")])
                        ], className='results-table')
                    except nx.NetworkXNoPath: message = "❌ No connecting flight path found."
            else: message = "Select two airports to find the optimal route."

        elif current_mode == 'all_routes':
            all_routes_opts = dropdown_options # Load options for this tab
            if find_all_clicks > 0:
                if not all_source_id or not all_dest_id or not num_flights: message = "⚠️ Please provide all inputs."
                elif not G_unweighted.has_node(all_source_id) or not G_unweighted.has_node(all_dest_id):
                    message = "⚠️ One or both selected airports have no flight routes in the dataset."
                elif num_flights >= 4:
                    message = "⚠️ Searching for 4 or more flights is computationally expensive. Please select a number between 1 and 3."
                else:
                    cutoff = num_flights + 1
                    paths = [p for p in nx.all_simple_paths(G_unweighted, source=all_source_id, target=all_dest_id, cutoff=cutoff) if len(p) == cutoff]
                    if not paths: message = f"Found 0 routes with exactly {num_flights} flight(s)."
                    else:
                        path_data = []
                        for path in paths:
                            distance = nx.path_weight(G_weighted, path, weight='weight')
                            path_airlines = []
                            for i in range(len(path) - 1):
                                airline_code = G_unweighted.get_edge_data(path[i], path[i+1]).get('airline', 'N/A')
                                airline_name = airline_name_map.get(airline_code, airline_code)
                                path_airlines.append(f"({airline_name})")
                            airport_names = f"{airport_dict[path[0]]['IATA']} " + " → ".join([f"{airline} {airport_dict[node]['IATA']}" for airline, node in zip(path_airlines, path[1:])])
                            path_data.append({'names': airport_names, 'distance': distance, 'path': path})
                        
                        sorted_paths = sorted(path_data, key=lambda x: x['distance'])
                        
                        for item in sorted_paths:
                            path = item['path']
                            details = [airport_dict[n] for n in path]
                            lats, lons = [d['Latitude'] for d in details], [d['Longitude'] for d in details]
                            
                            arc_lons_full, arc_lats_full = [], []
                            for i in range(len(path) - 1):
                                arc_lons, arc_lats = get_great_circle_arc(lons[i], lats[i], lons[i+1], lats[i+1])
                                split_lons, split_lats = split_antimeridian(arc_lons, arc_lats)
                                arc_lons_full.extend(split_lons + [None])
                                arc_lats_full.extend(split_lats + [None])
                            fig.add_trace(go.Scattermapbox(mode="lines", lon=arc_lons_full, lat=arc_lats_full, line=dict(width=1.5, color="#ff5733"), opacity=0.5, hoverinfo='none'))

                        start_details, end_details = airport_dict[all_source_id], airport_dict[all_dest_id]
                        fig.add_trace(go.Scattermapbox(mode="markers", lon=[start_details['Longitude'], end_details['Longitude']], lat=[start_details['Latitude'], end_details['Latitude']],
                                                       marker=dict(size=15, color="#ff5733"), text=[start_details['Name'], end_details['Name']], hoverinfo="text"))
                        summary_message = html.P(f"✅ Found {len(paths)} unique route(s) with exactly {num_flights} flight(s).")
                        path_list_items = [html.Li(f"{item['names']} ({item['distance']:,.0f} km)") for item in sorted_paths]
                        sorted_list_component = html.Div([
                            html.H5("Routes Sorted by Shortest Distance:"),
                            html.Ul(path_list_items)
                        ], className='sorted-routes-list')
                        message = html.Div([summary_message, sorted_list_component])
            else: message = "Select two airports and the number of flights to explore all routes."

        elif current_mode == 'single_airport':
            single_opts = dropdown_options # Load options for this tab
            if show_flights_clicks > 0:
                if not single_airport_id: message = "⚠️ Please select an airport."
                elif not G_unweighted.has_node(single_airport_id):
                    message = f"ℹ️ {airport_dict[single_airport_id]['Name']} has no flight routes in the dataset."
                else:
                    source_details = airport_dict[single_airport_id]
                    destinations = list(G_unweighted.successors(single_airport_id))
                    valid_destinations = [d for d in destinations if d in airport_dict]
                    if not valid_destinations: message = f"{source_details['Name']} has no outgoing flights from the dataset."
                    else:
                        lons, lats = [], []
                        for dest_id in valid_destinations:
                            arc_lons, arc_lats = get_great_circle_arc(source_details['Longitude'], source_details['Latitude'], airport_dict[dest_id]['Longitude'], airport_dict[dest_id]['Latitude'])
                            split_lons, split_lats = split_antimeridian(arc_lons, arc_lats)
                            lons.extend(split_lons + [None])
                            lats.extend(split_lats + [None])
                        
                        dest_lats_markers = [airport_dict[d]['Latitude'] for d in valid_destinations]
                        dest_lons_markers = [airport_dict[d]['Longitude'] for d in valid_destinations]
                        
                        all_marker_lons = [source_details['Longitude']] + dest_lons_markers
                        all_marker_lats = [source_details['Latitude']] + dest_lats_markers
                        all_marker_sizes = [15] + [8] * len(valid_destinations)
                        all_marker_colors = ["#ff3300"] + ["#008cff"] * len(valid_destinations)
                        all_marker_symbols = ["star"] + ["circle"] * len(valid_destinations)
                        all_marker_text = [source_details['Name']] + [airport_dict[d]['Name'] for d in valid_destinations]
                        
                        fig.add_trace(go.Scattermapbox(mode="lines", lon=lons, lat=lats, line=dict(width=1, color="#008cff"), opacity=0.7, hoverinfo='none'))
                        fig.add_trace(go.Scattermapbox(mode="markers", lon=all_marker_lons, lat=all_marker_lats,
                                                       marker=dict(size=all_marker_sizes, color=all_marker_colors, symbol=all_marker_symbols),
                                                       text=all_marker_text, hoverinfo="text"))
                        message = f"Showing {len(valid_destinations)} direct flights from {source_details['Name']} (using combined dataset)."
            else:
                message = "Select an airport to see all its direct flights."
                
        return fig, message, styles['network'], styles['route'], styles['all_routes'], styles['single_airport'], route_opts, route_opts, all_routes_opts, all_routes_opts, single_opts

