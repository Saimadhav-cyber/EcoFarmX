# components/marketplace.py
import math
import streamlit as st
from typing import Optional, Tuple

from data.demo_data import get_marketplace_items, get_demo_farmers
from utils import mongo_service, firebase_service
from components import maps as maps_comp


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _categorize(product_name: str) -> str:
    p = product_name.lower()
    if any(k in p for k in ["tomato", "onion", "potato", "chili", "leaf", "greens"]):
        return "Vegetables"
    if any(k in p for k in ["mango", "banana", "apple", "grape", "fruit", "berry"]):
        return "Fruits"
    if any(k in p for k in ["wheat", "rice", "maize", "corn", "millet", "grain"]):
        return "Grains"
    if any(k in p for k in ["milk", "curd", "paneer", "ghee", "butter", "dairy"]):
        return "Dairy"
    if any(k in p for k in ["dal", "pulses", "lentil", "chickpea"]):
        return "Pulses"
    # fallback for items like honey
    return "Dairy" if "honey" in p else "Fruits"


def _rating_from_quality(q: str) -> float:
    return 4.8 if q == "Premium" else (4.5 if q == "Grade A" else 4.2)


def _get_user_coords() -> Optional[Tuple[float, float]]:
    user_type = st.session_state.get("user_type", "Viewer (Demo)")
    farmers = get_demo_farmers()
    # Try to match by name snippet in user_type
    for f in farmers:
        if isinstance(user_type, str) and f["name"].split()[0] in user_type:
            if f.get("farm_location"):
                return f["farm_location"]
    return None


def _svg_product_placeholder() -> str:
    return """
<div style="width:100%; border-radius:8px; overflow:hidden;">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250" preserveAspectRatio="xMidYMid meet" width="100%" height="auto">
    <defs>
      <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
        <stop offset="0" stop-color="#e5e7eb"/>
        <stop offset="1" stop-color="#f3f4f6"/>
      </linearGradient>
    </defs>
    <rect width="400" height="250" fill="url(#g)"/>
    <rect x="5" y="5" width="390" height="240" rx="8" fill="none" stroke="#d1d5db"/>
    <text x="200" y="125" dominant-baseline="middle" text-anchor="middle" fill="#6b7280" font-family="Inter, Arial, sans-serif" font-size="26">Product</text>
  </svg>
 </div>
"""


def show_marketplace(fire_db=None, mongo_db=None):
    st.header("🏪 Marketplace")
    tab1, tab2, tab3 = st.tabs(["🌽 Sell Produce", "📦 My Listings", "🔎 Explore"])

    # --- Sell Produce (unchanged demo-friendly persistence) ---
    with tab1:
        st.subheader("Create Listing (Demo only)")
        product = st.text_input("Product Name", "Organic Tomatoes")
        qty = st.number_input("Quantity (kg)", 1, value=10)
        price = st.number_input("Price per kg (₹)", 10, value=40)
        quality = st.selectbox("Quality", ["Premium", "Grade A", "Grade B"])
        if st.button("Add Listing"):
            listing = {
                "product": product,
                "quantity": qty,
                "price_per_kg": price,
                "quality": quality,
                "seller": "Demo User",
            }
            # Persist to Firebase (Firestore)
            try:
                if fire_db is not None:
                    firebase_service.add_marketplace_listing(fire_db, listing)
            except Exception:
                st.info("Marketplace listing stored in Firebase demo mode.")
            # Persist to MongoDB
            try:
                if mongo_db is not None:
                    mongo_service.insert_marketplace_listing(mongo_db, listing)
            except Exception:
                st.info("Marketplace listing stored in MongoDB demo mode.")
            st.success(f"Added {qty}kg of {product} at ₹{price}/kg.")

    # --- My Listings (simple demo placeholder) ---
    with tab2:
        st.subheader("My Listings")
        st.info("No personal listings yet. Add some in the 'Sell Produce' tab.")

    # --- Explore with search, category, smart filter, and Nearby distance ---
    with tab3:
        st.subheader("Explore Available Products")
        items = get_marketplace_items()

        # Build farmer->location map from demo data
        farmer_locations = {f["name"]: f.get("farm_location") for f in get_demo_farmers()}
        farmer_village = {f["name"]: f.get("village") for f in get_demo_farmers()}

        # Controls: search, category, smart filter
        query = st.text_input("Search products or farmer", "").strip().lower()
        category = st.selectbox(
            "Category",
            ["All", "Vegetables", "Fruits", "Grains", "Dairy", "Pulses"],
            index=0,
        )
        smart_filter = st.selectbox(
            "Smart Filter",
            [
                "All",
                "🌿 Organic Certified (All)",
                "🥇 Best Seller",
                "💰 Price Drop",
                "📦 Bulk Deals",
                "🧺 New Arrivals",
                "🕒 Freshly Harvested",
                "📍 Nearby Farms",
            ],
            index=0,
        )

        # Determine user coordinates for Nearby filter
        user_coords = _get_user_coords()
        show_distance_ui = smart_filter == "📍 Nearby Farms"
        max_km = None
        if show_distance_ui:
            if user_coords is None:
                st.warning("No saved location found. Pick your location on the map below to enable Nearby filtering.")
                st.caption("Set your location (click map or type coords):")
                lat, lon = maps_comp.map_select_ui()
                if lat and lon:
                    user_coords = (lat, lon)
                    st.success(f"Using your location: {lat:.4f}, {lon:.4f}")
            if user_coords is not None:
                max_km = st.slider("Max distance (km)", 5, 100, 25)

        # Apply filters
        filtered = []
        for item in items:
            name = item["product"]
            farmer = item["farmer"]
            price_str = item.get("price", "₹0/kg")
            price_per_kg = 0
            try:
                # Expect formats like "₹40/kg"
                price_per_kg = int("".join(ch for ch in price_str if ch.isdigit()))
            except Exception:
                price_per_kg = 0
            quality = item.get("quality", "Grade A")
            qty = item.get("quantity", "0kg")
            try:
                qty_val = int("".join(ch for ch in str(qty) if ch.isdigit()))
            except Exception:
                qty_val = 0

            # Search filter
            if query and (query not in name.lower()) and (query not in farmer.lower()):
                continue

            # Category filter
            cat = _categorize(name)
            if category != "All" and cat != category:
                continue

            # Smart filter logic
            if smart_filter == "🥇 Best Seller" and quality != "Premium":
                continue
            if smart_filter == "💰 Price Drop" and not (price_per_kg and price_per_kg <= 45):
                continue
            if smart_filter == "📦 Bulk Deals" and not (qty_val and qty_val >= 50):
                continue
            # Freshly/New/Organic are permissive; keep all

            # Nearby distance filtering
            distance_km = None
            if smart_filter == "📍 Nearby Farms":
                if user_coords is None:
                    # Cannot evaluate distance; skip
                    continue
                farm_loc = farmer_locations.get(farmer)
                if not farm_loc:
                    # Skip items with unknown location in Nearby mode
                    continue
                distance_km = _haversine_km(user_coords[0], user_coords[1], farm_loc[0], farm_loc[1])
                if max_km is not None and distance_km > max_km:
                    continue

            filtered.append({
                "item": item,
                "category": cat,
                "distance_km": distance_km,
                "rating": _rating_from_quality(quality),
                "price_per_kg": price_per_kg,
                "qty_val": qty_val,
            })

        # Render e-commerce style cards in a responsive grid
        if not filtered:
            st.info("No items match your filters.")
            return

        cols = st.columns(3)
        for i, row in enumerate(filtered):
            col = cols[i % 3]
            with col:
                item = row["item"]
                name = item["product"]
                farmer = item["farmer"]
                price = item.get("price", "₹0/kg")
                quality = item.get("quality", "Grade A")
                qty = item.get("quantity", "0kg")
                village = farmer_village.get(farmer)

                card = st.container(border=True)
                with card:
                    img_src = item.get("image_url")
                    if img_src:
                        st.image(img_src, use_column_width=True)
                    else:
                        st.markdown(_svg_product_placeholder(), unsafe_allow_html=True)
                    st.subheader(name)

                    # Price, rating, badges
                    stars_full = int(math.floor(row["rating"]))
                    stars = "⭐" * stars_full
                    st.markdown(f"**Price:** {price}  |  **Rating:** {stars} {row['rating']:.1f}/5")
                    st.caption("✅ Organic Certified by Govt. of India")

                    # Feature icons
                    icons = []
                    if row["qty_val"] >= 50:
                        icons.append("📦 Bulk Deal")
                    if row["price_per_kg"] and row["price_per_kg"] <= 45:
                        icons.append("💰 Discount")
                    if quality == "Premium":
                        icons.append("🔥 Best Seller")
                    if icons:
                        st.write(" · ".join(icons))

                    # Distance (if computed)
                    if row["distance_km"] is not None:
                        st.write(f"📍 ~{row['distance_km']:.1f} km from you")

                    st.write(f"Farmer: {farmer} | Quality: {quality} | Quantity: {qty}")
                    if st.button("Contact Seller (Open Chat)", key=f"contact_{name}_{i}"):
                        st.session_state["selected_product_context"] = (
                            f"Hi, I’m interested in buying {name} ({price}) from {farmer} "
                            f"at {village or 'their location'}. Can you help me connect?"
                        )
                        st.toast("Sent product info to chat window 💬")
