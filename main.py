import pandas as pd
import folium
import webbrowser
from haversine import haversine, Unit
import sys
import os
import yaml

from utils.functions import Functions

def load_config(yaml_file):
    """Load YAML configuration."""
    with open(yaml_file, "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    # Require config file path
    if len(sys.argv) < 2:
        print("Usage: python script.py config.yaml")
        sys.exit(1)

    config_file = sys.argv[1]
    config = load_config(config_file)

    # Create an instance of the functions class
    calculator = Functions()

    # Load config values
    mode               = config.get("mode")
    filename           = config.get("filename")
    datetime_value     = config.get("datetime")
    height_of_object   = config.get("height_of_object")
    length_of_shadow   = config.get("length_of_shadow")
    solar_azimuth      = config.get("solar_azimuth")
    solar_elevation    = config.get("solar_elevation")
    intended_latitude  = config.get("intended_latitude")
    intended_longitude = config.get("intended_longitude")

    print(f"Mode: {mode}\n"
          f"Filename: {filename}\n"
          f"Datetime: {datetime_value}\n"
          f"Height of Object: {height_of_object}\n"
          f"Length of Shadow: {length_of_shadow}\n"
          f"Solar Azimuth: {solar_azimuth}\n"
          f"Solar Elevation: {solar_elevation}\n"
          f"Intended Latitude: {intended_latitude}\n"
          f"Intended Longitude: {intended_longitude}")

    # Convert datetime
    datetime_value = pd.Timestamp(datetime_value)
    intended_lat_lon = [intended_latitude, intended_longitude]

    # If mode is lengths, calculate solar elevation
    if mode == "lengths":
        target_elevation = calculator.calculate_solar_elevation_from_shadow(height_of_object, length_of_shadow)
        print("Estimated solar elevation angle:", target_elevation, "degrees")
        solar_elevation = target_elevation

    # Find location (progressive refinement)
    closest_location = calculator.find_location(datetime_value, solar_azimuth, solar_elevation,
                                                lat_min=-90, lat_max=90, lon_min=-180, lon_max=180, step_size=10)
    i = 10
    while i >= 10/(10**10):
        closest_location = calculator.find_location(datetime_value, solar_azimuth, solar_elevation,
                                                    lat_min=max((closest_location[0] - i), -90),
                                                    lat_max=min((closest_location[0] + i), 90),
                                                    lon_min=max((closest_location[1] - i), -180),
                                                    lon_max=min((closest_location[1] + i), 180),
                                                    step_size=i / 10)
        i /= 10

    print("Closest location:", closest_location)

    # Folium map
    closest = closest_location
    mymap = folium.Map(location=closest, zoom_start=5)

    folium.Marker(closest, tooltip=f"Coordinates: {closest}",
                  icon=folium.Icon(color='red', icon='camera'),
                  popup="Centroid").add_to(mymap)

    if intended_lat_lon is not None:
        distance = haversine(intended_lat_lon, closest, unit=Unit.MILES)
        folium.Marker(intended_lat_lon,
                      tooltip=f"Intended: {intended_lat_lon}",
                      icon=folium.Icon(color='blue', icon='home'),
                      popup="Centroid").add_to(mymap)
        folium.PolyLine([intended_lat_lon, closest], color='blue',
                        tooltip=f'{distance:.2f} miles').add_to(mymap)

    # Save & open map
    output_path = os.path.join("results/", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mymap.save(output_path)
    
    # uncomment the line below to open the map automatically on run
    # webbrowser.open(output_path)