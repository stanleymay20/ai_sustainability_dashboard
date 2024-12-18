import requests
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np

# API Keys
OPENWEATHER_API = "e6abd7c0126034673af84df1967d9d59"  # OpenWeatherMap API Key
CARBON_INTERFACE_API = "nZKI00HqSiFTFaaKnbAzw"        # Carbon Interface API Key
CHARGEMAP_API = "316788dd-6ba6-47ed-9437-5853c1f313b9"  # Open Charge Map API Key
AQICN_API = "1310913ccc485dacb27c50b206392aa070200922"  # AQICN API Key
ELECTRICITYMAP_API = "SxD5EyzABwTFZ"                   # Electricity Maps API Key

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
            for key, value in pollution['components'].items():
                full_name = POLLUTANT_NAMES.get(key, key)
                st.write(f"- **{full_name}**: {value} µg/m³")
        
        st.subheader("3. Carbon Intensity of Electricity Grid")
        carbon_intensity = get_electricity_carbon_intensity(zone)
        if carbon_intensity:
            st.success(f"Carbon Intensity in {zone}: {carbon_intensity} gCO₂/kWh")

        st.subheader("4. Carbon Emissions from Vehicle Travel")
        if vehicle_model_id:
            emissions = calculate_vehicle_emissions(distance, vehicle_model_id)
            if emissions:
                st.success(f"CO₂ Emissions for {distance} km in {selected_vehicle}: {emissions:.2f} kg CO₂")
        else:
            st.error("Please select a valid vehicle model to calculate emissions.")

        st.subheader("6. Nearby EV Charging Stations")
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

if __name__ == "__main__":
    main()