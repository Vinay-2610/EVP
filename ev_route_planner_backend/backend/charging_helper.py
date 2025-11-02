import requests
import math
from dotenv import load_dotenv
import os

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# ------------------------------
# Helper: Haversine distance
# ------------------------------
def haversine(coord1, coord2):
    R = 6371
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


# ------------------------------
# Get mid-point of route
# ------------------------------
def get_midpoint(path_coords):
    if not path_coords:
        return None
    mid_index = len(path_coords) // 2
    return path_coords[mid_index]


# ------------------------------
# Find nearest charging stations
# ------------------------------
def find_nearby_chargers(lat, lng, radius=5000):
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={lat},{lng}&radius={radius}&keyword=EV%20charging%20station"
        f"&key={GOOGLE_API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return {"error": f"Google Places API error: {data['status']}"}

    stations = []
    for place in data["results"][:5]:
        stations.append({
            "name": place.get("name", "Unknown"),
            "address": place.get("vicinity", "N/A"),
            "rating": place.get("rating", "N/A"),
            "lat": place["geometry"]["location"]["lat"],
            "lng": place["geometry"]["location"]["lng"]
        })

    return {"count": len(stations), "stations": stations}
