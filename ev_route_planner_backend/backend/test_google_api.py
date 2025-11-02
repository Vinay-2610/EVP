import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not GOOGLE_MAPS_API_KEY:
    print("❌ Google Maps API key not found in .env file!")
    exit()

# Sample test: get directions from Hyderabad → Bangalore
url = (
    f"https://maps.googleapis.com/maps/api/directions/json?"
    f"origin=Hyderabad&destination=Bangalore&key={GOOGLE_MAPS_API_KEY}"
)

response = requests.get(url)
data = response.json()

if data["status"] == "OK":
    print("✅ Google Maps API key is working correctly!")
    route = data["routes"][0]["legs"][0]
    print(f"Distance: {route['distance']['text']}")
    print(f"Duration: {route['duration']['text']}")
else:
    print("❌ Something went wrong.")
    print("Error message:", data.get("error_message"))
