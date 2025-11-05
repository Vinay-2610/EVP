# main.py
import os
import math
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from a_star_real_routes import run_a_star_with_google
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------
# Load environment variables (Google Maps + Supabase)
# --------------------------------------------------
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --------------------------------------------------
# Supabase Connection (lazy initialization)
# --------------------------------------------------
supabase = None

def get_supabase():
    global supabase
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise HTTPException(status_code=500, detail="Supabase credentials not configured")
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Supabase: {str(e)}")
    return supabase

# --------------------------------------------------
# FastAPI Setup
# --------------------------------------------------
app = FastAPI(title="EV Route Planner Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Pydantic Models
# --------------------------------------------------
class TripInput(BaseModel):
    user_id: str = "guest_user"
    from_location: str
    to_location: str
    battery_percent: float

class PredictionInput(BaseModel):
    from_location: str
    to_location: str
    ev_model_id: Optional[int] = None
    ev_model_name: Optional[str] = None
    battery_percent: float  # required for your user flow

# --------------------------------------------------
# Helper: route distance/duration via Directions API
# --------------------------------------------------
def get_route_data(from_loc: str, to_loc: str):
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={from_loc}&destination={to_loc}&key={GOOGLE_MAPS_API_KEY}"
    )
    resp = requests.get(url)
    data = resp.json()
    if data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Google Maps error: {data.get('status')}")
    route = data["routes"][0]["legs"][0]
    distance_km = route["distance"]["value"] / 1000.0
    duration_min = route["duration"]["value"] / 60.0
    return distance_km, duration_min

# --------------------------------------------------
# Fetch EV model from Supabase (by id or name)
# --------------------------------------------------
def get_ev_model(ev_model_id: Optional[int], ev_model_name: Optional[str]) -> Optional[Dict[str, Any]]:
    q = get_supabase().table("ev_models").select("*")
    if ev_model_id:
        q = q.eq("ev_model_id", ev_model_id)
    elif ev_model_name:
        q = q.ilike("model_name", f"%{ev_model_name.strip()}%")
    resp = q.limit(1).execute()
    if resp.data and len(resp.data) > 0:
        return resp.data[0]
    return None

# --------------------------------------------------
# Compute available range (km) from model + battery%
# Model fields supported: max_range (km) OR battery_capacity (kWh) + avg_consumption (kWh/km)
# --------------------------------------------------
def compute_range_from_model(model: Optional[Dict[str, Any]], battery_percent: float) -> Optional[float]:
    if not model:
        return None
    max_range = model.get("max_range")
    avg_consumption = model.get("avg_consumption")  # kWh per km
    battery_capacity = model.get("battery_capacity")  # kWh
    if max_range:
        base_range = float(max_range)
    elif battery_capacity and avg_consumption:
        base_range = float(battery_capacity) / float(avg_consumption)
    else:
        return None
    # clamp battery_percent
    pct = max(0.0, min(100.0, float(battery_percent)))
    return base_range * (pct / 100.0)

# --------------------------------------------------
# Places Nearby helper (Google Places Nearby Search) - with small debugging
# --------------------------------------------------
def places_nearby(lat: float, lng: float, radius: int = 12000, api_key: str = None) -> List[Dict[str, Any]]:
    """
    Searches for 'charging station' near the provided lat,lng.
    Default radius increased to 12km to improve catch-rate along highways; tune as needed.
    """
    if api_key is None:
        api_key = GOOGLE_MAPS_API_KEY
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}&keyword=charging%20station&key={api_key}"
    )
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        print("Places API request error:", str(e))
        return []
    status = data.get("status")
    print(f"Places API near ({lat:.6f},{lng:.6f}) radius={radius} => status={status}")
    if status not in ("OK", "ZERO_RESULTS"):
        # log for debugging
        print("Places API error_message:", data.get("error_message"))
        return []
    results = []
    for r in data.get("results", []):
        loc = r.get("geometry", {}).get("location", {})
        results.append({
            "name": r.get("name"),
            "address": r.get("vicinity") or r.get("formatted_address"),
            "rating": r.get("rating"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "place_id": r.get("place_id")
        })
    return results

# --------------------------------------------------
# Sample route points (every ~sample_km) to search nearby places along route
# Handles tuples or lists.
# --------------------------------------------------
def sample_route_points(path: List[List[float]], sample_km: int = 60) -> List[List[float]]:
    def haversine(a, b):
        R = 6371.0
        lat1, lon1 = a; lat2, lon2 = b
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return R * (2 * math.atan2(math.sqrt(x), math.sqrt(1-x)))

    samples: List[List[float]] = []
    if not path:
        return samples

    accumulated = 0.0
    # ensure consistent tuple/list form
    def norm(pt):
        return [float(pt[0]), float(pt[1])]

    samples.append(norm(path[0]))
    for i in range(len(path)-1):
        a = norm(path[i])
        b = norm(path[i+1])
        d = haversine((a[0], a[1]), (b[0], b[1]))
        accumulated += d
        if accumulated >= sample_km:
            samples.append(b)
            accumulated = 0.0
    if norm(path[-1]) not in samples:
        samples.append(norm(path[-1]))
    return samples

# --------------------------------------------------
# Startup Event
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting EV Route Planner Backend...")
    print(f"✅ Google Maps API Key: {'Set' if GOOGLE_MAPS_API_KEY else '❌ Missing'}")
    print(f"✅ Supabase URL: {'Set' if SUPABASE_URL else '❌ Missing'}")
    print(f"✅ Supabase Key: {'Set' if SUPABASE_KEY else '❌ Missing'}")
    
    # Test Supabase connection
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            get_supabase()
            print("✅ Supabase connection successful")
        except Exception as e:
            print(f"⚠️  Supabase connection warning: {str(e)}")

# --------------------------------------------------
# Root
# --------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "EV Route Planner Backend running ⚡",
        "status": "healthy",
        "config": {
            "google_maps_api": "configured" if GOOGLE_MAPS_API_KEY else "missing",
            "supabase": "configured" if (SUPABASE_URL and SUPABASE_KEY) else "missing"
        }
    }

# --------------------------------------------------
# POST /trip - unchanged
# --------------------------------------------------
@app.post("/trip")
def create_trip(trip: TripInput):
    distance_km, duration_min = get_route_data(trip.from_location, trip.to_location)
    battery_efficiency = 1.2
    est_battery_usage = distance_km / battery_efficiency
    battery_end = max(trip.battery_percent - (est_battery_usage / 100 * trip.battery_percent), 0)
    response = get_supabase().table("trips").insert({
        "user_id": trip.user_id,
        "source": trip.from_location,
        "destination": trip.to_location,
        "distance": distance_km,
        "duration": duration_min,
        "battery_start": trip.battery_percent,
        "battery_end": battery_end,
        "energy_used": est_battery_usage,
        "timestamp": "now()",
        "route_taken": f"{trip.from_location} → {trip.to_location}",
        "ev_model_id": 1
    }).execute()
    if response.data:
        return {
            "status": "success",
            "trip_id": response.data[0].get("trip_id", "N/A"),
            "distance_km": distance_km,
            "duration_min": duration_min,
            "battery_end": battery_end,
            "energy_used": est_battery_usage
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to save trip data.")

# --------------------------------------------------
# GET /trips
# --------------------------------------------------
@app.get("/trips")
def get_trips(user_id: Optional[str] = None):
    q = get_supabase().table("trips").select("*")
    if user_id:
        q = q.eq("user_id", user_id)
    resp = q.execute()
    return {"trips": resp.data}

# --------------------------------------------------
# GET /nearest-charging-stations
# --------------------------------------------------
@app.get("/nearest-charging-stations")
def get_nearest_charging_stations(lat: float, lng: float, radius: int = 5000):
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={lat},{lng}&radius={radius}&keyword=EV%20charging%20station&key={GOOGLE_MAPS_API_KEY}"
    )
    resp = requests.get(url)
    data = resp.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(status_code=400, detail=f"Google Places API error: {data.get('status')}")
    stations = [
        {
            "name": p.get("name", "Unknown"),
            "address": p.get("vicinity", "N/A"),
            "rating": p.get("rating", "N/A"),
            "lat": p["geometry"]["location"]["lat"],
            "lng": p["geometry"]["location"]["lng"]
        } for p in data.get("results", [])
    ]
    return {"count": len(stations), "radius_used_meters": radius, "stations": stations[:5]}

# --------------------------------------------------
# GET /ev-models — list models for frontend dropdown
# --------------------------------------------------
@app.get("/ev-models")
def list_ev_models():
    try:
        # use desc=False to indicate ascending order (client supports this signature)
        resp = get_supabase().table("ev_models").select("*").order("model_name", desc=False).execute()
        return {"models": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EV models: {str(e)}")

# --------------------------------------------------
# POST /predict-route — main endpoint (model + A* + chargers)
# --------------------------------------------------
@app.post("/predict-route")
def predict_route(input: PredictionInput):
    try:
        # 1) Lookup EV model
        model = get_ev_model(input.ev_model_id, input.ev_model_name)
        if not model:
            raise HTTPException(status_code=400, detail=f"EV model not found")

        # 2) Compute user available range in km
        estimated_range_km = compute_range_from_model(model, input.battery_percent)
        if estimated_range_km is None:
            raise HTTPException(status_code=400, detail="Unable to compute range from model data")

        print(f"Running A* for {input.from_location} -> {input.to_location} with range {estimated_range_km:.2f} km")
        result = run_a_star_with_google(input.from_location, input.to_location, estimated_range_km, GOOGLE_MAPS_API_KEY)

        path = result.get("path", [])
        total_distance_km = result.get("total_distance_km", 0.0)

        # 3) If we have a path, sample and find charging stations along the way
        charging_stations: List[Dict[str, Any]] = []
        if path:
            sampled_points = sample_route_points(path, sample_km=40)  # more frequent sampling
            seen_place_ids = set()
            for pt in sampled_points:
                lat, lng = float(pt[0]), float(pt[1])
                places = places_nearby(lat, lng, radius=12000, api_key=GOOGLE_MAPS_API_KEY)
                for p in places:
                    pid = p.get("place_id")
                    if pid and pid not in seen_place_ids:
                        charging_stations.append(p)
                        seen_place_ids.add(pid)
            charging_info = {
                "message": None if charging_stations else "No charging stations found",
                "count": len(charging_stations),
                "stations": charging_stations
            }
        else:
            charging_info = {"message": "No route path available", "count": 0, "stations": []}

        return {
            "status": result.get("status", "failed"),
            "path": path,
            "total_distance_km": round(total_distance_km, 2),
            "estimated_range_km": round(estimated_range_km, 2),
            "message": result.get("message", ""),
            "charging_suggestions": charging_info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
