from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client
from typing import Optional

# -------------------------------
# Supabase connection
# -------------------------------
SUPABASE_URL = "https://zygdfixfuvujnccyhgab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp5Z2RmaXhmdXZ1am5jY3loZ2FiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDc4MTA2NiwiZXhwIjoyMDc2MzU3MDY2fQ.cFxHQ2yRb3pYD3s0S_FSRKWxvCVVd8e6R-mWrnnkukY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# FastAPI app setup
# -------------------------------
app = FastAPI(title="EV Route Planner Backend")

# -------------------------------
# Request body model
# -------------------------------
class TripInput(BaseModel):
    user_id: str = "guest_user"  # Default until Auth added
    from_location: str
    to_location: str
    battery_percent: float

# -------------------------------
# Root test route
# -------------------------------
@app.get("/")
def home():
    return {"message": "EV Route Planner Backend running ⚡"}

# -------------------------------
# Trip creation route
# -------------------------------
@app.post("/trip")
def create_trip(trip: TripInput):
    # --- Dummy values for now (to be replaced later) ---
    distance_km = 120            # Example: will come from route API
    duration_min = 90            # Example: travel time in minutes
    battery_efficiency = 1.2     # km per 1% battery
    est_battery_usage = distance_km / battery_efficiency
    battery_end = max(trip.battery_percent - (est_battery_usage / 100 * trip.battery_percent), 0)

    # --- Insert into Supabase ---
    response = supabase.table("trips").insert({
        "user_id": trip.user_id,
        "source": trip.from_location,
        "destination": trip.to_location,
        "distance": distance_km,
        "duration": duration_min,
        "battery_start": trip.battery_percent,
        "battery_end": battery_end,
        "energy_used": est_battery_usage,
        "timestamp": "now()",
        "route_taken": f"{trip.from_location} → {trip.to_location} (demo route)",
        "ev_model_id": 1
    }).execute()

    if response.data:
        return {
            "status": "success",
            "trip_id": response.data[0].get("trip_id", "N/A"),
            "distance": distance_km,
            "battery_end": battery_end,
            "energy_used": est_battery_usage
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to save trip data.")

# -------------------------------
# Get all trips (GET)
# -------------------------------
@app.get("/trips")
def get_trips(user_id: Optional[str] = None):
    """
    Fetch all trips or filter by user_id (if provided).
    Example:
      /trips               -> returns all trips
      /trips?user_id=guest_user -> returns trips for that user
    """
    try:
        query = supabase.table("trips").select("*")
        if user_id:
            query = query.eq("user_id", user_id)

        response = query.execute()
        return {"trips": response.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
