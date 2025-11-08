# backend.py - Flask API for EcoFarmX
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Any, Dict

from utils import firebase_service, mongo_service, sms_service, helpers
from data.demo_data import get_demo_farmers

app = Flask(__name__)
CORS(app)


def services_status() -> Dict[str, Any]:
    fire_db = firebase_service.get_db()
    mongo_db = mongo_service.get_db()
    return {
        "firebase": firebase_service.db_status(fire_db),
        "mongo": mongo_service.db_status(mongo_db),
        "demo": firebase_service.is_demo(fire_db) or mongo_service.is_demo(mongo_db),
    }


@app.get("/api/health")
def health():
    try:
        status = services_status()
        return jsonify({"ok": True, "status": status})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/dashboard")
def dashboard():
    try:
        farmer = get_demo_farmers()[0]
        return jsonify({"ok": True, "farmer": farmer})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/sos")
def sos():
    try:
        data = request.get_json(force=True)
        name = data.get("name")
        phone = data.get("phone")
        problem = data.get("problem")
        lat = data.get("lat")
        lon = data.get("lon")
        map_link = f"https://maps.google.com/?q={lat},{lon}" if lat and lon else "Location not provided"
        message = f"HELP REQUEST from {name}. Issue: {problem}. Location: {map_link}. Contact: {phone}"
        sent = sms_service.send_help_alert(name, phone, message)

        payload = {"name": name, "phone": phone, "problem": problem, "lat": lat, "lon": lon}
        fire_db = firebase_service.get_db()
        mongo_db = mongo_service.get_db()
        try:
            firebase_service.log_help_request(fire_db, payload)
        except Exception:
            pass
        try:
            mongo_service.log_help_request(mongo_db, payload)
        except Exception:
            pass
        return jsonify({"ok": True, "sms": bool(sent)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/api/marketplace")
def marketplace_get():
    try:
        # Demo listings
        listings = [
            {"product": "Urea", "category": "Fertilizer", "price": 580, "rating": 4.2, "available": True,
             "freshness_h": 12, "lat": 12.91, "lon": 77.59, "seller": "AgroMart"},
            {"product": "Paddy Seed", "category": "Seed", "price": 1200, "rating": 4.7, "available": True,
             "freshness_h": 48, "lat": 12.88, "lon": 77.62, "seller": "GreenSeeds"},
        ]
        return jsonify({"ok": True, "listings": listings})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/marketplace")
def marketplace_post():
    try:
        data = request.get_json(force=True)
        action = data.get("action", "create")
        # Persist in DBs if needed
        mongo_db = mongo_service.get_db()
        try:
            mongo_service.save_market_action(mongo_db, data)
        except Exception:
            pass
        return jsonify({"ok": True, "action": action})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/auth/send_otp")
def auth_send_otp():
    try:
        data = request.get_json(force=True)
        phone = data.get("phone")
        message = data.get("message") or "EcoFarmX login code"
        sent = sms_service.send_help_alert("EcoFarmX", phone, message)
        return jsonify({"ok": bool(sent)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/api/sustainability")
def sustainability_get():
    try:
        # Demo pillars
        return jsonify({
            "ok": True,
            "score": 72,
            "pillars": {"Water": 0.68, "Soil": 0.75, "Energy": 0.6, "Biodiversity": 0.85, "Economics": 0.7},
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/sustainability")
def sustainability_post():
    try:
        data = request.get_json(force=True)
        pillars = data.get("pillars", {})
        weights = data.get("weights", {})
        # Simple weighted average
        total_w = sum(weights.values()) or 1.0
        score = 0.0
        for k, v in pillars.items():
            w = weights.get(k, 1.0)
            score += (v * w)
        score = int(round(100 * (score / total_w)))
        # Save to Mongo
        try:
            mongo_service.save_sustainability(mongo_service.get_db(), {"pillars": pillars, "weights": weights, "score": score})
        except Exception:
            pass
        return jsonify({"ok": True, "score": score})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/api/social")
def social_get():
    try:
        return jsonify({"ok": True, "message": "EcoFarmX helps farmers with sustainable practices!"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/social")
def social_post():
    try:
        data = request.get_json(force=True)
        mongo_service.save_share(mongo_service.get_db(), data)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/api/tech_portal")
def tech_portal_get():
    try:
        champs = [
            {"name": "Priya", "region": "Telangana", "phone": "+919876543210"},
            {"name": "Arun", "region": "Tamil Nadu", "phone": "+919812345678"},
        ]
        return jsonify({"ok": True, "champions": champs})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/image_verification")
def image_verification_post():
    try:
        data = request.get_json(force=True)
        # Stub: classify as genuine if length of url/text even
        text = data.get("image_url", "")
        result = {"verified": (len(text) % 2 == 0), "confidence": 0.75}
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.get("/api/maps")
def maps_get():
    try:
        boundaries = [{"name": "My Farm", "coords": [[77.6, 12.9], [77.605, 12.9], [77.605, 12.905], [77.6, 12.905]]}]
        risks = [{"type": "Drought", "lat": 12.91, "lon": 77.60, "level": "High"}]
        return jsonify({"ok": True, "boundaries": boundaries, "risks": risks})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/")
def root():
    return jsonify({"ok": True, "message": "EcoFarmX API running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)