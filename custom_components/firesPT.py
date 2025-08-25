import requests
import math
import json
import argparse

# Função Haversine para calcular distância
def haversine(coord1, coord2):
    R = 6371  # Earth radius in km
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c

# Função para verificar incêndios
def check_fires(my_coordinate, radius_km):
    url = "https://api.fogos.pt/new/fires"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        fires = []
        for fire in data.get("data", []):
            if not (fire.get("lat") and fire.get("lng") and fire.get("statusCode") == 5):
                continue
            fire_coordinate = (float(fire["lat"]), float(fire["lng"]))
            distance = haversine(my_coordinate, fire_coordinate)
            if distance <= radius_km:
                fires.append({
                    "location": fire.get("location"),
                    "distance_km": round(distance, 2),
                    "lat": fire.get("lat"),
                    "lng": fire.get("lng")
                })

        result = {
            "fire_active": len(fires) > 0,
            "fires": fires
        }

        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

# Entrada via linha de comando
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check fires near a location")
    parser.add_argument("--lat", type=float, default=39.966298, help="Latitude of your location")
    parser.add_argument("--lng", type=float, default=-8.797222, help="Longitude of your location")
    parser.add_argument("--radius", type=float, default=200, help="Radius in km to check for fires")

    args = parser.parse_args()
    user_coordinate = (args.lat, args.lng)
    radius_km = args.radius

    check_fires(user_coordinate, radius_km)