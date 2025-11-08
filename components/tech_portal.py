# components/tech_portal.py
import streamlit as st
from data.demo_data import get_demo_farmers, get_demo_volunteers
from components import maps as maps_comp
from utils import firebase_service, mongo_service, helpers

def show_tech_champion_portal(fire_db, mongo_db):
    st.header("👨‍💻 Tech Champion Portal")
    user_name = st.session_state.get("user_name", "Tech Champion")
    st.success(f"Welcome, {user_name}! Manage your profile and help requests.")

    # Profile Management
    st.subheader("Your Profile")
    volunteers = get_demo_volunteers() + firebase_service.get_volunteers(fire_db) + mongo_service.get_volunteers(mongo_db)
    volunteer = next((v for v in volunteers if v["name"] == user_name), None)
    if not volunteer:
        # Create default profile
        volunteer = {
            "name": user_name,
            "district": "Hyderabad",
            "languages": ["English", "Hindi"],
            "phone": "+91 98765 43210",
            "availability": "Online",
            "location": (17.3850, 78.4867)
        }
        firebase_service.save_volunteer_profile(fire_db, volunteer)
        mongo_service.save_volunteer_profile(mongo_db, volunteer)

    with st.form("profile_form"):
        name = st.text_input("Name", volunteer["name"])
        district = st.text_input("District", volunteer["district"])
        languages = st.multiselect("Languages Known", ["English", "Hindi", "Telugu"], default=volunteer["languages"])
        phone = st.text_input("Contact Number", volunteer["phone"])
        availability = st.selectbox("Availability", ["Online", "Offline"], index=0 if volunteer["availability"] == "Online" else 1)
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            updated_profile = {
                "name": name,
                "district": district,
                "languages": languages,
                "phone": phone,
                "availability": availability,
                "location": volunteer["location"]
            }
            firebase_service.save_volunteer_profile(fire_db, updated_profile)
            mongo_service.save_volunteer_profile(mongo_db, updated_profile)
            st.success("Profile updated!")

    # Help Requests
    st.subheader("Incoming Help Requests")
    # In demo, show mock requests; in real, fetch from DB
    st.write("Recent requests assigned to you:")
    st.write("- Farmer Ramesh: App Help — 10 mins ago")
    st.write("- Farmer Laxmi: Product Upload Issue — 30 mins ago")

    # Assigned Farmers
    st.subheader("Assigned Farmers")
    farmers = get_demo_farmers()
    for f in farmers:
        with st.expander(f"👨‍🌾 {f['name']} — {f['village']}"):
            st.write(f"Phone: {f['phone']}")
            st.write(f"Sustainability Score: {f['sustainability_score']}")
            if f.get("farm_location"):
                lat, lon = f["farm_location"]
                st.write(f"Location: {lat:.5f}, {lon:.5f}")
                if st.button(f"Show on Map - {f['name']}"):
                    maps_comp.show_map_preview(lat, lon)
            else:
                st.info("No location saved for this farmer.")
