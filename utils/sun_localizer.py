from haversine import haversine, Unit
from tqdm import tqdm
import csv
import folium
import os
import pandas as pd
import webbrowser
import yaml

from utils.functions import Functions
from utils.loc_describer_agent import navigation_agent
from utils.summarize_results import SolarResultsAnalyzer

class SunLocalizer():
    def __init__(self, args, datetime_rt):
        self.args = args
        self.datetime_rt = datetime_rt
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
            lat = min(max(lat, -90.0), 90.0)
            lon = min(max(lon, -180.0), 180.0)
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
                                 unit=Unit.METERS)
            if self.distance < 0:
                print("WTF")

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
                            tooltip=f'{self.distance:.2f} meters'
                            ).add_to(mymap)

        output_path = os.path.join("results", 
                                   self.datetime_rt,
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
        if self.mode == "shadow":
            target_elevation = self.calculator.calculate_solar_elevation_from_shadow(self.height_of_object, 
                                                                                     self.length_of_shadow)
            # print("Estimated solar elevation angle:", target_elevation, "degrees")
            self.solar_elevation = target_elevation
            
        self.calc_closest_location()

    def write_results(self, output_path):
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
        if not os.path.exists(output_path):
            with open(output_path, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(results.keys()))
                writer.writeheader()

        with open(output_path, "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(results.keys()))
            writer.writerow(results)

    def name_file(self):
        """
        Create a filename for saving the results based on the errors in the solar azimuth and elevation.

        If both errors are positive, the filename will be "results_az_+{azimuth_error}_el_+{elevation_error}.csv".
        If the azimuth error is positive and the elevation error is negative, 
        the filename will be "results_az_+{azimuth_error}_el_{elevation_error}.csv".
        If the azimuth error is negative and the elevation error is positive, 
        the filename will be "results_az_{azimuth_error}_el_+{elevation_error}.csv".
        If both errors are negative, the filename will be "results_az_{azimuth_error}_el_{elevation_error}.csv".
        If either or both errors are zero, the filename will be "results.csv".

        Returns
        -------
        str
            The filename for saving the results.
        """
        self.csvs_path = os.path.join("results", self.datetime_rt, "csvs")
        os.makedirs(self.csvs_path, exist_ok=True)
        if hasattr(self, "test_db"):
            self.jsons_path = os.path.join("results", self.datetime_rt, "jsons")
            os.makedirs(self.jsons_path, exist_ok=True)

        if self.azimuth_error > 0 and self.elevation_error > 0:
            file_name = f"results_az_+{self.azimuth_error}_el_+{self.elevation_error}.csv"
        elif self.azimuth_error > 0 and self.elevation_error < 0:
            file_name = f"results_az_+{self.azimuth_error}_el_{self.elevation_error}.csv"
        elif self.azimuth_error < 0 and self.elevation_error > 0:
            file_name = f"results_az_{self.azimuth_error}_el_+{self.elevation_error}.csv"
        elif self.azimuth_error < 0 and self.elevation_error < 0:
            file_name = f"results_az_{self.azimuth_error}_el_{self.elevation_error}.csv"
        else:
            file_name = f"results_az_+{self.azimuth_error}_el_+{self.elevation_error}.csv"

        return file_name

    def find_me(self, azimuth_error=0, elevation_error=0, show_progress=True):    
        """
        Run the solar location finder on either a config file or a pandas dataframe.

        If `degrees_of_error` is greater than 0, the function will run the solar location
        finder multiple times with different error offsets for the solar azimuth and
        elevation angles. The error offsets are generated by the
        `create_error_combinations` function.

        If `degrees_of_error` is 0, the function will run the solar location finder once
        with no error offset.

        Parameters
        ----------
        azimuth_error : int
            The error offset to add to the solar azimuth angle.
        elevation_error : int
            The error offset to add to the solar elevation angle.
        show_progress : bool, default=True
            Whether to display a tqdm progress bar during iteration.
        """
        self.azimuth_error = azimuth_error
        self.elevation_error = elevation_error

        file_name = self.name_file()
        csv_path = os.path.join(self.csvs_path, file_name)

        if hasattr(self, "config"):
            self.run()
            if self.args.agent_description:
                description = navigation_agent(self.closest_location[0], 
                                            self.closest_location[1], 
                                            self.datetime_value, 
                                            self.solar_azimuth)
                print("\nNavigation Description:\n")
                print(description)
            print(f"Estimated location: {self.closest_location}")
            print(f"Distance from intended location: {self.distance} meters")
            self.write_results(csv_path)
            if not self.args.skip_map:
                self.plot_location()

        elif hasattr(self, "test_db"):
            self.mode = "angles"

            analyzer = SolarResultsAnalyzer(csv_path)
            for _, row in tqdm(
                self.test_db.iterrows(),
                desc="Running tests",
                total=len(self.test_db),
                disable=not show_progress  # toggle here
            ):
                try:
                    self.filename = f"{row['city']}_{row['country']}"
                    self.datetime_value = pd.Timestamp(row["timestamp"])
                    self.solar_azimuth = row["azimuth"] + azimuth_error
                    self.solar_elevation = row["elevation"] + elevation_error
                    self.intended_lat_lon = [row["latitude"], row["longitude"]]
                    self.run()
                    self.write_results(csv_path)
                    if not self.args.skip_map:
                        self.plot_location()
                except Exception as e:
                    print(f"Error processing row {row['timestamp']}: {e}")
                    continue

            analyzer.summarize(os.path.join(
                self.jsons_path,
                f"summary_{file_name.replace('.csv', '.json')}"
            ))
