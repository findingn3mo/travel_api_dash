import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data import combined_df
from dash import Dash, dcc, html, Input, Output, dash_table, State
import requests
import time
import json

# enter your API key here
WEATHER_API = '9567c7dc82b4425ea6d221305231504'  # you can create one for free at their website

# https://simplemaps.com/data/us-cities.
CITIES_DF = pd.read_csv('uscities.csv', usecols=['city', 'state_name', 'lat', 'lng'])

# The Google Maps API key, if this doesn't work, you can replace it with your own
GOOGLE_MAPS_API ='AIzaSyCyblSRaTVhEEyc6_G9JykWH4mT9_38moE'

# Data Preparation for Dash Table
combined = combined_df()
filter = combined.drop_duplicates(subset=['name'])
points = filter.reset_index(drop=True)
points = points[['name', 'lat', 'lon']]

# create an app dashboard
app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H4('An Interactive Travel Dashboard'),
    html.Div([
        dcc.Dropdown(
                    id='state-dropdown',
                    options=[{'label': state, 'value': state} for state in CITIES_DF['state_name'].unique()],
                    value='New York',clearable=False
                ),
                dcc.Dropdown(
                    id='city-dropdown',
                    value='Manhattan',clearable=False
                )
    ]),
        dcc.Tabs(id='tabs', value='tab-1', children=[
            dcc.Tab(label='Attractions', value='tab-1', children=[
                html.Div([
                    html.P('Choose the radius within which to return place results'),
                    dcc.Slider(
                        id='radius-slider',
                        min=1,
                        max=50000,
                        value=10000,
                        marks={
                            1000: '1km',
                            5000: '5km',
                            10000: '10km',
                            15000: '15km',
                            20000: '20km',
                            25000: '25km',
                            30000: '30km',
                            35000: '35km',
                            40000: '40km',
                            45000: '45km',
                            50000: '50km'
                        }
                    )]
                ),
                dcc.Input(id='search-input', type='text', placeholder='Enter your search query'),
                dcc.Input(id='place-limit', type='number', placeholder='How many places do you want to see?'),
                html.Button('Search', id='search-button', n_clicks=0),
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in ['Name', 'Address', 'Rating', 'Price Level', 'Operating Hours']],
                    data=[],
                    row_selectable='multi',
                    selected_rows=[],
                    style_table={'overflowX': 'scroll'}
                ),
                html.Button('Add to itinerary', id='add-itinerary'),
                html.P('Your Itinerary List'),
                dash_table.DataTable(
                    id='itinerary-table',
                    columns=[{"name": i, "id": i} for i in ['Name', 'Address', 'Operating Hours']],
                    data=[],
                    style_table={'overflowX': 'scroll'}
                )
            ]),
            dcc.Tab(label='Weather Forecast', value='tab-2', children=[
                html.Div([
                    dcc.Dropdown(
                    id='days-dropdown',
                    options=[{'label': f'{i} days', 'value': i} for i in range(1, 15)],
                    value=7,
                    clearable=False
                ),
                    html.Div(id='forecast-graph')
                ])
            ]),
            dcc.Tab(label='Daily Weather Details of Big Cities In the US', value='tab-3', children=[
                html.Div([
                    dcc.Dropdown(
                        id='weather-variable',
                        options=[
                            {'label': 'Maximum Temperature (Celcius)', 'value': 'day.maxtemp_c'},
                            {'label': 'Maximum Temperature (Fahrenheit)', 'value': 'day.maxtemp_f'},
                            {'label': 'Minimum Temperature (Celcius)', 'value': 'day.mintemp_c'},
                            {'label': 'Minimum Temperature (Fahrenheit)', 'value': 'day.mintemp_f'},
                            {'label': 'Average Temperature (Celcius)', 'value': 'day.avgtemp_c'},
                            {'label': 'Average Temperature (Fahrenheit)', 'value': 'day.avgtemp_f'},
                            {'label': 'Total Precipitation (mm)', 'value': 'day.totalprecip_mm'},
                            {'label': 'Total Precipitation (in)', 'value': 'day.totalprecip_in'},
                            {'label': 'Total Snow (cm)', 'value': 'day.totalsnow_cm'}
                            ],
                            value='day.avgtemp_f',
                            clearable=False,
                        ),
                    dcc.Graph(id='weather-map') 
                        ])
            ])
        ])

])


# Call back on the weather map function with the input from the user
@app.callback(
    Output('weather-map', 'figure'),
    Input('weather-variable', 'value')
)
def update_weather_map(value):
    """
        Function: update_weather_map
        (a function to plot the weather map for major city based on the user input weather index)
        Input: value (string)
        Return: fig (a graph)
    """
    # Plot the map based on the latitude and longtitude from the df and the user input weather index
    fig = px.scatter_mapbox(combined, lat="lat", lon="lon", color=value,
                            color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=3,
                            center={"lat": 39.8283, "lon": -98.5795})
    
    # update the figure
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return {'data': fig.data, 'layout': fig.layout}

@app.callback(
    Output('city-dropdown', 'options'),
    [Input('state-dropdown', 'value')]
)
def set_cities_options(selected_state):
    filtered_df = CITIES_DF[CITIES_DF['state_name'] == selected_state]
    return [{'label': city, 'value': city} for city in filtered_df['city'].unique()]

@app.callback(
    [Output('table', 'data')],
    [Input('search-button', 'n_clicks'),
     Input('state-dropdown', 'value'),
     Input('city-dropdown', 'value'),
     Input('radius-slider', 'value'),
     Input('place-limit', 'value')],
    [State('search-input', 'value')]
)
def update_search_results(n_clicks, selected_state, selected_city, radius, place_limit, search_query):
    if not search_query:
        # Return empty list of data if search input is empty
        return [[]]
    
    else:
        query = search_query

        # Filter the CITIES_DF to get the corresponding latitude and longitude values
        selected_row = CITIES_DF[(CITIES_DF['state_name'] == selected_state) & (CITIES_DF['city'] == selected_city)]

        # Extract the latitude and longitude values
        lat = selected_row['lat'].values[0]
        lng = selected_row['lng'].values[0]

        # Define the radius (in meters) for the search
        radius = radius

        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&location={lat},{lng}&radius={radius}&key={GOOGLE_MAPS_API}"

        # Send the HTTP request and get the response
        response = requests.get(url)

        places = response.json()['results']

        data = []
        counter = 0
        for place in places:
            if counter >= place_limit:
                break

            # Get the place details using the Place ID
            place_id = place['place_id']
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,rating,price_level,opening_hours&key={GOOGLE_MAPS_API}"
            details_response = requests.get(details_url)
            details = details_response.json()['result']

            # Extract the opening hours and weekday text
            opening_hours = details.get('opening_hours', {})
            weekday_text = opening_hours.get('weekday_text', [])

            data.append({
                'Name': place['name'],
                'Address': place['formatted_address'],
                'Rating': place.get('rating', ''),
                'Price Level': place.get('price_level', ''),
                'Operating Hours': ','.join(weekday_text)
            })

             # Increment the counter
            counter += 1
            
            # Pause for 1 second between API requests to avoid hitting the rate limit
            time.sleep(.3)
            
        df = pd.DataFrame(data)
            
        return [df.to_dict('records')]

@app.callback(
    Output('itinerary-table', 'data'),
    Input('add-itinerary', 'n_clicks'),
    State('table', 'data'),
    State('table', 'selected_rows'),
    State('itinerary-table', 'data'),
    prevent_initial_call=True
)
def add_rows_to_new_table(n_clicks, data, selected_rows, current_itinerary):
    if not selected_rows:
        return current_itinerary
    
    selected_data = [{'Name': row['Name'], 'Address': row['Address'], 'Operating Hours': row['Operating Hours']} for row in data if data.index(row) in selected_rows and {'Name': row['Name'], 'Address': row['Address'], 'Operating Hours': row['Operating Hours']} not in current_itinerary]
    current_itinerary.extend(selected_data)
    return current_itinerary

# Define the callback function that creates the forecast graph
@app.callback(
    Output('forecast-graph', 'children'),
    Input('city-dropdown', 'value'),
    Input('days-dropdown', 'value')
)
def update_forecast(city, days):
    # Set the OpenWeatherMap API endpoint URL
    call = f'https://api.weatherapi.com/v1/forecast.json?key={WEATHER_API}&q={city}&days={days}&aqi=no&alerts=no'
    # Send the API request and parse the JSON response
    response = requests.get(call)
    data = json.loads(response.text)

    # Extract the relevant data from the JSON response
    city = data['location']['name']
    lat = data['location']['lat']
    lon = data['location']['lon']
    temps = [day['day']['avgtemp_c'] for day in data['forecast']['forecastday']]

    city_data_dict = {'city': city, 'lat': lat, 'lon': lon, 'temps': temps}

    # Create the line chart for the forecast
    forecast_graph = go.Figure(data=go.Scatter(x=list(range(1, days+1)), y=city_data_dict['temps']))
    forecast_graph.update_layout(title=f"{days}-Day Forecast for {city_data_dict['city']}", xaxis_title='Days into the future', yaxis_title='Temperature (Celsius)')
    
    # Return the forecast graph
    return dcc.Graph(figure=forecast_graph)


if __name__ == '__main__':
    app.run_server(debug=True)

