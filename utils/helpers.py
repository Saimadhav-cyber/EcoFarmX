# utils/helpers.py
import os
import streamlit as st

def read_env_bool(name, default=False):
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y")

def read_secret_str(name, default=""):
    """Safely read a string from Streamlit secrets, returning default if missing."""
    try:
        # st.secrets behaves like a mapping; use [] for compatibility
        return st.secrets[name]
    except Exception:
        return default

def env_or_secret(name, default=""):
    """Return the env var if set, else try Streamlit secrets, else default."""
    return os.getenv(name) or read_secret_str(name, default)

def mock_reverse_geocode(lat, lon):
    """Mock reverse geocoding to get district/village from lat/lon."""
    # Simple mock based on coordinates
    if 17.3 < lat < 17.5 and 78.4 < lon < 78.5:
        return {"district": "Hyderabad", "village": "Mohanpur"}
    elif 19.0 < lat < 19.1 and 72.8 < lon < 72.9:
        return {"district": "Mumbai", "village": "Andheri"}
    else:
        return {"district": "Unknown", "village": "Unknown"}

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate Euclidean distance between two points (in degrees, for demo)."""
    return ((lat1 - lat2)**2 + (lon1 - lon2)**2)**0.5

def find_best_volunteer(farmer_lat, farmer_lon, farmer_district, farmer_language, volunteers):
    """Find the best matching volunteer based on location and language."""
    if not volunteers:
        return None

    # Filter online volunteers
    online_volunteers = [v for v in volunteers if v.get("availability") == "Online"]

    if not online_volunteers:
        return None

    # Prioritize same district
    same_district = [v for v in online_volunteers if v.get("district") == farmer_district]
    if same_district:
        candidates = same_district
    else:
        candidates = online_volunteers

    # Within candidates, prioritize same language
    same_lang = [v for v in candidates if farmer_language in v.get("languages", [])]
    if same_lang:
        candidates = same_lang

    # Find nearest by distance
    best_volunteer = min(candidates, key=lambda v: calculate_distance(farmer_lat, farmer_lon, v["location"][0], v["location"][1]))
    return best_volunteer
