
import pandas as pd
import numpy as np
import requests
import streamlit as st
import folium
import os
import plotly.express as px
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from streamlit_folium import folium_static
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# API Keys
OPENWEATHER_API = os.getenv("OPENWEATHER_API")
CARBON_INTERFACE_API = os.getenv("CARBON_INTERFACE_API")
CHARGEMAP_API = os.getenv("CHARGEMAP_API")
AQICN_API = os.getenv("AQICN_API")
ELECTRICITYMAP_API = os.getenv("ELECTRICITYMAP_API")

# Pollutant Names Mapping
POLLUTANT_NAMES = {
    "co": "Carbon Monoxide (CO)",
    "no": "Nitric Oxide (NO)",
    "no2": "Nitrogen Dioxide (NO₂)",
    "o3": "Ozone (O₃)",
    "so2": "Sulfur Dioxide (SO₂)",
    "pm2_5": "Fine Particulate Matter (PM2.5)",
    "pm10": "Particulate Matter (PM10)",
    "nh3": "Ammonia (NH₃)"
}

# Fetch Real-Time Pollution Data
def get_openweather_pollution(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API}"
        response = requests.get(url)
        if response.ok:
            return response.json()['list'][0]
        else:
            st.error(f"OpenWeatherMap Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return None

# Fetch Real-Time AQI
def get_aqicn_aqi(city):
    try:
        url = f"https://api.waqi.info/feed/{city}/?token={AQICN_API}"
        response = requests.get(url)
        if response.ok:
            return response.json().get('data', {}).get('aqi')
        else:
            st.error(f"AQICN API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return None

# Fetch Electricity Carbon Intensity
def get_electricity_carbon_intensity(zone):
    try:
        url = "https://api.electricitymap.org/v3/carbon-intensity/latest"
        headers = {"auth-token": ELECTRICITYMAP_API}
        response = requests.get(url, headers=headers, params={"zone": zone})
        if response.ok:
            return response.json().get('carbonIntensity')
        else:
            st.error(f"Electricity Maps Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return None
# Fetch Historical Pollution Data
def fetch_historical_pollution(lat, lon):
    try:
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=7)).timestamp())
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start_time}&end={end_time}&appid={OPENWEATHER_API}"
        response = requests.get(url)
        if response.ok:
            return response.json().get("list", [])
        else:
            st.error(f"Error fetching historical pollution data: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return []

# Preprocess Time Series Data
def preprocess_time_series_data(historical_data):
    timestamps = []
    pm25_values = []
    for record in historical_data:
        timestamps.append(datetime.utcfromtimestamp(record['dt']))
        pm25_values.append(record['components']['pm2_5'])
    return pd.DataFrame({"timestamp": timestamps, "pm2_5": pm25_values})

# Predict Pollution Trends
def predict_trends(dataframe):
    model = ExponentialSmoothing(dataframe['pm2_5'], seasonal='add', seasonal_periods=7)
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=7)
    return forecast

# Fetch Vehicle Models from Carbon Interface
def get_vehicle_models():
    try:
        url = "https://www.carboninterface.com/api/v1/vehicle_makes"
        headers = {"Authorization": f"Bearer {CARBON_INTERFACE_API}"}
        response = requests.get(url, headers=headers)
        if response.ok:
            vehicle_models = {}
            for make in response.json():
                make_id = make['data']['id']
                make_name = make['data']['attributes']['name']
                models_url = f"https://www.carboninterface.com/api/v1/vehicle_makes/{make_id}/vehicle_models"
                models_response = requests.get(models_url, headers=headers)
                if models_response.ok:
                    for model in models_response.json():
                        model_name = f"{make_name} {model['data']['attributes']['name']}"
                        vehicle_models[model_name] = model['data']['id']
            return vehicle_models
        else:
            st.error(f"Carbon Interface Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return {}

# Calculate Carbon Emissions
def calculate_vehicle_emissions(distance, vehicle_model_id):
    try:
        url = "https://www.carboninterface.com/api/v1/estimates"
        headers = {"Authorization": f"Bearer {CARBON_INTERFACE_API}", "Content-Type": "application/json"}
        payload = {
            "type": "vehicle",
            "distance_unit": "km",
            "distance_value": distance,
            "vehicle_model_id": vehicle_model_id
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.ok:
            return response.json()['data']['attributes']['carbon_kg']
        else:
            st.warning(f"Carbon Interface API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return None

# Fetch EV Charging Stations
def get_ev_charging_stations(lat, lon, max_results=5):
    try:
        url = "https://api.openchargemap.io/v3/poi/"
        params = {"latitude": lat, "longitude": lon, "maxresults": max_results, "key": CHARGEMAP_API}
        response = requests.get(url, params=params)
        if response.ok:
            return response.json()
        else:
            st.warning(f"Open Charge Map API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Exception: {e}")
    return None
# Clustering for High-Emission Zones
def create_pollution_data(points):
    data = []
    for point in points:
        lat, lon = point
        pollution = get_openweather_pollution(lat, lon)
        if pollution:
            pm25 = pollution['components']['pm2_5']
            data.append({"latitude": lat, "longitude": lon, "pm2_5": pm25})
    return pd.DataFrame(data)

def apply_clustering(dataframe, n_clusters=3):
    kmeans = KMeans(n_clusters=n_clusters)
    dataframe['cluster'] = kmeans.fit_predict(dataframe[['latitude', 'longitude', 'pm2_5']])
    return dataframe, kmeans.cluster_centers_


# Main Dashboard
def main():
    st.title("\U0001F30D AI-Driven Sustainability Dashboard")
    st.write("Track real-time air quality, carbon emissions, and EV charging stations interactively.")

    # User Inputs
    city = st.text_input("Enter City Name:", "Berlin")
    lat = st.number_input("Latitude:", value=52.52)
    lon = st.number_input("Longitude:", value=13.405)
    zone = st.text_input("Electricity Zone Code (e.g., DE):", "DE")
    distance = st.number_input("Distance Travelled (km):", value=50.0, min_value=0.0)
    lat_lon_points = [(52.5200, 13.4050), (52.5205, 13.4080), (52.5190, 13.4020)]
    n_clusters = st.slider("Select Number of Clusters:", 1, 10, 3)
    
    # Fetch Vehicle Models
    vehicle_models = get_vehicle_models()
    if vehicle_models:
        selected_vehicle = st.selectbox("Select Vehicle Model:", list(vehicle_models.keys()))
        vehicle_model_id = vehicle_models[selected_vehicle]
    else:
        st.error("Unable to fetch vehicle models. Check API key.")
        return

    if st.button("Fetch Data"):
        st.subheader("1. Real-Time Air Pollution Data")
        pollution = get_openweather_pollution(lat, lon)
        if pollution:
            st.write(f"Air Quality Index (AQI): {pollution['main']['aqi']}")
            data = []
            for key, value in pollution['components'].items():
                full_name = POLLUTANT_NAMES.get(key, key)
                data.append({"Pollutant": full_name, "Concentration (µg/m³)": value})
            df = pd.DataFrame(data)
            st.dataframe(df)
            # Visualization with Plotly
            fig = px.bar(df, x="Pollutant", y="Concentration (µg/m³)", title="Pollutant Concentrations")
            st.plotly_chart(fig)

        st.subheader("2. Pollution Trends Prediction")
        historical_data = fetch_historical_pollution(lat, lon)
        if historical_data:
            df = preprocess_time_series_data(historical_data)
            st.write(df)
            fig = px.line(df, x='timestamp', y='pm2_5', title="Historical PM2.5 Levels")
            st.plotly_chart(fig)
            forecast = predict_trends(df)
            st.subheader("Predicted PM2.5 Levels")
            st.line_chart(forecast)

        st.subheader("3. High-Emission Zones Clustering")
        pollution_data = create_pollution_data(lat_lon_points)
        clustered_data, cluster_centers = apply_clustering(pollution_data, n_clusters)
        st.write(clustered_data)
        fig = px.scatter_mapbox(
            clustered_data,
            lat="latitude",
            lon="longitude",
            color="cluster",
            size="pm2_5",
            mapbox_style="carto-positron",
            title="Clustered High-Emission Zones"
        )
        st.plotly_chart(fig)
        
        st.subheader("4. Real-Time AQI and Recommendations")
        aqi = get_aqicn_aqi(city)
        if aqi:
            st.write(f"Air Quality Index (AQI) in {city}: {aqi}")
            if aqi <= 50:
                st.success("Air quality is good. Enjoy your day outside!")
            elif aqi <= 100:
                st.warning("Air quality is moderate. Sensitive groups should take precautions.")
            else:
                st.error("Air quality is unhealthy. Limit outdoor activities.")

        st.subheader("5. Carbon Intensity of Electricity Grid")
        carbon_intensity = get_electricity_carbon_intensity(zone)
        if carbon_intensity:
            st.success(f"Carbon Intensity in {zone}: {carbon_intensity} gCO₂/kWh")
            # Visualization
            fig = px.pie(values=[carbon_intensity, 1000-carbon_intensity], 
                         names=["Carbon Intensity", "Other"], 
                         title="Carbon Intensity Proportion")
            st.plotly_chart(fig)

        st.subheader("6. Carbon Emissions from Vehicle Travel")
        if vehicle_model_id:
            emissions = calculate_vehicle_emissions(distance, vehicle_model_id)
            if emissions:
                st.success(f"CO₂ Emissions for {distance} km in {selected_vehicle}: {emissions:.2f} kg CO₂")
                # Visualization
                fig = px.bar(
                    x=[selected_vehicle], 
                    y=[emissions], 
                    title="CO₂ Emissions", 
                    labels={"x": "Vehicle", "y": "Emissions (kg CO₂)"}
                 )
                st.plotly_chart(fig)
        else:
            st.error("Please select a valid vehicle model to calculate emissions.")

        st.subheader("7. Nearby EV Charging Stations")
        ev_stations = get_ev_charging_stations(lat, lon)
        if ev_stations:
            st.write("Nearby EV Charging Stations:")
            m = folium.Map(location=[lat, lon], zoom_start=13)
            for station in ev_stations[:5]:
                folium.Marker(
                    [station['AddressInfo']['Latitude'], station['AddressInfo']['Longitude']],
                    popup=station['AddressInfo']['Title'],
                    icon=folium.Icon(color="green", icon="bolt")
                ).add_to(m)
            folium_static(m)
        else:
            st.write("No nearby EV charging stations found.")

if __name__ == "__main__":
    main()