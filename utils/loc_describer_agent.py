from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import ollama  # Correct import

def compass_direction(degrees):
    dirs = ['North', 'North-East', 'East', 'South-East',
            'South', 'South-West', 'West', 'North-West']
    ix = round(degrees / 45) % 8
    return dirs[ix]
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

def get_nearby_cities(lat, lon, radius_km=50, max_results=5):
    geolocator = Nominatim(user_agent="nav_agent")

    # Bounding box: ((south, west), (north, east))
    delta = 0.5  # rough ~50 km
    south, west = lat - delta, lon - delta
    north, east = lat + delta, lon + delta
    viewbox = ((south, west), (north, east))

    try:
        locations = geolocator.geocode(
            query="city",
            exactly_one=False,
            viewbox=viewbox,
            bounded=True
        )
    except Exception as e:
        print("Geocoding error:", e)
        return []

    cities = []
    if locations:
        for loc in locations[:max_results]:
            dist = geodesic((lat, lon), (loc.latitude, loc.longitude)).km
            if dist <= radius_km:
                cities.append({
                    'name': loc.raw.get('display_name').split(',')[0],
                    'lat': loc.latitude,
                    'lon': loc.longitude,
                    'distance_km': round(dist, 2)
                })
    return cities



def generate_prompt(lat, lon, utc_time, solar_azimuth, cities):
    """
    Generate a prompt for a location-describing navigation assistant.

    The model should describe the estimated location in relation to nearby cities,
    giving compass directions, distances, and how the solar azimuth aligns.
    """
    city_list = '\n'.join([
        f"- {c['name']} ({c['lat']}, {c['lon']}), approx. {c['distance_km']} km away"
        for c in cities
    ])
    
    return f"""
        You are a geographic analysis assistant.

        Estimated current location (from another program): ({lat}, {lon})
        Current UTC: {utc_time}
        Solar azimuth: {solar_azimuth}°

        Nearby cities and their approximate distances:
        {city_list}

        Describe the current location in relation to these nearby cities.
        For each city, explain:
        - Compass direction from your estimated location
        - Relative orientation to the sun (solar azimuth)
        - Approximate distance

        Do not give navigation instructions; instead, provide a descriptive summary of your position relative to the surrounding cities.
        """


def navigation_agent(lat, lon, utc_time, solar_azimuth, model_name="llama2"):
    cities = get_nearby_cities(lat, lon)
    if not cities:
        return "No nearby cities found within 50 km."
    
    prompt = generate_prompt(lat, lon, utc_time, solar_azimuth, cities)
    
    # Chat with the model
    response = ollama.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
    
    # Return just the text
    return response.message.content



# ---------- Example Usage ----------

if __name__ == "__main__":
    lat, lon = 47.2321832786, -94.98680949989993
    utc_time = "2025-08-21 17:00:00"
    solar_azimuth = 146.97

    description = navigation_agent(lat, lon, utc_time, solar_azimuth)
    print("\nNavigation Description:\n")
    print(description)
