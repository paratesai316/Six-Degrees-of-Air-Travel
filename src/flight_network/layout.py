import dash
from dash import dcc, html

def create_layout(app, options):
    """
    Creates the static layout for the Dash application.
    'app' is passed in to correctly generate asset URLs.
    'options' is the list of airports for dropdowns (passed as empty list on init).
    """
    return html.Div(className='main-container', children=[
    html.Link(rel='icon', href=app.get_asset_url('logo.png')),
    html.Header(className='app-header', children=[
        html.Img(src=app.get_asset_url('logo.png')),
        html.Div(className='header-title-container', children=[
            html.H1("Global Flight Network Explorer"),
            html.P(
                "Created by Sai Parate",
                className='app-author-credit'
            ),
        ]),
        
        dcc.Tabs(id="mode-switcher", value='network', className='custom-tabs', children=[
            dcc.Tab(label='🌐 Network', value='network', className='custom-tab', selected_className='custom-tab--selected'),
            dcc.Tab(label='✈️ Optimal Route', value='route', className='custom-tab', selected_className='custom-tab--selected'),
            dcc.Tab(label='🔍 All Routes', value='all_routes', className='custom-tab', selected_className='custom-tab--selected'),
            dcc.Tab(label='📍 Single Airport', value='single_airport', className='custom-tab', selected_className='custom-tab--selected'),
        ])
    ]),    
        # --- Static Control Panels (visibility controlled by callback) ---
        html.Div(id='network-controls', children=[
            html.Div(className='controls-container slider-container', children=[
                html.Label("Filter Network Density:"),
                dcc.Slider(id='degree-slider', min=0, max=200, step=1, value=50, marks={0: '0', **{i: str(i) for i in range(20, 201, 20)}})
            ])
        ]),
        html.Div(id='route-controls', style={'display': 'none'}, children=[
            html.Div(className='controls-container route-container', children=[
                dcc.Dropdown(id='source-airport-dropdown', options=options, placeholder="Select a starting airport..."),
                dcc.Dropdown(id='destination-airport-dropdown', options=options, placeholder="Select a destination..."),
                html.Button('Find Optimal Route', id='find-route-button', n_clicks=0)
            ])
        ]),
        html.Div(id='all-routes-controls', style={'display': 'none'}, children=[
            html.Div(className='controls-container all-routes-container', children=[
                dcc.Dropdown(id='all-routes-source-dropdown', options=options, placeholder="Select a starting airport..."),
                dcc.Dropdown(id='all-routes-dest-dropdown', options=options, placeholder="Select a destination..."),
                dcc.Input(id='num-flights-input', type='number', placeholder='Num. of flights...', min=1, max=3, step=1, value=2),
                html.Button('Find All Routes', id='find-all-routes-button', n_clicks=0)
            ])
        ]),
        html.Div(id='single-airport-controls', style={'display': 'none'}, children=[
            html.Div(className='controls-container single-airport-container', children=[
                dcc.Dropdown(id='single-airport-dropdown', options=options, placeholder="Select an airport to explore..."),
                html.Button('Show Flights', id='show-flights-button', n_clicks=0)
            ])
        ]),
        
        dcc.Loading(id="loading-spinner", type="default", children=[
            html.Div(id='output-message'),
            dcc.Graph(id='flight-map', style={'height': '80vh'}, config={'scrollZoom': True})
        ])
    ])

