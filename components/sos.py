# components/sos.py
import streamlit as st
import requests
from utils import helpers
from components import maps as maps_comp

def show_helpline():
    st.header("🆘 Immediate Help Center")

    st.warning("Press the button below if you need immediate assistance. A Tech Champion will be alerted.")

    name = st.text_input("Your Name", "Ramesh Kumar")
    phone = st.text_input("Your Phone", "+91 98765 43210")
    problem = st.selectbox("Type of problem", ["Crop Disease", "Equipment Issue", "Medical Emergency", "App Help", "Other"])
    st.markdown("**Map / Location**")
    lat, lon = maps_comp.map_select_ui()  # returns (lat, lon) or (None, None)

    if st.button("🚨 REQUEST HELP NOW"):
        base = helpers.env_or_secret("BACKEND_URL", "http://localhost:5000")
        payload = {"name": name, "phone": phone, "problem": problem, "lat": lat, "lon": lon}
        try:
            resp = requests.post(f"{base}/api/sos", json=payload, timeout=12)
            data = resp.json()
        except Exception as e:
            data = {"ok": False, "error": str(e)}
        if not data.get("ok"):
            st.error(f"Failed to send help request via API: {data.get('error', 'unknown error')}")
        else:
            st.success("✅ Help alert sent! Tech Champions alerted.")
