# utils/mongo_service.py
import os
import streamlit as st
from utils import helpers

# Try to initialize pymongo; if not available, run in mock mode
try:
    import pymongo
    _HAS_PYMONGO = True
except Exception:
    _HAS_PYMONGO = False

_CLIENT = None
_DB = None

def _read_secret(name: str, default: str = ""):
    # Prefer Streamlit secrets if present (using helpers for compatibility)
    try:
        from utils import helpers
        return helpers.read_secret_str(name, default)
    except Exception:
        return default

def get_db():
    """Return a MongoDB database handle or a mock DB if unavailable.

    Uses env vars or Streamlit secrets:
      - MONGODB_URI: connection string (e.g., mongodb+srv://user:pass@cluster/...)
      - MONGODB_DB: database name (default: ecofarmx)
    """
    global _CLIENT, _DB
    if _DB is not None:
        return _DB

    uri = os.getenv("MONGODB_URI") or _read_secret("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB") or _read_secret("MONGODB_DB", "ecofarmx") or "ecofarmx"
    require_real = helpers.read_env_bool("REQUIRE_REAL_DB", False) or helpers.read_env_bool("REQUIRE_REAL_MONGO", False)

    if _HAS_PYMONGO and uri:
        try:
            _CLIENT = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
            # touch server to validate (non-blocking quick check)
            try:
                _CLIENT.admin.command("ping")
            except Exception:
                pass
            _DB = _CLIENT[db_name]
            return _DB
        except Exception as e:
            st.warning(f"MongoDB connection failed, using demo mode: {e}")
    else:
        if require_real:
            if not _HAS_PYMONGO:
                st.error("pymongo not installed and real mode is required. Install pymongo and set MONGODB_URI.")
                raise RuntimeError("MongoDB real mode required but pymongo missing")
            else:
                st.error("MONGODB_URI not set and real mode is required. Set MONGODB_URI.")
                raise RuntimeError("MongoDB real mode required but URI missing")
        else:
            if not _HAS_PYMONGO:
                st.warning("pymongo not installed. Running MongoDB in demo mode.")
            else:
                st.info("MONGODB_URI not set. Using demo mode.")

    _DB = MockMongoDB()
    return _DB

def db_status(db) -> str:
    if isinstance(db, MockMongoDB):
        return "MongoDB: demo mode"
    try:
        name = getattr(db, "name", "ecofarmx")
        return f"MongoDB: connected to '{name}'"
    except Exception:
        return "MongoDB: connected"

def is_demo(db) -> bool:
    return isinstance(db, MockMongoDB)

def log_help_request(db, payload: dict):
    """Insert a help request document into 'help_requests'."""
    if isinstance(db, MockMongoDB):
        db.log("help_requests", payload)
    else:
        db["help_requests"].insert_one(payload)

def insert_marketplace_listing(db, listing: dict):
    """Insert a marketplace listing document into 'marketplace_listings'."""
    if isinstance(db, MockMongoDB):
        db.log("marketplace_listings", listing)
    else:
        db["marketplace_listings"].insert_one(listing)

def save_sustainability_score(db, payload: dict):
    """Insert a sustainability score document into 'sustainability_scores'."""
    if isinstance(db, MockMongoDB):
        db.log("sustainability_scores", payload)
    else:
        db["sustainability_scores"].insert_one(payload)

def save_volunteer_profile(db, profile: dict):
    """Insert a volunteer profile document into 'volunteers'."""
    if isinstance(db, MockMongoDB):
        db.log("volunteers", profile)
    else:
        db["volunteers"].insert_one(profile)

def get_volunteers(db):
    """Retrieve all volunteer profiles from 'volunteers' collection."""
    if isinstance(db, MockMongoDB):
        return []
    else:
        return list(db["volunteers"].find({}))

def log_volunteer_help_request(db, payload: dict):
    """Insert a help request assigned to a volunteer into 'volunteer_help_requests'."""
    if isinstance(db, MockMongoDB):
        db.log("volunteer_help_requests", payload)
    else:
        db["volunteer_help_requests"].insert_one(payload)

class MockMongoDB:
    def __init__(self):
        self.storage = {}
        self.name = "mock_ecofarmx"
    def log(self, collection, doc):
        self.storage.setdefault(collection, []).append(doc)
        print(f"[MockMongo] logged to {collection}: {doc}")
    def __getitem__(self, name):
        # Simulate collections
        return MockCollection(self.storage.setdefault(name, []))

class MockCollection:
    def __init__(self, bucket):
        self.bucket = bucket
    def insert_one(self, doc):
        self.bucket.append(doc)
        print(f"[MockMongo] insert_one: {doc}")

# --- Additional helpers used by backend API ---
def save_market_action(db, payload: dict):
    """Record marketplace actions (create/update/listing interactions)."""
    if isinstance(db, MockMongoDB):
        db.log("market_actions", payload)
    else:
        db["market_actions"].insert_one(payload)

def save_sustainability(db, payload: dict):
    """Alias for saving sustainability score documents."""
    # Reuse existing collection name for consistency
    if isinstance(db, MockMongoDB):
        db.log("sustainability_scores", payload)
    else:
        db["sustainability_scores"].insert_one(payload)

def save_share(db, payload: dict):
    """Record social share payloads (messages/links)."""
    if isinstance(db, MockMongoDB):
        db.log("social_shares", payload)
    else:
        db["social_shares"].insert_one(payload)