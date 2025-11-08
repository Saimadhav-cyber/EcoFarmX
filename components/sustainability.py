import streamlit as st
import json
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from utils import firebase_service, mongo_service
from utils import sms_service


# Pillars for sub-score model
PILLARS = [
    "Soil Health",
    "Water Stewardship",
    "Nutrient Efficiency",
    "Biodiversity",
    "Emissions",
    "Waste Management",
    "Social",
]


def dynamic_weights(crop: str, irrigation: str, state: str) -> dict:
    base = {
        "Soil Health": 0.18,
        "Water Stewardship": 0.18,
        "Nutrient Efficiency": 0.16,
        "Biodiversity": 0.14,
        "Emissions": 0.14,
        "Waste Management": 0.10,
        "Social": 0.10,
    }
    if irrigation.lower() in {"drip", "sprinkler"}:
        base["Water Stewardship"] += 0.04
        base["Emissions"] -= 0.02
        base["Waste Management"] -= 0.02
    if crop.lower() in {"rice", "paddy"}:
        base["Water Stewardship"] += 0.05
        base["Emissions"] += 0.04
        base["Biodiversity"] -= 0.03
        base["Waste Management"] -= 0.06
    if state.lower() in {"rajasthan", "gujarat"}:
        base["Water Stewardship"] += 0.04
        base["Soil Health"] += 0.02
        base["Emissions"] -= 0.02
        base["Waste Management"] -= 0.04
    # Normalize to sum to 1.0
    total = sum(base.values())
    return {k: v / total for k, v in base.items()}


def compute_subscores(inputs: dict) -> dict:
    soil = min(100, 50 + inputs.get("organic_matter", 1) * 8 + (5 if inputs.get("crop_rotation") else 0) + (5 if inputs.get("mulching") else 0))
    water = min(100, 40 + (15 if inputs.get("irrigation") in ["drip", "sprinkler"] else 0) + int(inputs.get("rainwater_harvest", False)) * 15 + max(0, 20 - inputs.get("water_use_index", 10)))
    nutrient = min(100, 45 + max(0, 18 - inputs.get("urea_kg_per_acre", 50) // 10) + (10 if inputs.get("soil_test") else 0) + (7 if inputs.get("balanced_npk") else 0))
    biodiversity = min(100, 35 + (12 if inputs.get("intercropping") else 0) + (10 if inputs.get("border_trees") else 0) + (10 if inputs.get("flower_strips") else 0))
    emissions = max(0, 80 - (inputs.get("diesel_liters", 10) * 2) - (20 if inputs.get("residue_burning") else 0) + (10 if inputs.get("solar_pump") else 0))
    waste = min(100, 50 + (inputs.get("compost_fraction", 0.3) * 40) - (15 if inputs.get("plastic_mulch") else 0) + (10 if inputs.get("bio_pesticides") else 0))
    social = min(100, 50 + (10 if inputs.get("farmer_training") else 0) + (10 if inputs.get("women_participation") else 0) + (10 if inputs.get("community_sharing") else 0))
    return {
        "Soil Health": round(soil),
        "Water Stewardship": round(water),
        "Nutrient Efficiency": round(nutrient),
        "Biodiversity": round(biodiversity),
        "Emissions": round(emissions),
        "Waste Management": round(waste),
        "Social": round(social),
    }


def overall_score(subscores: dict, weights: dict) -> int:
    val = sum(subscores[k] * weights.get(k, 1 / len(PILLARS)) for k in PILLARS)
    return int(round(val))


def radar_chart(subscores: dict):
    labels = PILLARS
    stats = [subscores[l] for l in labels]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    stats += stats[:1]
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, stats, color="#2e7d32", linewidth=2)
    ax.fill(angles, stats, color="#66bb6a", alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"])
    ax.set_ylim(0, 100)
    st.pyplot(fig)


def recommendations(subscores: dict) -> list:
    items = []
    if subscores["Water Stewardship"] < 60:
        items.append({"title": "Adopt drip irrigation", "impact": "+15 water", "cost": "₹₹", "lift": "+8–12"})
        items.append({"title": "Rainwater harvesting pits", "impact": "+10 water", "cost": "₹₹", "lift": "+6–10"})
    if subscores["Nutrient Efficiency"] < 60:
        items.append({"title": "Soil testing before sowing", "impact": "+10 nutrient", "cost": "₹", "lift": "+6–8"})
        items.append({"title": "Balanced NPK application", "impact": "+8 nutrient", "cost": "₹₹", "lift": "+4–6"})
    if subscores["Emissions"] < 60:
        items.append({"title": "Switch to solar pump", "impact": "+10 emissions", "cost": "₹₹₹", "lift": "+6–10"})
        items.append({"title": "Avoid residue burning", "impact": "+20 emissions", "cost": "₹", "lift": "+10–15"})
    if subscores["Soil Health"] < 60:
        items.append({"title": "Add vermicompost/green manure", "impact": "+12 soil", "cost": "₹₹", "lift": "+6–10"})
        items.append({"title": "Mulching to retain moisture", "impact": "+8 soil", "cost": "₹", "lift": "+4–6"})
    if subscores["Biodiversity"] < 60:
        items.append({"title": "Intercropping or border trees", "impact": "+10 biodiversity", "cost": "₹₹", "lift": "+5–8"})
    if subscores["Waste Management"] < 60:
        items.append({"title": "Compost organic waste", "impact": "+12 waste", "cost": "₹", "lift": "+6–9"})
    if subscores["Social"] < 60:
        items.append({"title": "Farmer training participation", "impact": "+10 social", "cost": "₹", "lift": "+6–8"})
    return items[:5]


def badges(score: int, subscores: dict) -> list:
    b = []
    if subscores["Water Stewardship"] >= 75:
        b.append("💧 Water Saver")
    if subscores["Soil Health"] >= 75:
        b.append("🌱 Soil Steward")
    if not subscores["Emissions"] < 70 and not subscores["Emissions"] < subscores["Nutrient Efficiency"]:
        b.append("🌍 Climate Conscious")
    if score >= 80:
        b.append("✅ Eco Champion")
    return b


def load_farm_context() -> dict:
    ctx = {"state": "Telangana", "district": "Hyderabad", "area": 1.0}
    try:
        df = pd.read_csv("farm_data.csv")
        if not df.empty:
            row = df.iloc[0].to_dict()
            ctx["state"] = str(row.get("state", ctx["state"]))
            ctx["district"] = str(row.get("district", ctx["district"]))
            ctx["area"] = float(row.get("area", ctx["area"]))
    except Exception:
        pass
    return ctx


def show_sustainability(db_fire=None, db_mongo=None):
    st.header("🌿 Sustainability Score")
    st.caption("Measure, simulate, and improve your farm’s sustainability with guided actions.")

    ctx = load_farm_context()

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Farm Inputs")
        crop = st.selectbox("Primary crop", ["Wheat", "Rice", "Maize", "Vegetables", "Cotton"], index=3)
        irrigation = st.selectbox("Irrigation type", ["Flood", "Drip", "Sprinkler"], index=0)
        state = st.text_input("State", value=ctx["state"])

        st.markdown("**Practices and usage**")
        organic_matter = st.slider("Estimated organic matter %", 0.5, 5.0, 1.5, 0.1)
        urea_kg = st.slider("Urea usage (kg/acre)", 0, 120, 50, 5)
        diesel = st.slider("Diesel used this season (liters)", 0, 200, 10, 5)
        water_use_index = st.slider("Water use index (lower is better)", 1, 20, 10)
        soil_test = st.checkbox("Recent soil test done", value=False)
        balanced_npk = st.checkbox("Using balanced NPK", value=False)
        crop_rotation = st.checkbox("Crop rotation practiced", value=True)
        intercropping = st.checkbox("Intercropping/cover crops", value=False)
        border_trees = st.checkbox("Border trees/hedgerows", value=False)
        flower_strips = st.checkbox("Flower strips for pollinators", value=False)
        mulch = st.checkbox("Mulching in field", value=True)
        rainwater_harvest = st.checkbox("Rainwater harvesting pits/tanks", value=False)
        solar_pump = st.checkbox("Solar pump installed", value=False)
        residue_burning = st.checkbox("Residue burning practiced", value=False)
        plastic_mulch = st.checkbox("Plastic mulch used", value=False)
        compost_fraction = st.slider("Fraction of organic waste composted", 0.0, 1.0, 0.3, 0.05)
        bio_pesticides = st.checkbox("Using bio-pesticides/biocontrols", value=False)
        farmer_training = st.checkbox("Participated in training/extension", value=False)
        women_participation = st.checkbox("Women involvement in decision-making", value=False)
        community_sharing = st.checkbox("Sharing knowledge/tools in community", value=False)

        inputs = {
            "organic_matter": organic_matter,
            "urea_kg_per_acre": urea_kg,
            "diesel_liters": diesel,
            "water_use_index": water_use_index,
            "soil_test": soil_test,
            "balanced_npk": balanced_npk,
            "crop_rotation": crop_rotation,
            "intercropping": intercropping,
            "border_trees": border_trees,
            "flower_strips": flower_strips,
            "mulching": mulch,
            "irrigation": irrigation.lower(),
            "rainwater_harvest": rainwater_harvest,
            "solar_pump": solar_pump,
            "residue_burning": residue_burning,
            "plastic_mulch": plastic_mulch,
            "compost_fraction": compost_fraction,
            "bio_pesticides": bio_pesticides,
            "farmer_training": farmer_training,
            "women_participation": women_participation,
            "community_sharing": community_sharing,
        }

        subscores = compute_subscores(inputs)
        weights = dynamic_weights(crop, irrigation, state)
        score = overall_score(subscores, weights)

        st.metric("Overall Sustainability Score", f"{score}/100")
        st.progress(score / 100)

        st.markdown("**Sub‑scores by pillar**")
        cols = st.columns(3)
        for i, pillar in enumerate(PILLARS):
            with cols[i % 3]:
                st.metric(pillar, f"{subscores[pillar]}")

        st.markdown("---")
        st.subheader("What‑if Simulator")
        sim_drip = st.checkbox("Simulate switching to drip irrigation", value=False)
        sim_mulch = st.checkbox("Simulate adding mulching", value=False)
        sim_reduce_urea = st.checkbox("Simulate reducing urea by 25%", value=False)

        sim_inputs = inputs.copy()
        if sim_drip:
            sim_inputs["irrigation"] = "drip"
        if sim_mulch:
            sim_inputs["mulching"] = True
        if sim_reduce_urea:
            sim_inputs["urea_kg_per_acre"] = int(inputs["urea_kg_per_acre"] * 0.75)

        sim_subscores = compute_subscores(sim_inputs)
        sim_score = overall_score(sim_subscores, weights)
        st.write(f"Projected score with selected actions: **{sim_score}/100** (current {score}/100)")

    with right:
        st.subheader("Pillar Radar")
        radar_chart(subscores)

        st.subheader("Top Recommendations")
        recs = recommendations(subscores)
        for r in recs:
            st.markdown(f"• **{r['title']}** — impact {r['impact']}, cost {r['cost']} — expected lift {r['lift']}")

        st.subheader("Badges")
        for b in badges(score, subscores):
            st.success(b)

        st.subheader("Export & Share")
        report = {
            "when": datetime.utcnow().isoformat(),
            "context": {"crop": crop, "irrigation": irrigation, "state": state, **ctx},
            "weights": weights,
            "subscores": subscores,
            "score": score,
            "simulated_subscores": sim_subscores,
            "simulated_score": sim_score,
            "recommendations": recs,
        }
        st.download_button(
            "⬇️ Download scorecard (JSON)",
            data=json.dumps(report, indent=2),
            file_name="ecofarmx_sustainability_scorecard.json",
            mime="application/json",
            use_container_width=True,
        )

        phone = st.text_input("SMS this report to phone (optional)")
        if st.button("📲 Send SMS summary", type="secondary") and phone:
            summary = f"EcoFarmX Sustainability: {score}/100. Top rec: {recs[0]['title'] if recs else 'Keep it up!'}."
            ok = sms_service.send_help_alert("Sustainability", phone, summary)
            if ok:
                st.success("SMS sent (or previewed in demo mode)")
            else:
                st.info("SMS not sent; check Twilio credentials or phone number.")

    st.markdown("---")
    if st.button("💾 Save Score"):
        payload = {
            "context": {"crop": crop, "irrigation": irrigation, "state": state, **ctx},
            "inputs": inputs,
            "weights": weights,
            "subscores": subscores,
            "score": score,
            "sim": {"inputs": sim_inputs, "subscores": sim_subscores, "score": sim_score},
            "recommendations": recs,
        }
        try:
            firebase_service.save_sustainability_score(db_fire, payload)
        except Exception:
            st.info("Saved to Firebase in demo mode.")
        try:
            mongo_service.save_sustainability_score(db_mongo, payload)
        except Exception:
            st.info("Saved to MongoDB in demo mode.")
        st.success("Score saved!")