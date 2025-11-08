# utils/firebase_service.py
import os
import json
import streamlit as st
from utils import helpers
import glob

# Try to initialize Firebase; if not available, run in mock mode
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    _HAS_FIREBASE = True
except Exception:
    _HAS_FIREBASE = False

_DB = None

def get_db():
    global _DB
    if _DB:
        return _DB

    require_real = helpers.read_env_bool("REQUIRE_REAL_DB", False) or helpers.read_env_bool("REQUIRE_REAL_FIREBASE", False)
    if _HAS_FIREBASE:
        # Look for path in env var or Streamlit secrets
        cred_path = helpers.env_or_secret("FIREBASE_CRED_PATH", "")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            try:
                firebase_admin.initialize_app(cred)
            except Exception:
                # already initialized
                pass
            _DB = firestore.client()
            return _DB
        else:
            # Fallback: try to auto-detect service account JSON in ./config/
            config_dir = os.path.join(os.getcwd(), "config")
            json_candidates = []
            try:
                if os.path.isdir(config_dir):
                    json_candidates = glob.glob(os.path.join(config_dir, "*.json"))
            except Exception:
                json_candidates = []
            if json_candidates:
                auto_path = json_candidates[0]
                try:
                    cred = credentials.Certificate(auto_path)
                    try:
                        firebase_admin.initialize_app(cred)
                    except Exception:
                        pass
                    _DB = firestore.client()
                    st.info(f"Using Firebase credentials from: {auto_path}")
                    return _DB
                except Exception as e:
                    st.error(f"Failed to initialize Firebase from {auto_path}: {e}")
            if require_real:
                st.error("Firebase credentials not found and real mode is required. Set FIREBASE_CRED_PATH or place JSON in ./config.")
                raise RuntimeError("Firebase real mode required but credentials missing")
            st.warning("Firebase credentials not found. Running in demo mode.")
    else:
        if require_real:
            st.error("Firebase Admin SDK not installed and real mode is required. Add firebase-admin to requirements and set FIREBASE_CRED_PATH.")
            raise RuntimeError("Firebase real mode required but SDK missing")
        st.warning("Firebase admin SDK not installed or available. Running in demo mode.")
    # Mock DB object
    _DB = MockDB()
    return _DB

def log_help_request(db, payload):
    """
    store help requests to Firestore collection 'help_requests'
    In mock DB, it just prints.
    """
    if isinstance(db, MockDB):
        db.log("help_requests", payload)
    else:
        db.collection("help_requests").add(payload)

def add_marketplace_listing(db, listing):
    """
    store marketplace listings to Firestore collection 'marketplace_listings'.
    In mock DB, it just prints.
    """
    if isinstance(db, MockDB):
        db.log("marketplace_listings", listing)
    else:
        db.collection("marketplace_listings").add(listing)

def save_user_profile(db, profile: dict):
    """
    Save a basic user profile to Firestore collection 'users'.
    In mock DB, it just prints/logs.
    """
    if isinstance(db, MockDB):
        db.log("users", profile)
    else:
        db.collection("users").add(profile)

def save_sustainability_score(db, payload: dict):
    """Save sustainability score to 'sustainability_scores' collection."""
    if isinstance(db, MockDB):
        db.log("sustainability_scores", payload)
    else:
        db.collection("sustainability_scores").add(payload)

def save_volunteer_profile(db, profile: dict):
    """
    Save a volunteer profile to Firestore collection 'volunteers'.
    In mock DB, it just prints/logs.
    """
    if isinstance(db, MockDB):
        db.log("volunteers", profile)
    else:
        db.collection("volunteers").add(profile)

def get_volunteers(db):
    """
    Retrieve all volunteer profiles from 'volunteers' collection.
    In mock DB, return empty list.
    """
    if isinstance(db, MockDB):
        return []
    else:
        docs = db.collection("volunteers").stream()
        return [doc.to_dict() for doc in docs]

def log_volunteer_help_request(db, payload: dict):
    """
    Log a help request assigned to a volunteer in 'volunteer_help_requests'.
    In mock DB, it just prints.
    """
    if isinstance(db, MockDB):
        db.log("volunteer_help_requests", payload)
    else:
        db.collection("volunteer_help_requests").add(payload)

def db_status(db) -> str:
    if isinstance(db, MockDB):
        return "Firebase: demo mode"
    try:
        # Firestore client does not expose project id directly; show generic connected
        return "Firebase: connected (Firestore)"
    except Exception:
        return "Firebase: connected"

def is_demo(db) -> bool:
    return isinstance(db, MockDB)

class MockDB:
    def __init__(self):
        self.storage = {}
    def log(self, collection, doc):
        self.storage.setdefault(collection, []).append(doc)
        print(f"[MockDB] logged to {collection}: {doc}")
    def collection(self, collection):
        # minimal Firestore-like API for reading/writing in real mode only
        raise NotImplementedError("Mock collection not implemented for reads.")
