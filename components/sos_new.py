import streamlit as st
import requests
from utils import helpers, firebase_service, mongo_service
from data.demo_data import get_demo_farmers, get_demo_volunteers
from components import maps as maps_comp

def show_helpline():
    st.header("🆘 Get Help (SOS)")

    user_role = st.session_state.get("user_role", "viewer")
    if user_role != "farmer":
        st.warning("This feature is for farmers. Please select a farmer user from the sidebar.")
        return

    user_name = st.session_state.get("user_name", "Farmer")
    farmer = next((f for f in get_demo_farmers() if f["name"] == user_name), None)
    if not farmer:
        st.error("Farmer profile not found.")
        return

    # Existing SOS form
    st.subheader("Immediate Help Center")
    st.warning("Press the button below if you need immediate assistance. A Tech Champion will be alerted.")

    name = st.text_input("Your Name", farmer["name"])
    phone = st.text_input("Your Phone", farmer["phone"])
    problem = st.selectbox("Type of problem", ["Crop Disease", "Equipment Issue", "Medical Emergency", "App Help", "Product Upload", "Certifications", "Sustainability Scores", "Other"])
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

    st.markdown("---")

    # New Volunteer Connect Feature
    st.subheader("Need Help? Connect with a Volunteer")
    if st.button("🔗 Find a Nearby Volunteer"):
        st.info("Finding a nearby volunteer for you...")

        # Get farmer location
        if lat and lon:
            farmer_lat, farmer_lon = lat, lon
        elif farmer.get("farm_location"):
            farmer_lat, farmer_lon = farmer["farm_location"]
        else:
            st.error("No location available. Please set your location above.")
            return

        # Reverse geocode to get district
        geo = helpers.mock_reverse_geocode(farmer_lat, farmer_lon)
        farmer_district = geo["district"]
        farmer_language = farmer.get("language", "English")

        # Get volunteers (demo + DB)
        fire_db = firebase_service.get_db()
        mongo_db = mongo_service.get_db()
        volunteers = get_demo_volunteers() + firebase_service.get_volunteers(fire_db) + mongo_service.get_volunteers(mongo_db)

        # Find best volunteer
        best_volunteer = helpers.find_best_volunteer(farmer_lat, farmer_lon, farmer_district, farmer_language, volunteers)

        if best_volunteer:
            st.success(f"✅ Matched with {best_volunteer['name']} ({best_volunteer['district']})")
            st.write(f"**Contact:** {best_volunteer['phone']}")
            st.write(f"**Languages:** {', '.join(best_volunteer['languages'])}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📞 Call Volunteer"):
                    st.info("Mock call initiated. In real app, this would dial the number.")
            with col2:
                if st.button("🚨 Report Issue"):
                    st.info("Issue reported to admin. Escalating...")
                    # Log escalation
                    escalation_payload = {"farmer": user_name, "volunteer": best_volunteer["name"], "issue": "Unresolved help request"}
                    firebase_service.log_volunteer_help_request(fire_db, escalation_payload)
                    mongo_service.log_volunteer_help_request(mongo_db, escalation_payload)

            # Feedback after session
            st.markdown("### Rate Your Experience")
            rating = st.slider("Rate the volunteer's support (1-5 stars)", 1, 5, 5)
            feedback = st.text_area("Additional feedback (optional)")
            if st.button("Submit Feedback"):
                feedback_payload = {"farmer": user_name, "volunteer": best_volunteer["name"], "rating": rating, "feedback": feedback}
                firebase_service.log_volunteer_help_request(fire_db, feedback_payload)
                mongo_service.log_volunteer_help_request(mongo_db, feedback_payload)
                st.success("Thank you for your feedback!")
        else:
            st.warning("No nearby volunteer found. Connecting you via call.")
            st.info("Mock call to helpline initiated. In real app, this would connect to a general support line.")
            if st.button("🚨 Report Issue"):
                st.info("Issue reported to admin.")
                escalation_payload = {"farmer": user_name, "issue": "No volunteer available"}
                firebase_service.log_volunteer_help_request(fire_db, escalation_payload)
                mongo_service.log_volunteer_help_request(mongo_db, escalation_payload)
