# components/smart_farm_map.py
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import folium
from streamlit_folium import st_folium


# ---------------------------
# Utility: Geocoding (Nominatim)
# ---------------------------
def _geocode_location(query: str) -> Optional[Tuple[float, float]]:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": query, "format": "json", "limit": 1}
        headers = {"User-Agent": "EcoFarmX/1.0 (Streamlit)"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception:
        return None
    return None


# ---------------------------
# Utility: Weather via OpenWeatherMap
# ---------------------------
def _fetch_weather(lat: float, lon: float) -> Optional[Dict]:
    key = (
        st.secrets.get("OPENWEATHER", {}).get("api_key")
        if hasattr(st, "secrets") else None
    )
    if not key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": key, "units": "metric"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        rain_mm = 0.0
        # rain may be in last 1h or 3h
        if isinstance(data.get("rain"), dict):
            rain_mm = float(data["rain"].get("1h") or data["rain"].get("3h") or 0.0)
        out = {
            "temp_c": float(data.get("main", {}).get("temp", 0.0)),
            "humidity": float(data.get("main", {}).get("humidity", 0.0)),
            "rain_mm": rain_mm,
            "description": (data.get("weather", [{}])[0].get("description") or "").title(),
        }
        return out
    except Exception:
        return None


# ---------------------------
# Utility: Soil & NDVI (Mock)
# ---------------------------
def _mock_soil(state: str) -> Tuple[str, str]:
    s = (state or "").lower()
    # Simple mapping for demo purposes
    if any(k in s for k in ["maharashtra", "mp", "madhya pradesh"]):
        return "Black (Regur)", "7.2–8.5"
    if any(k in s for k in ["tamil nadu", "andhra", "telangana", "karnataka"]):
        return "Red", "6.0–7.5"
    if any(k in s for k in ["uttar pradesh", "bihar", "punjab", "haryana"]):
        return "Alluvial", "6.5–8.0"
    if any(k in s for k in ["rajasthan", "gujarat"]):
        return "Desert/Arid", "7.5–8.5"
    if any(k in s for k in ["kerala", "odisha", "west bengal"]):
        return "Laterite", "5.5–6.5"
    return "Mixed/Unknown", "6.0–7.5"


def _mock_ndvi(lat: float, lon: float, month: int) -> float:
    # Pseudo NDVI based on coordinates and month
    base = (np.sin(lat) + np.cos(lon)) * 0.1 + 0.5
    seasonal = 0.15 if 6 <= month <= 10 else (0.05 if 11 <= month or month <= 3 else 0.1)
    ndvi = np.clip(base + seasonal, 0.2, 0.85)
    return float(ndvi)


# ---------------------------
# Utility: Season
# ---------------------------
def _detect_season(month: int) -> str:
    if 6 <= month <= 10:
        return "Kharif"
    if 11 <= month or month <= 3:
        return "Rabi"
    return "Zaid"


# ---------------------------
# Utility: ML Recommendation (Mock RF)
# ---------------------------
def _train_mock_model() -> Tuple[RandomForestClassifier, OneHotEncoder, List[str]]:
    # Tiny synthetic dataset
    rows = [
        {"soil": "Alluvial", "season": "Kharif", "temp": 30, "rain": 120, "last": "Wheat", "next": "Rice"},
        {"soil": "Alluvial", "season": "Rabi",   "temp": 18, "rain": 40,  "last": "Rice",  "next": "Wheat"},
        {"soil": "Red",      "season": "Kharif", "temp": 32, "rain": 90,  "last": "Chili", "next": "Maize"},
        {"soil": "Red",      "season": "Rabi",   "temp": 22, "rain": 50,  "last": "Maize", "next": "Gram"},
        {"soil": "Black",    "season": "Kharif", "temp": 28, "rain": 100, "last": "Cotton","next": "Sorghum"},
        {"soil": "Black",    "season": "Rabi",   "temp": 20, "rain": 30,  "last": "Sorghum","next": "Cotton"},
        {"soil": "Laterite", "season": "Kharif", "temp": 29, "rain": 140, "last": "Rice",  "next": "Banana"},
        {"soil": "Desert",   "season": "Rabi",   "temp": 16, "rain": 20,  "last": "Mustard","next": "Cumin"},
        {"soil": "Alluvial", "season": "Zaid",   "temp": 34, "rain": 70,  "last": "Potato","next": "Pumpkin"},
        {"soil": "Red",      "season": "Zaid",   "temp": 33, "rain": 60,  "last": "Tomato","next": "Watermelon"},
    ]
    X = pd.DataFrame(rows, columns=["soil", "season", "temp", "rain", "last"])
    y = pd.Series([r["next"] for r in rows])
    enc = OneHotEncoder(handle_unknown="ignore")
    X_cat = enc.fit_transform(X[["soil", "season", "last"]])
    X_num = X[["temp", "rain"]].values
    X_all = np.hstack([X_cat.toarray(), X_num])
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(X_all, y)
    classes = list(rf.classes_)
    return rf, enc, classes


def _predict_next_crops(soil: str, season: str, temp: float, rain: float, last_crop: str,
                        model_bundle: Tuple[RandomForestClassifier, OneHotEncoder, List[str]]) -> List[str]:
    rf, enc, classes = model_bundle
    X_df = pd.DataFrame([{"soil": soil, "season": season, "last": last_crop, "temp": temp, "rain": rain}])
    X_cat = enc.transform(X_df[["soil", "season", "last"]])
    X_num = X_df[["temp", "rain"]].values
    X_all = np.hstack([X_cat.toarray(), X_num])
    probs = rf.predict_proba(X_all)[0]
    # pick top 3 crops
    top_idx = np.argsort(-probs)[:3]
    return [classes[i] for i in top_idx]


# ---------------------------
# Utility: Fertilizer & Risk rules
# ---------------------------
def _fertilizer_suggestions(crop_list: List[str], soil: str, ph: str) -> List[str]:
    base = {
        "Rice": "NPK 10-26-26 + Urea (split)",
        "Wheat": "DAP + Urea top-dress",
        "Maize": "NPK 20-20-0 + Zinc",
        "Gram": "Rock Phosphate + Organic Compost",
        "Sorghum": "NPK 15-15-15",
        "Cotton": "NPK 12-32-16 + Potash",
        "Banana": "Organic Compost + Potash",
        "Cumin": "NPK 10-10-10, low nitrogen",
        "Pumpkin": "NPK 12-12-17",
        "Watermelon": "NPK 15-15-15 + Calcium",
    }
    out = []
    for c in crop_list:
        fert = base.get(c, "Balanced NPK + micronutrients")
        out.append(f"{c}: {fert} (soil: {soil}, pH: {ph})")
    return out


def _risk_factors(temp: float, rain: float, humidity: float) -> List[str]:
    risks = []
    if rain > 120:
        risks.append("High rainfall → avoid long-duration root crops; ensure drainage.")
    if temp > 35:
        risks.append("Heat stress risk → prefer heat-tolerant varieties.")
    if humidity > 80:
        risks.append("High humidity → fungal disease risk; plan prophylactic sprays.")
    if rain < 20:
        risks.append("Low rainfall → consider drought-resistant crops.")
    return risks or ["No major risks detected."]


def _sowing_period(crops: List[str], season: str, state: str) -> Dict[str, str]:
    # Very rough demo timelines
    season_windows = {
        "Kharif": "Jun–Jul",
        "Rabi": "Oct–Nov",
        "Zaid": "Apr–May",
    }
    win = season_windows.get(season, "Seasonal")
    return {c: f"Ideal sowing: {win} (Region: {state or 'Unknown'})" for c in crops}


# ---------------------------
# Storage: farm_data.csv
# ---------------------------
def _save_farm_entry(row: Dict):
    csv_path = Path("farm_data.csv")
    cols = ["farmer", "plot_no", "lat", "lon", "area", "village", "district", "state"]
    df_new = pd.DataFrame([row], columns=cols)
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            df = pd.DataFrame(columns=cols)
        # update if plot_no exists, else append
        if ("plot_no" in df.columns) and (row["plot_no"] in set(df["plot_no"].astype(str))):
            df.loc[df["plot_no"].astype(str) == str(row["plot_no"]), cols] = df_new.iloc[0][cols].values
        else:
            df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(csv_path, index=False)


# ---------------------------
# Optional: Hindi translation
# ---------------------------
def _to_hindi(texts: List[str]) -> List[str]:
    try:
        from googletrans import Translator  # type: ignore
        tr = Translator()
        res = tr.translate(texts, dest="hi")
        return [r.text for r in res]
    except Exception:
        # Fallback: return original with note
        return [t for t in texts]


# ---------------------------
# Main UI
# ---------------------------
def show_smart_farm_map():
    # Title
    st.subheader("🗺️ Smart Farm Map & Analysis")
    st.caption("Mark your farm, analyze soil and weather, and get crop recommendations.")

    # Inputs
    with st.form("farm_form"):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            farmer = st.text_input("Farmer name", "Ramesh Kumar")
            plot_no = st.text_input("Plot/Survey number", "MK-101")
            area_ha = st.number_input("Land area (hectares)", min_value=0.1, value=1.0, step=0.1)
        with c2:
            village = st.text_input("Village", "Mohanpur")
            district = st.text_input("District", "Hyderabad")
            state = st.text_input("State", "Telangana")
        with c3:
            last_crop = st.text_input("Last crop grown", "Tomato")

        c4, c5 = st.columns([2, 2])
        with c4:
            lat = st.number_input("Latitude", value=17.3850, format="%f")
            lon = st.number_input("Longitude", value=78.4867, format="%f")
        with c5:
            search_q = st.text_input("Search by location (optional)", "Mohanpur Telangana India")
            if st.form_submit_button("Geocode Location"):
                pair = _geocode_location(search_q)
                if pair:
                    lat, lon = pair
                    st.success(f"Found: {lat:.5f}, {lon:.5f}")
                else:
                    st.warning("Could not geocode the query. Please adjust the text.")

        submitted = st.form_submit_button("Analyze Farm")

    # Save entry when submitted
    if submitted:
        _save_farm_entry({
            "farmer": farmer,
            "plot_no": plot_no,
            "lat": lat,
            "lon": lon,
            "area": area_ha,
            "village": village,
            "district": district,
            "state": state,
        })
        st.success("Farm entry saved locally to farm_data.csv")

    # Map-first layout
    st.markdown("---")
    st.markdown("#### 📍 Farm Location")
    # Folium map with clickable capture
    # Use CartoDB Positron to avoid OSM tile requests that can be blocked in some environments
    fmap = folium.Map(location=[lat, lon], zoom_start=13, control_scale=True, tiles="CartoDB positron")
    popup_html = folium.Popup(
        f"<b>{farmer}</b><br>Plot: {plot_no}<br>Area: {area_ha} ha<br>{village}, {district}, {state}",
        max_width=300
    )
    folium.Marker([lat, lon], popup=popup_html, tooltip=f"Plot {plot_no}").add_to(fmap)
    map_state = st_folium(fmap, height=420, width=None, returned_objects=["last_clicked"])

    # Allow users to refine lat/lon by clicking on map
    if map_state and map_state.get("last_clicked"):
        lat = float(map_state["last_clicked"]["lat"])
        lon = float(map_state["last_clicked"]["lng"]) 
        st.info(f"Updated location from map: {lat:.5f}, {lon:.5f}")

    # Analysis below map
    st.markdown("---")
    st.markdown("#### 📊 Soil & Climate Summary")
    # Soil
    soil_type, ph_range = _mock_soil(state)
    # Weather
    weather = _fetch_weather(lat, lon) or {"temp_c": 28.0, "humidity": 65.0, "rain_mm": 10.0, "description": "Clear"}
    # NDVI mock
    month = datetime.now().month
    ndvi = _mock_ndvi(lat, lon, month)
    season = _detect_season(month)

    c6, c7, c8, c9 = st.columns(4)
    with c6:
        st.metric("Soil Type", soil_type)
        st.caption(f"pH Range: {ph_range}")
    with c7:
        st.metric("Temperature (°C)", f"{weather['temp_c']:.1f}")
        st.caption(f"Humidity: {weather['humidity']:.0f}%")
    with c8:
        st.metric("Rainfall (mm)", f"{weather['rain_mm']:.1f}")
        st.caption(weather["description"])
    with c9:
        st.metric("NDVI", f"{ndvi:.2f}")
        st.caption(f"Season: {season}")

    # AI Recommendation Engine
    st.markdown("#### 🌱 Recommended Crops & Guidance")
    model_bundle = _train_mock_model()
    crops = _predict_next_crops(soil_type.split()[0], season, weather["temp_c"], weather["rain_mm"], last_crop, model_bundle)
    ferts = _fertilizer_suggestions(crops, soil_type, ph_range)
    risks = _risk_factors(weather["temp_c"], weather["rain_mm"], weather["humidity"])
    sow = _sowing_period(crops, season, state)

    c10, c11 = st.columns([2, 1])
    with c10:
        box = st.container(border=True)
        with box:
            st.write("**Best Seasonal Picks:**", ", ".join(crops))
            st.write("**Fertilizer Suggestions:**")
            for f in ferts:
                st.write("- ", f)
            st.write("**Risk Factors:**")
            for r in risks:
                st.write("- ", r)
    with c11:
        box2 = st.container(border=True)
        with box2:
            st.write("**Sowing Windows:**")
            for c in crops:
                st.write(f"- {c}: {sow[c]}")

    # Optional Hindi summary
    st.markdown("---")
    show_hi = st.checkbox("Show Hindi summary 🇮🇳")
    if show_hi:
        hi_texts = _to_hindi([
            f"Mitti ka prakar: {soil_type}; pH range: {ph_range}",
            f"Taapmaan: {weather['temp_c']:.1f}°C, Baarish: {weather['rain_mm']:.1f}mm, Aardrata: {weather['humidity']:.0f}%",
            f"Ritu: {season}; Uttam fasle: {', '.join(crops)}",
        ])
        st.info(" \n".join(hi_texts))

    # Footer hints
    st.caption("Data saved locally in farm_data.csv for testing. Weather via OpenWeatherMap; soil/NDVI are mock estimates for demo.")