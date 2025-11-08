# components/maps.py
import streamlit as st
from streamlit_folium import st_folium
import folium

def map_select_ui():
    """
    Renders a map and lets user click to pick a coordinate.
    Returns (lat, lon) or (None, None)
    """
    st.info("Click on the map to set your farm location. If you cannot click, fill coordinates manually below.")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    folium.TileLayer('OpenStreetMap').add_to(m)

    # render map
    output = st_folium(m, width=700, height=400)

    lat = lon = None
    if output and output.get("last_clicked"):
        lat = output["last_clicked"]["lat"]
        lon = output["last_clicked"]["lng"]
        st.success(f"Selected: {lat:.5f}, {lon:.5f}")

    c1, c2 = st.columns(2)
    with c1:
        lat_manual = st.text_input("Or enter latitude (decimal)", "")
    with c2:
        lon_manual = st.text_input("Or enter longitude (decimal)", "")

    if lat_manual and lon_manual:
        try:
            lat = float(lat_manual.strip())
            lon = float(lon_manual.strip())
        except Exception:
            st.error("Invalid manual coordinates")

    return lat, lon

def show_map_preview(lat, lon):
    if not (lat and lon):
        st.error("No coords to show")
        return
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], tooltip="Farm Location").add_to(m)
    st_folium(m, width=700, height=400)
