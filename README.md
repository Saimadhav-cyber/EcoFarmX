# EcoFarmX — Hackathon MVP (Maps + SOS + Marketplace demo)

## What this repo contains
- Streamlit app that demos:
  - Farm location mapping (click map or enter coords)
  - SOS help request (SMS mock or real via Twilio)
  - Tech Champion portal (demo)
  - Marketplace (demo listings)
  
  Works in demo mode if Firebase or Twilio are not configured.
  Now supports Firebase (Firestore) and MongoDB. Both run in demo mode if not configured.

## Setup (No venv)
1. Install Python 3.9+.
2. Install requirements:
   - Linux/macOS: `pip3 install --user -r requirements.txt`
   - Windows: `pip install -r requirements.txt` (or use `--user`)

## Configure credentials (optional for real services)
Set environment variables (or set them in your Streamlit Cloud Secrets):

- Firebase: set `FIREBASE_CRED_PATH` to the path of the service account JSON file.
- Twilio:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`

- MongoDB:
  - `MONGODB_URI` (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority`)
  - `MONGODB_DB` (optional, defaults to `ecofarmx`)

You can also use `.streamlit/secrets.toml` with keys `FIREBASE_CRED_PATH`, `MONGODB_URI`, `MONGODB_DB` for local development.

### Enforce real mode (disable demo)
Set one or more of the following flags to require real services:
- `REQUIRE_REAL_DB=true` (global)
- `REQUIRE_REAL_FIREBASE=true`
- `REQUIRE_REAL_MONGO=true`
- `REQUIRE_REAL_SMS=true`

When a required service is not configured, the app will show an error and stop.

See `.streamlit/secrets.example.toml` for a template.


- The widget will render inside the Streamlit page.

## Run locally
```bash
streamlit run app.py
