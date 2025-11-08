import json
from backend import app

def main():
    c = app.test_client()
    results = {
        "health": c.get("/api/health").get_json(),
        "dashboard": c.get("/api/dashboard").get_json(),
        "marketplace_post": c.post("/api/marketplace", json={"action": "create"}).get_json(),
        "sustainability_post": c.post(
            "/api/sustainability",
            json={"pillars": {"Water": 0.5, "Soil": 0.6}, "weights": {"Water": 1, "Soil": 1}},
        ).get_json(),
        "social_post": c.post("/api/social", json={"message": "Hi"}).get_json(),
        "tech_portal": c.get("/api/tech_portal").get_json(),
        "maps": c.get("/api/maps").get_json(),
        "root": c.get("/").get_json(),
    }
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()