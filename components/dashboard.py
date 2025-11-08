# components/dashboard.py
import streamlit as st
from utils import firebase_service
from data.demo_data import get_demo_farmers

def show_farmer_dashboard(db):
    st.header("👨‍🌾 Farmer Dashboard")
    # In real app, fetch farmer by auth; here show demo farmer
    farmer = get_demo_farmers()[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌿 Sustainability Score", f"{farmer['sustainability_score']}/100")
        st.progress(farmer['sustainability_score'] / 100)
    with col2:
        st.metric("🏷️ Eco Practices", ", ".join(farmer['practices']))
    with col3:
        st.metric("📞 Contact", farmer['phone'])

    st.subheader("📍 Your Farm Location")
    if farmer.get("farm_location"):
        lat, lon = farmer["farm_location"]
        st.write(f"Saved Coordinates: {lat:.5f}, {lon:.5f}")
        st.write(f"[Open in Google Maps](https://maps.google.com/?q={lat},{lon})")
    else:
        st.info("No farm location saved. Go to 'Get Help' → Map to set location.")

    st.subheader("🚀 Quick Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🆘 Request Help"):
            st.session_state.show_help = True
            st.experimental_rerun()
    with c2:
        if st.button("📱 Share Story"):
            st.success("Share message prepared (copy from UI).")
