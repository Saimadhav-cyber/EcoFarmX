# data/demo_data.py
def get_demo_farmers():
    return [
        {
            "name": "Ramesh Kumar",
            "village": "Mohanpur",
            "district": "Hyderabad",
            "language": "Telugu",
            "sustainability_score": 85,
            # sample farm location (lat, lon)
            "farm_location": (17.3850, 78.4867),
            "practices": ["Organic Farming", "Solar Pump"],
            "phone": "+91 98765 43210"
        },
        {
            "name": "Laxmi Devi",
            "village": "Chandapur",
            "district": "Hyderabad",
            "language": "Hindi",
            "sustainability_score": 72,
            "farm_location": None,
            "practices": ["Vermicompost", "Rainwater Harvesting"],
            "phone": "+91 98765 43211"
        }
    ]

def get_demo_volunteers():
    return [
        {
            "name": "Priya Sharma",
            "district": "Hyderabad",
            "languages": ["Telugu", "Hindi", "English"],
            "phone": "+91 98765 43212",
            "availability": "Online",
            "location": (17.3850, 78.4867)  # lat, lon
        },
        {
            "name": "Amit Patel",
            "district": "Mumbai",
            "languages": ["Hindi", "English"],
            "phone": "+91 98765 43213",
            "availability": "Online",
            "location": (19.0760, 72.8777)  # lat, lon
        },
        {
            "name": "Suresh Reddy",
            "district": "Hyderabad",
            "languages": ["Telugu", "English"],
            "phone": "+91 98765 43214",
            "availability": "Offline",
            "location": (17.3850, 78.4867)  # lat, lon
        }
    ]

def get_marketplace_items():
    return [
        {"product": "Organic Tomatoes", "farmer": "Ramesh Kumar", "price": "₹40/kg", "quality": "Premium", "quantity": "100kg"},
        {"product": "Pure Honey", "farmer": "Laxmi Devi", "price": "₹500/kg", "quality": "Grade A", "quantity": "20kg"}
    ]
