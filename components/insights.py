# components/insights.py
import requests
import streamlit as st
from utils import helpers
from components import maps as maps_comp


def _fetch_weather(lat: float, lon: float):
    api_key = helpers.env_or_secret("OPENWEATHER_API_KEY", "")
    if not api_key:
        return {"note": "OPENWEATHER_API_KEY not set — showing demo data.", "temp": 28, "humidity": 60, "rain": 2}
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        data = requests.get(url, timeout=10).json()
        rain = 0
        if isinstance(data.get("rain"), dict):
            rain = data["rain"].get("1h", 0)
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "rain": rain,
        }
    except Exception:
        return {"note": "OpenWeather error — using demo.", "temp": 28, "humidity": 60, "rain": 2}


def _fetch_soil(lat: float, lon: float):
    # Simple call to SoilGrids (public REST). Values vary by endpoint; use demo fallback on failure.
    try:
        url = (
            "https://rest.isric.org/soilgrids/v2.0/properties/query?"
            f"lon={lon}&lat={lat}&property=clay&depth=0-5cm"
        )
        data = requests.get(url, timeout=10).json()
        clay = None
        try:
            layers = data.get("properties", {}).get("layers", [])
            if layers and layers[0].get("values"):
                clay = layers[0]["values"][0].get("value")
        except Exception:
            clay = None
        if clay is None:
            raise RuntimeError("No clay value")
        return {"clay": clay}
    except Exception:
        return {"note": "SoilGrids unavailable — using demo.", "clay": 30}


def show_insights():
    st.header("🧠 AI Insights Engine")
    st.caption("Combines weather and soil data to suggest farming actions.")

    lat, lon = maps_comp.map_select_ui()
    if not (lat and lon):
        st.info("Select your farm location to fetch local insights.")
        return

    weather = _fetch_weather(lat, lon)
    soil = _fetch_soil(lat, lon)

    st.subheader("Current Conditions")
    st.write({"temperature_C": weather.get("temp"), "humidity_%": weather.get("humidity"), "rain_mm": weather.get("rain")})
    st.write({"soil_clay_%": soil.get("clay")})

    st.subheader("Recommendations")
    recs = []
    temp = weather.get("temp", 28)
    humidity = weather.get("humidity", 60)
    clay = soil.get("clay", 30)
    if temp > 32:
        recs.append("High temperature; consider mulching and mid-day irrigation.")
    if humidity < 40:
        recs.append("Low humidity; drip irrigation helps conserve water.")
    if clay and clay > 35:
        recs.append("High clay content; improve aeration and add organic matter.")
    if weather.get("rain", 0) > 5:
        recs.append("Rain forecast; delay fertilizer application to prevent runoff.")
    if not recs:
        recs.append("Conditions stable; continue regular monitoring and balanced composting.")

    for r in recs:
        st.write("- " + r)