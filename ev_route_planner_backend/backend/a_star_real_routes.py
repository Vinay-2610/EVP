import os
import math
import heapq
import requests
from dotenv import load_dotenv
from a_star import a_star

def get_nearest_charging_stations(lat, lng, api_key, radius=5000):
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={lat},{lng}&radius={radius}&keyword=EV%20charging%20station&key={api_key}"
    )
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return {"message": "No charging stations found", "count": 0, "stations": []}

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

# ----------------------------
# 1️⃣ Load API Key
# ----------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ----------------------------
# 2️⃣ Helper: Haversine formula
# ----------------------------
def haversine(coord1, coord2):
    R = 6371
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# ----------------------------
# 3️⃣ Core A* Algorithm
# ----------------------------
def a_star(graph, start, goal, battery_range_km):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for neighbor, dist in graph.get(current, []):
            if dist > battery_range_km:
                continue
            tentative_g = g_score[current] + dist
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + haversine(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None

# ----------------------------
# 4️⃣ Build Graph Using Google Directions
# ----------------------------
def build_graph_from_google(from_location, to_location, api_key):
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json?"
        f"origin={from_location}&destination={to_location}&key={api_key}"
    )

    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        raise Exception(f"Google Directions API Error: {data['status']}")

    route = data["routes"][0]["legs"][0]["steps"]
    graph = {}

    for step in route:
        start_loc = (step["start_location"]["lat"], step["start_location"]["lng"])
        end_loc = (step["end_location"]["lat"], step["end_location"]["lng"])
        distance_km = step["distance"]["value"] / 1000

        graph.setdefault(start_loc, []).append((end_loc, distance_km))
        graph.setdefault(end_loc, []).append((start_loc, distance_km))

    print(f"✅ Graph built with {len(graph)} nodes")
    start = (route[0]["start_location"]["lat"], route[0]["start_location"]["lng"])
    goal = (route[-1]["end_location"]["lat"], route[-1]["end_location"]["lng"])
    return graph, start, goal

# ----------------------------
# 5️⃣ Main Runner
# ----------------------------
def run_a_star_with_google(from_location, to_location, battery_range_km, api_key):
    graph, start, goal = build_graph_from_google(from_location, to_location, api_key)

    if not graph:
        return {"message": "Failed to build graph or no route data available"}

    path = a_star(graph, start, goal, battery_range_km)

    # --- If no valid path ---
    if not path:
        midpoint = start  # fallback to start coordinates
        charging_suggestions = get_nearest_charging_stations(midpoint[0], midpoint[1], api_key)

        return {
            "status": "failed",
            "message": "No valid path found (battery may be insufficient)",
            "total_distance_km": 0,
            "estimated_range_km": battery_range_km,
            "path": path or [],
            "charging_suggestions": charging_suggestions,
        }

    # --- Calculate total distance ---
    total_distance_km = 0
    for i in range(len(path) - 1):
        for neighbor, dist in graph[path[i]]:
            if neighbor == path[i + 1]:
                total_distance_km += dist
                break

    # --- Midpoint for station lookup ---
    midpoint = path[len(path) // 2]
    charging_suggestions = get_nearest_charging_stations(midpoint[0], midpoint[1], api_key)

    return {
        "status": "success",
        "path": path,
        "total_distance_km": round(total_distance_km, 2),
        "estimated_range_km": battery_range_km,
        "message": (
            "✅ Route within range."
            if total_distance_km <= battery_range_km
            else "⚠️ Range insufficient — recharge required mid-route."
        ),
        "charging_suggestions": charging_suggestions,
    }



# ----------------------------
# 6️⃣ Run Test
# ----------------------------
if __name__ == "__main__":
    from_loc = "Hyderabad"
    to_loc = "Warangal"
    battery_range = 120

    result = run_a_star_with_google(from_loc, to_loc, battery_range, GOOGLE_API_KEY)
    print(result)
