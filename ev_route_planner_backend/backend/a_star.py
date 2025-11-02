import heapq
import math

# --------------------------------------------------
# Haversine formula — to calculate distance between coordinates
# --------------------------------------------------
def haversine_distance(coord1, coord2):
    """
    Calculate the great-circle distance between two points
    on the Earth specified in decimal degrees.
    Returns distance in kilometers.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# --------------------------------------------------
# Heuristic Function (used by A* to guide the search)
# --------------------------------------------------
def heuristic(node, goal):
    """
    Estimate remaining distance between current node and goal.
    """
    return haversine_distance(node, goal)


# --------------------------------------------------
# A* Algorithm Core Logic
# --------------------------------------------------
def a_star(graph, start, goal, battery_range_km):
    """
    graph: dict of {node: {neighbor: distance_km}}
    start: starting coordinate tuple (lat, lng)
    goal: destination coordinate tuple (lat, lng)
    battery_range_km: how far EV can go on current battery

    Returns best route if found, else None
    """
    open_set = [(0, start)]
    came_from = {}
    g_score = {node: float("inf") for node in graph}
    g_score[start] = 0

    while open_set:
        current_f, current_node = heapq.heappop(open_set)

        if current_node == goal:
            return reconstruct_path(came_from, current_node)

        for neighbor, distance in graph[current_node].items():
            if distance > battery_range_km:
                continue  # can't reach without charging

            tentative_g = g_score[current_node] + distance
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None


# --------------------------------------------------
# Path Reconstruction (once goal is reached)
# --------------------------------------------------
def reconstruct_path(came_from, current):
    """
    Build the final route path after reaching goal node.
    """
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


# --------------------------------------------------
# Example Test (for local check)
# --------------------------------------------------
if __name__ == "__main__":
    # Example graph (simple 4-node route)
    graph = {
        (17.3850, 78.4867): {(17.5, 78.5): 20, (17.4, 78.6): 15},
        (17.5, 78.5): {(17.3850, 78.4867): 20, (17.7, 78.7): 30},
        (17.4, 78.6): {(17.3850, 78.4867): 15, (17.7, 78.7): 25},
        (17.7, 78.7): {},
    }

    start = (17.3850, 78.4867)
    goal = (17.7, 78.7)
    battery_range = 100  # in km

    path = a_star(graph, start, goal, battery_range)
    print("🔋 Optimal path:", path)
