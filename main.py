from haversine import haversine, Unit
from tqdm import tqdm
import argparse
import folium
import os
import pandas as pd
import webbrowser
import yaml
from datetime import datetime
import csv

from utils.functions import Functions
from utils.loc_describer_agent import navigation_agent
from utils.random_location_Generator import random_locations
from utils.summarize_results import SolarResultsAnalyzer

datetime_rt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs(os.path.join("results", datetime_rt), exist_ok=True)

class SunLocalizer():
    def __init__(self, args):
        self.args = args
        if args.config.endswith(".yaml"):
            self.load_config_yaml(args.config)
        elif args.config.endswith(".csv"):
            self.load_config_csv(args.config)
        else:
            raise ValueError("Invalid configuration file format. Please provide a YAML or CSV file.")
        self.calculator = Functions()

    def load_config_yaml(self, yaml_file):
        """
        Load the configuration from a YAML file.

        The configuration file should contain the following keys and values:

            mode: string, either "angles" or "shadows"
            filename: string, the name of the file to save the results to
            datetime: string, the UTC datetime for the observation, in the format "%Y-%m-%d %H:%M:%S"
            solar_azimuth: float, the solar azimuth angle in degrees
            intended_latitude: float, the intended latitude of the observation
            intended_longitude: float, the intended longitude of the observation

            and one of the following:


            height_of_object: float, the height of the object casting the shadow
            length_of_shadow: float, the length of the shadow

            or

            solar_elevation: float, the solar elevation angle in degrees

        Parameters
        ----------
        yaml_file : str
            The path to the YAML file containing the configuration.
        """
        with open(yaml_file, "r") as f:
            self.config = yaml.safe_load(f)

        # Read and store the configuration
        self.mode               = self.config.get("mode")
        self.filename           = self.config.get("filename")
        self.datetime_value     = pd.Timestamp(self.config.get("datetime"))
        self.height_of_object   = self.config.get("height_of_object")
        self.length_of_shadow   = self.config.get("length_of_shadow")
        self.solar_azimuth      = self.config.get("solar_azimuth")
        self.solar_elevation    = self.config.get("solar_elevation")
        self.intended_lat_lon   = [self.config.get("intended_latitude"), 
                                   self.config.get("intended_longitude")]

        # Print the configuration to the console
        print(f"Mode: {self.mode}\n"
              f"Filename: {self.filename}\n"
              f"Datetime: {self.datetime_value}\n"
              f"Height of Object: {self.height_of_object}\n"
              f"Length of Shadow: {self.length_of_shadow}\n"
              f"Solar Azimuth: {self.solar_azimuth}\n"
              f"Solar Elevation: {self.solar_elevation}\n"
              f"Intended Lat, Lon: {self.intended_lat_lon}\n"
              )
    
    def load_config_csv(self, csv_file):
        """
        Load the configuration from a CSV file.

        The CSV file should contain columns for timestamp, intended_latitude,
        intended_longitude, solar_azimuth, solar_elevation, city, and country.

        Parameters
        ----------
        csv_file : str
            The path to the CSV file containing the configuration.
        """
        self.test_db = pd.read_csv(csv_file)

    def calc_closest_location(self, initial_step=10.0, refinement_factor=10, min_step=1e-9):
        """
        Iteratively refine the closest location with maximum accuracy.

        Parameters
        ----------
        initial_step : float
            Starting step size (degrees).
        refinement_factor : int
            Factor by which step size is reduced each iteration.
        min_step : float
            Minimum step size to stop refinement.
        """
        # Initial global search
        self.closest_location = self.calculator.find_location(self.datetime_value,
                                                            self.solar_azimuth,
                                                            self.solar_elevation,
                                                            lat_min=-90, lat_max=90,
                                                            lon_min=-180, lon_max=180,
                                                            step_size=initial_step
                                                            )

        step = initial_step
        while step > min_step:
            lat, lon = self.closest_location
            self.closest_location = self.calculator.find_location(self.datetime_value,
                                                                self.solar_azimuth,
                                                                self.solar_elevation,
                                                                lat_min=max(lat - step, -90), lat_max=min(lat + step, 90),
                                                                lon_min=max(lon - step, -180), lon_max=min(lon + step, 180),
                                                                step_size=step / refinement_factor)

            # Reduce step size for next refinement
            step /= refinement_factor

        if self.intended_lat_lon is not None:
            self.distance = haversine(self.intended_lat_lon, 
                                 self.closest_location, 
                                 unit=Unit.MILES)

    def plot_location(self):
        """
        Plot the closest location on a map.

        Notes
        -----
        If `intended_lat_lon` is not None, the map will also show the intended location
        and the distance between the intended and closest locations.
        """
        mymap = folium.Map(location=self.closest_location, zoom_start=5)
        folium.Marker(self.closest_location, tooltip=f"Coordinates: {self.closest_location}",
                    icon=folium.Icon(color='red', icon='camera'),
                    popup="Centroid").add_to(mymap)

        if self.intended_lat_lon is not None:
            folium.Marker(self.intended_lat_lon,
                          tooltip=f"Intended: {self.intended_lat_lon}",
                          icon=folium.Icon(color='blue', icon='home'),
                          popup="Centroid"
                          ).add_to(mymap)
            folium.PolyLine([self.intended_lat_lon, self.closest_location], 
                            color='blue',
                            tooltip=f'{self.distance:.2f} miles'
                            ).add_to(mymap)

        output_path = os.path.join("results", 
                                   datetime_rt,
                                   "maps", 
                                   f"{self.filename}_{str(self.datetime_value).replace(' ', '_')}.html")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        mymap.save(output_path)
        
        if self.args.open_map:
            webbrowser.open(output_path)

    def run(self):
        """
        Find the closest location to the given solar azimuth and elevation angles.

        Parameters:
        agent_description (bool): If True, print out a description of how to navigate to the location.
        """
        if self.mode == "lengths":
            target_elevation = self.calculator.calculate_solar_elevation_from_shadow(self.height_of_object, 
                                                                                     self.length_of_shadow)
            print("Estimated solar elevation angle:", target_elevation, "degrees")
            self.solar_elevation = target_elevation
            
        self.calc_closest_location()

        if self.args.agent_description:
            description = navigation_agent(self.closest_location[0], 
                                           self.closest_location[1], 
                                           self.datetime_value, 
                                           self.solar_azimuth)
            print("\nNavigation Description:\n")
            print(description)

    def write_results(self):
        """
        Write the results to a CSV file.

        The file is saved in a directory named "results" in the current working directory.
        The filename is the same as the input filename, but with the ".html" extension removed.
        The columns are "location", "intended_lat_lon", "closest_location", and "distance_miles".
        The first row is the header, and the second row is the results.
        """
        results = {
            "location": self.filename.strip(".html"),
            "intended_lat_lon": self.intended_lat_lon,
            "closest_location": self.closest_location,
            "distance_miles": self.distance
        }

        output_path = os.path.join("results", datetime_rt, "results.csv")
        if not os.path.exists(output_path):
            with open(output_path, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(results.keys()))
                writer.writeheader()

        with open(output_path, "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(results.keys()))
            writer.writerow(results)

    def find_me(self):
        """
        Run the solar location finder on either a config file or a pandas dataframe.

        If `config` is an attribute of the object, it will run the solar location finder on the config file.
        If `test_db` is an attribute of the object, it will run the solar location finder on the pandas dataframe.
        """
        if hasattr(self, "config"):
            self.run()
            self.write_results()
            if not args.skip_map:
                self.plot_location()
        elif hasattr(self, "test_db"):
            self.mode = "angles"
            analyzer = SolarResultsAnalyzer("results", datetime_rt)
            for _, row in tqdm(self.test_db.iterrows(), desc="Running tests", total=len(self.test_db)):
                try:
                    self.filename = f"{row['city']}_{row['country']}"
                    self.datetime_value = pd.Timestamp(row["timestamp"])
                    self.solar_azimuth = row["azimuth"]
                    self.solar_elevation = row["elevation"]
                    self.intended_lat_lon = [row["latitude"], row["longitude"]]
                    self.run()
                    self.write_results()
                    if not args.skip_map:
                        self.plot_location()
                except Exception as e:
                    print(f"Error processing row {row['timestamp']}: {e}")
                    continue
            analyzer.summarize()

if __name__ == "__main__":
    # Require config file path
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, help="Path to the YAML configuration file")
    parser.add_argument("--random", type=int, help="Number of random locations to run on")
    parser.add_argument("--skip_map", action="store_true", help="Skip map generation")
    parser.add_argument("--open_map", action="store_true", help="Open the map in a web browser")
    parser.add_argument("--agent_description", action="store_true", help="Print navigation description")
    args = parser.parse_args()

    if args.random:
        os.makedirs("random_location_csvs", exist_ok=True)
        file_name = f"{datetime_rt}.csv"
        file_name = os.path.join("random_location_csvs", file_name)
        random_locations(args.random, file_name)
        args.config = file_name

    sun_localizer = SunLocalizer(args)
    sun_localizer.find_me()
