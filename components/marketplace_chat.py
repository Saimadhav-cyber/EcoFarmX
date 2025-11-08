# components/marketplace_chat.py
import streamlit as st
import streamlit.components.v1 as stc
from components import marketplace
import random
import re

# 🧑‍🌾 VEGETABLE CULTIVATION ANALYSIS DATASET
VEGETABLE_KNOWLEDGE = {
    "soil_types": {
        "alluvial": {
            "name": "🌱 Alluvial Soil",
            "regions": "Indo-Gangetic Plains (Uttar Pradesh, Bihar, West Bengal, Punjab, Haryana)",
            "texture": "Rich in nutrients, good water retention",
            "ph_range": "6.5 – 7.5",
            "vegetables": ["Potato 🥔", "Tomato 🍅", "Brinjal (Eggplant) 🍆", "Cabbage 🥬", "Cauliflower 🌸", "Carrot 🥕"],
            "fertilizers": {
                "basal": "FYM (Farm Yard Manure) – 20 tons/ha",
                "npk": "100:60:60 per hectare",
                "pesticides": "Neem-based bio pesticide for aphids and leaf curl",
                "fungicide": "Mancozeb or Carbendazim (for fungal wilt control)"
            },
            "tips": [
                "Maintain proper drainage as alluvial soil may get waterlogged",
                "Use mulching to retain soil moisture",
                "Crop rotation with legumes improves fertility"
            ]
        },
        "black": {
            "name": "🌾 Black Soil (Regur Soil)",
            "regions": "Maharashtra, Madhya Pradesh, Gujarat, Andhra Pradesh",
            "texture": "Clayey, moisture-retentive, high in iron and lime",
            "ph_range": "6.8 – 8.0",
            "vegetables": ["Onion 🧅", "Garlic 🧄", "Okra (Lady Finger) 🌿", "Chilli 🌶", "Tomato 🍅"],
            "fertilizers": {
                "organic": "15–20 tons FYM per hectare",
                "npk": "90:45:45",
                "micronutrients": "Zinc Sulphate (ZnSO₄) – 25 kg/ha",
                "pesticides": "Imidacloprid for sucking pests"
            },
            "tips": [
                "Avoid over-irrigation — leads to cracking",
                "Deep ploughing before sowing enhances root penetration",
                "Use drip irrigation to manage water efficiently"
            ]
        },
        "red": {
            "name": "🌿 Red Soil",
            "regions": "Tamil Nadu, Karnataka, Odisha, Jharkhand, Chhattisgarh",
            "texture": "Sandy to loamy; low in nitrogen, phosphorus",
            "ph_range": "5.5 – 7.0",
            "vegetables": ["Sweet Potato 🍠", "Groundnut 🥜", "Chilli 🌶", "Onion 🧅", "Beans 🌱"],
            "fertilizers": {
                "fym": "25 tons/ha",
                "npk": "120:60:60",
                "lime": "Apply dolomite/lime to reduce acidity (500 kg/ha)",
                "fungicide": "Copper oxychloride for leaf spot and rust diseases"
            },
            "tips": [
                "Add compost to improve organic matter",
                "Use green manuring (sunhemp) for soil enrichment",
                "Frequent irrigation is required in sandy red soils"
            ]
        },
        "sandy": {
            "name": "🏜 Sandy Soil",
            "regions": "Rajasthan, coastal Andhra, parts of Gujarat",
            "texture": "Light, porous, low nutrient content",
            "ph_range": "6.0 – 7.0",
            "vegetables": ["Watermelon 🍉", "Muskmelon 🍈", "Cucumber 🥒", "Radish 🌿", "Sweet Potato 🍠"],
            "fertilizers": {
                "organic": "25 tons/ha",
                "npk": "80:40:40",
                "pesticides": "Use organic neem oil or pyrethrin-based sprays",
                "micronutrients": "Foliar spray of micronutrient mix (Zn, Fe, Mn)"
            },
            "tips": [
                "Irrigate frequently due to low water-holding capacity",
                "Apply mulching to reduce evaporation losses",
                "Drip irrigation is best suited"
            ]
        },
        "laterite": {
            "name": "🌾 Laterite Soil",
            "regions": "Kerala, Karnataka, West Bengal, Assam",
            "texture": "Porous, low fertility, rich in iron/aluminium",
            "ph_range": "4.5 – 6.0",
            "vegetables": ["Tapioca (Cassava) 🌿", "Cowpea 🌱", "Brinjal 🍆", "Chilli 🌶"],
            "fertilizers": {
                "fym": "30 tons/ha",
                "npk": "100:50:50",
                "lime": "250 kg/ha (to neutralize acidity)",
                "biofertilizer": "Azospirillum or Rhizobium cultures"
            },
            "tips": [
                "Add compost and lime to improve fertility",
                "Apply mulch and organic residue to conserve moisture",
                "Prefer drought-tolerant vegetable varieties"
            ]
        },
        "clay": {
            "name": "🌴 Clay Soil",
            "regions": "Deltaic regions of Tamil Nadu, coastal Andhra, Assam",
            "texture": "Heavy, sticky, high nutrient content",
            "ph_range": "6.5 – 7.5",
            "vegetables": ["Paddy-related vegetables", "Taro (Colocasia) 🌿", "Spinach 🍃", "Tomato 🍅", "Pumpkin 🎃"],
            "fertilizers": {
                "fym": "15–20 tons/ha",
                "npk": "80:40:40",
                "pesticides": "Carbofuran for root grubs",
                "fungicides": "Bordeaux mixture for fungal diseases"
            },
            "tips": [
                "Maintain good drainage",
                "Avoid compaction by ploughing after each crop",
                "Grow cover crops to improve aeration"
            ]
        },
        "mountain": {
            "name": "🌿 Mountain/Loamy Soil",
            "regions": "Himachal Pradesh, Uttarakhand, parts of North-East India",
            "texture": "Loamy, well-drained, rich in humus",
            "ph_range": "6.0 – 7.0",
            "vegetables": ["Peas 🌿", "Cabbage 🥬", "Carrot 🥕", "Beetroot 🌰", "Lettuce 🥗"],
            "fertilizers": {
                "fym": "25 tons/ha",
                "npk": "60:50:40",
                "biofertilizer": "Rhizobium and Azotobacter",
                "fungicide": "Sulphur-based dust for powdery mildew"
            },
            "tips": [
                "Practice contour farming to prevent erosion",
                "Use mulching to retain moisture",
                "Maintain proper spacing to prevent fungal attacks"
            ]
        },
        "saline": {
            "name": "🌍 Saline/Alkaline Soil",
            "regions": "Arid regions of Rajasthan, Haryana, Gujarat",
            "texture": "Variable; high in sodium and calcium salts",
            "ph_range": "8.0 – 9.5",
            "vegetables": ["Beetroot 🌰", "Spinach 🍃", "Barley-based vegetables", "Mustard greens 🌿"],
            "fertilizers": {
                "gypsum": "5 tons/ha",
                "fym": "25 tons/ha",
                "npk": "60:40:20",
                "biofertilizer": "Salt-tolerant bacterial strains"
            },
            "tips": [
                "Apply gypsum to neutralize salinity",
                "Prefer raised beds for sowing",
                "Regular flushing with freshwater reduces salt accumulation"
            ]
        }
    },
    "general_tips": [
        "💧 Use drip irrigation for efficiency",
        "🌿 Use mulching or pre-emergent herbicides for weed control",
        "🌱 Add compost, green manure, vermicompost for organic boost",
        "🐛 Integrated Pest Management (IPM) preferred for pest control",
        "🔄 Rotate crops with legumes to restore nitrogen",
        "🧪 Perform soil testing once a year before sowing"
    ]
}

def get_soil_recommendation(soil_type):
    """Get comprehensive soil recommendations"""
    soil_data = VEGETABLE_KNOWLEDGE["soil_types"].get(soil_type.lower())
    if not soil_data:
        return "I don't have information about that soil type. Please try: alluvial, black, red, sandy, laterite, clay, mountain, or saline."
    
    response = f"""
{soil_data['name']}
📍 **Regions:** {soil_data['regions']}
🌱 **Texture:** {soil_data['texture']}
🧪 **pH Range:** {soil_data['ph_range']}

🥬 **Suitable Vegetables:**
{chr(10).join(['• ' + veg for veg in soil_data['vegetables']])}

🌿 **Fertilizers & Chemicals:**
{chr(10).join(['• ' + key.replace('_', ' ').title() + ': ' + value for key, value in soil_data['fertilizers'].items()])}

💡 **Cultivation Tips:**
{chr(10).join(['• ' + tip for tip in soil_data['tips']])}
    """
    return response.strip()

def get_vegetable_recommendation(vegetable_name):
    """Find which soil types are suitable for a specific vegetable"""
    suitable_soils = []
    for soil_type, data in VEGETABLE_KNOWLEDGE["soil_types"].items():
        if any(vegetable_name.lower() in veg.lower() for veg in data["vegetables"]):
            suitable_soils.append({
                "soil": data["name"],
                "regions": data["regions"],
                "ph_range": data["ph_range"]
            })
    
    if not suitable_soils:
        return f"I don't have specific recommendations for {vegetable_name}. Try asking about common vegetables like potato, tomato, onion, etc."
    
    response = f"🥬 **{vegetable_name.title()}** can be grown in:\n\n"
    for soil in suitable_soils:
        response += f"• **{soil['soil']}**\n"
        response += f"  📍 Regions: {soil['regions']}\n"
        response += f"  🧪 pH Range: {soil['ph_range']}\n\n"
    
    return response.strip()

def get_fertilizer_recommendation(soil_type, vegetable=None):
    """Get specific fertilizer recommendations"""
    soil_data = VEGETABLE_KNOWLEDGE["soil_types"].get(soil_type.lower())
    if not soil_data:
        return "I don't have information about that soil type."
    
    response = f"🌿 **Fertilizer Recommendations for {soil_data['name']}**\n\n"
    
    if vegetable:
        response += f"🥬 **For {vegetable.title()}:**\n"
    
    response += f"🌱 **Organic Matter:** {soil_data['fertilizers'].get('fym', soil_data['fertilizers'].get('organic', 'N/A'))}\n"
    response += f"⚗️ **NPK Ratio:** {soil_data['fertilizers'].get('npk', 'N/A')}\n"
    
    # Add specific nutrients if available
    for key, value in soil_data['fertilizers'].items():
        if key not in ['fym', 'organic', 'npk']:
            response += f"🧪 **{key.replace('_', ' ').title()}:** {value}\n"
    
    return response.strip()

def chatbot_response(user_message):
    """Main chatbot function to process user messages"""
    user_message = user_message.lower().strip()
    
    # Greetings
    greetings = ["hello", "hi", "hey", "namaste", "नमस्ते"]
    if any(greet in user_message for greet in greetings):
        return """🌱 **Welcome to EcoFarmX AI Assistant!**

I'm here to help you with:
• 🧪 Soil analysis and recommendations
• 🥬 Vegetable cultivation guidance  
• 🌿 Fertilizer and pesticide advice
• 📍 Regional farming tips
• 🌾 General agricultural best practices

**Try asking me:**
• "What vegetables grow well in black soil?"
• "Tell me about tomato cultivation"
• "What fertilizers for red soil?"
• "Best vegetables for sandy soil"
• "General farming tips"""
    
    # Soil type queries
    soil_keywords = ["alluvial", "black", "red", "sandy", "laterite", "clay", "mountain", "saline", "alkaline"]
    for soil in soil_keywords:
        if soil in user_message:
            if "fertilizer" in user_message or "manure" in user_message or "npk" in user_message:
                # Extract vegetable name if mentioned
                vegetable_match = re.search(r'for\s+(\w+)', user_message)
                vegetable = vegetable_match.group(1) if vegetable_match else None
                return get_fertilizer_recommendation(soil, vegetable)
            else:
                return get_soil_recommendation(soil)
    
    # Vegetable queries
    vegetable_keywords = ["potato", "tomato", "onion", "garlic", "brinjal", "eggplant", "cabbage", "cauliflower", 
                         "carrot", "sweet potato", "chilli", "pepper", "okra", "lady finger", "spinach", 
                         "cucumber", "watermelon", "muskmelon", "radish", "beans", "peas", "lettuce", 
                         "beetroot", "pumpkin", "tapioca", "cassava", "cowpea", "groundnut", "mustard"]
    
    for veg in vegetable_keywords:
        if veg in user_message:
            return get_vegetable_recommendation(veg)
    
    # General tips
    if any(word in user_message for word in ["tip", "advice", "suggestion", "recommendation", "best practice"]):
        tips = random.sample(VEGETABLE_KNOWLEDGE["general_tips"], 3)
        return "🌾 **General Farming Tips:**\n\n" + "\n".join([f"• {tip}" for tip in tips])
    
    # Irrigation queries
    if "irrigation" in user_message or "water" in user_message:
        return """💧 **Irrigation Guidelines:**

• **Drip irrigation** is most efficient for vegetables
• **Frequency:** Sandy soils need more frequent watering than clay soils
• **Timing:** Early morning or late evening to reduce evaporation
• **Amount:** Generally 2-3 cm per week for most vegetables
• **Method:** Drip irrigation saves 30-50% water compared to flood irrigation

**Soil-specific irrigation:**
• Sandy soil: Frequent, light irrigation
• Clay soil: Less frequent, deep irrigation
• Black soil: Avoid over-irrigation to prevent cracking"""
    
    # Pest management
    if "pest" in user_message or "insect" in user_message or "disease" in user_message:
        return """🐛 **Integrated Pest Management (IPM):**

**Preventive Measures:**
• Crop rotation to break pest cycles
• Use resistant varieties
• Maintain proper plant spacing
• Remove infected plants immediately

**Organic Solutions:**
• Neem oil spray for aphids and mites
• Garlic-chili spray for caterpillars
• Trichoderma for soil-borne diseases
• Beneficial insects like ladybugs

**Chemical Options (when necessary):**
• Imidacloprid for sucking pests
• Mancozeb for fungal diseases
• Always follow recommended dosage and safety precautions"""
    
    # Default response
    return """🤔 I'm not sure about that specific question.

**I can help you with:**
• 🧪 Soil analysis (alluvial, black, red, sandy, laterite, clay, mountain, saline)
• 🥬 Vegetable cultivation guidance
• 🌿 Fertilizer and pesticide recommendations  
• 💧 Irrigation advice
• 🐛 Pest management
• 🌾 General farming best practices

**Try asking:**
• "What grows well in red soil?"
• "Tell me about potato farming"
• "Fertilizers for black soil"
• "Irrigation tips for sandy soil"
• "General farming tips" """


def show_marketplace_chat(fire_db=None, mongo_db=None):
    """Builds the full Marketplace + Chat UI in one page."""
    # Use subheader so the global app title remains the single main heading
    st.subheader("🛍️ Marketplace + AI Assistant")
    st.caption("Browse organic products and get AI-powered farming advice in one view.")

    left, right = st.columns([3, 2])

    # LEFT: Marketplace — render the full feature set
    with left:
        marketplace.show_marketplace(fire_db, mongo_db)

    # RIGHT: AI Chat Assistant
    with right:
        st.subheader("🤖 EcoFarmX AI Assistant")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Product context from marketplace
        context_msg = st.session_state.get("selected_product_context")
        if context_msg:
            st.success(context_msg)
            # Add context to chat if not already added
            if not any(msg.get("context") == context_msg for msg in st.session_state.messages):
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"I see you're interested in: {context_msg}",
                    "context": context_msg
                })
        
        # Quick action buttons for common queries
        st.caption("💡 Quick Questions:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧪 Soil Help", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Tell me about different soil types"})
                st.session_state.messages.append({"role": "assistant", "content": get_soil_recommendation("alluvial")})
        with col2:
            if st.button("🥬 Vegetables", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What vegetables should I grow?"})
                st.session_state.messages.append({"role": "assistant", "content": "I can help you choose vegetables based on your soil type. Try asking 'What grows well in black soil?' or 'Best vegetables for red soil?'"})
        with col3:
            if st.button("💧 Irrigation", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Irrigation tips"})
                st.session_state.messages.append({"role": "assistant", "content": """💧 **Irrigation Guidelines:**

• **Drip irrigation** is most efficient for vegetables
• **Frequency:** Sandy soils need more frequent watering than clay soils
• **Timing:** Early morning or late evening to reduce evaporation
• **Amount:** Generally 2-3 cm per week for most vegetables
• **Method:** Drip irrigation saves 30-50% water compared to flood irrigation"""})
        
        # Chat interface
        st.markdown("---")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about soil, vegetables, fertilizers, irrigation..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get AI response
            response = chatbot_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to show new messages
            st.rerun()
        
        # Clear chat button
        if st.session_state.messages and st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        # Help text
        with st.expander("📖 How to use AI Assistant"):
            st.markdown("""
            **Ask me about:**
            • 🧪 Soil types and recommendations
            • 🥬 Vegetable cultivation guidance  
            • 🌿 Fertilizers and pesticides
            • 💧 Irrigation and water management
            • 🐛 Pest and disease control
            • 📍 Regional farming advice
            
            **Example questions:**
            • "What grows well in black soil?"
            • "Tell me about tomato farming"
            • "Fertilizers for red soil"
            • "Irrigation tips for sandy soil"
            • "How to control pests organically?"
            """)