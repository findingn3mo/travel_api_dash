import requests
import json
import pandas as pd

# You can change the list of your the major cities that you want
CITIES = ['New York', 'Los Angeles', 'San Francisco', 'Miami', 'Boston', 'Dallas', 'Chicago', 'Seattle', 'Philadelphia',
          'Cincinnati', 'Houston', 'Minneapolis', 'Denver', 'Orlando', 'Phoenix', 'Las Vegas', 'Washington DC']

# Enter your API key here
API_KEY = '9567c7dc82b4425ea6d221305231504'  # you can create one for free at their website


def combined_df():
    combined_df = pd.DataFrame()

    for city in CITIES:
        df = city_data(city, api_key=API_KEY)
        combined_df = pd.concat([combined_df, df])

    combined_df = combined_df.reset_index(drop=True)
    return combined_df


def city_list(combined_df):
    city = list(combined_df.name.unique())

    return city


def city_data(cityname, api_key):
    # Set the OpenWeatherMap API endpoint URL
    call = f'https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={cityname}&days=7&aqi=no&alerts=no'
    # Send the API request and parse the JSON response
    response = requests.get(call)
    data = json.loads(response.text)

    # Removing extra (missing) data from response
    for i in range(7):
        del data['forecast']['forecastday'][i]['astro']
        del data['forecast']['forecastday'][i]['hour']

    coordinate = data['location']
    forecast = data['forecast']['forecastday']

    location_df = pd.json_normalize(coordinate)
    forecast_df = pd.json_normalize(forecast)

    location_df = location_df.filter(['name', 'lat', 'lon'])
    location_df7 = pd.concat([location_df] * 7, ignore_index=True)

    city_df = location_df7.join(forecast_df)

    return city_df