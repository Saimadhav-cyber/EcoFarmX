# app.py - Main Streamlit entrypoint
import streamlit as st
import requests
from components import dashboard, sos_new as sos, tech_portal
from components import auth, sustainability, social, image_verification, marketplace_chat, smart_farm_map
from utils import firebase_service, helpers
from utils import mongo_service

st.set_page_config(page_title="EcoFarmX", page_icon="🌱", layout="wide")

# Backend API base URL (env or Streamlit secrets), default to localhost
BACKEND_URL = helpers.env_or_secret("BACKEND_URL", "http://localhost:5000")

# Initialize databases (Firebase/Firestore and MongoDB or mock fallbacks)
fire_db = firebase_service.get_db()
mongo_db = mongo_service.get_db()
require_real = helpers.read_env_bool("REQUIRE_REAL_DB", False)


def api_get(path: str, timeout: float = 10.0):
    try:
        resp = requests.get(f"{BACKEND_URL}{path}", timeout=timeout)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def api_post(path: str, payload: dict, timeout: float = 10.0):
    try:
        resp = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    st.markdown("<h1 style='text-align:center'>🌱 EcoFarmX — Farmer Support & Marketplace</h1>", unsafe_allow_html=True)
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "",
        [
            "📲 Auth & Login",
            "Farmer Dashboard",
            "🆘 Get Help",
            "🗺️ Smart Farm Map",
            "🛍️ AI Assistant + Market",
            "👨‍💻 Tech Champion Portal",
            "📷 Image Verification",
            
            "🌿 Sustainability Score",
            "📣 Social Sharing",
            
        ],
    )

    # Simple auth stub: choose demo users
    st.sidebar.markdown("### Demo users")
    user_type = st.sidebar.selectbox("I am:", ["Farmer: Ramesh", "Tech Champion: Priya", "Viewer (Demo)"])
    st.session_state.setdefault("user_type", user_type)
    # Set user context based on selection
    if "Farmer:" in user_type:
        st.session_state["user_role"] = "farmer"
        st.session_state["user_name"] = user_type.split(": ")[1]
    elif "Tech Champion:" in user_type:
        st.session_state["user_role"] = "volunteer"
        st.session_state["user_name"] = user_type.split(": ")[1]
    else:
        st.session_state["user_role"] = "viewer"
        st.session_state["user_name"] = "Demo User"

    if page == "📲 Auth & Login":
        auth.show_auth(fire_db)
    elif page == "Farmer Dashboard":
        # Fetch dashboard data from backend API
        data = api_get("/api/dashboard")
        if not data.get("ok"):
            st.error(f"Failed to load dashboard data from API: {data.get('error', 'unknown error')}")
        else:
            dashboard.show_farmer_dashboard(data.get("farmer"))
    elif page == "🆘 Get Help":
        sos.show_helpline()
    elif page == "🗺️ Smart Farm Map":
        smart_farm_map.show_smart_farm_map()
    elif page == "🛍️ AI Assistant + Market":
        marketplace_chat.show_marketplace_chat(fire_db, mongo_db)
    elif page == "👨‍💻 Tech Champion Portal":
        tech_portal.show_tech_champion_portal(fire_db)
    elif page == "📷 Image Verification":
        image_verification.show_image_verification()
    
    elif page == "🌿 Sustainability Score":
        sustainability.show_sustainability(fire_db, mongo_db)
    elif page == "📣 Social Sharing":
        social.show_social_share()

    st.sidebar.markdown("---")
    st.sidebar.markdown("Project: EcoFarmX — Hackathon MVP")
    st.sidebar.markdown("Features: Auth, Mapping, SOS, Marketplace, Sustainability, Social, Insights.")
    st.sidebar.markdown("---")
    # Show backend/API health if available
    api_health = api_get("/api/health")
    if api_health.get("ok"):
        st.sidebar.caption("API: healthy")
    else:
        st.sidebar.caption("API: unavailable")
    st.sidebar.caption(firebase_service.db_status(fire_db))
    st.sidebar.caption(mongo_service.db_status(mongo_db))

    # If real mode is required globally, gate the app if any service is in demo
    if require_real:
        in_demo = firebase_service.is_demo(fire_db) or mongo_service.is_demo(mongo_db)
        if in_demo:
            st.error("Real mode required: configure Firebase and MongoDB credentials. See README for setup.")
            st.stop()

if __name__ == "__main__":
    main()
