import subprocess
import sys
import pandas as pd
import datetime
import time
import os
from random_location_Generator import random_locations
import statistics
from write_stats import write_stats
import math

timestamp = time.strftime('%Y_%m_%d__%H_%M_%S', time.localtime())
directory = f"Tests/{timestamp}"
# Create the directory if it doesn't exist
os.makedirs(directory, exist_ok=True)

def calculate_solar_elevation_from_shadow(height_of_object, length_of_shadow):
        """
        Calculate the solar elevation angle based on the height of an object and the length of its shadow.

        Args:
            height_of_object (float): The height of the object in meters.
            length_of_shadow (float): The length of the shadow cast by the object in meters.

        Returns:
            float or None: The solar elevation angle in degrees if height_of_object and length_of_shadow are positive,
                        otherwise returns None.
        """
        # Ensure height_of_object and length_of_shadow are non-zero
        if height_of_object <= 0 or length_of_shadow <= 0:
            return None
        
        # Calculate the angle in radians
        angle_radians = math.atan(length_of_shadow / height_of_object)
        
        # Convert radians to degrees
        angle_degrees = math.degrees(angle_radians)
        
        # Calculate solar elevation angle
        solar_elevation = 90 - angle_degrees
        print(f"\nHeight: {height_of_object} and \nLength {length_of_shadow} \ngives {max(20, solar_elevation)}")
        return max(20, solar_elevation)  # Ensure solar elevation is non-negative
    


def read_test_txt(testing_filename):
    tests = []
    times = []
    azimiuths = []
    elevations = []
    heights = []
    lengths = []
    lats = []
    lons = []
    names = []
    with open(testing_filename, 'r') as f:
        for line in f:
            if "Timestamp: " in line:
                _time = str(line.split("Timestamp: ")[1])
                times.append(_time)
            elif "Azimuth:" in line:
                azimuth = float(line.split("Azimuth:")[1].strip())
                azimiuths.append(azimuth)
            elif "Elevation:" in line:
                elevation = float(line.split("Elevation:")[1].strip())
                elevations.append(elevation)
            elif "Obj Height:" in line:
                height = float(line.split("Obj Height:")[1].strip())
                heights.append(height)
            elif "Shadow Length:" in line:
                length = float(line.split("Shadow Length:")[1].strip())
                lengths.append(length)
            elif "Latitude:" in line:
                lat = float(line.split("Latitude:")[1].strip())
                lats.append(lat)
            elif "Longitude:" in line:
                lon = float(line.split("Longitude:")[1].strip())
                lons.append(lon)
            if "Name: " in line:
                name = str(line.split("Name: ")[1].strip())
                names.append(name)
    
    if len(elevations) == 0:
        for height, length in zip(heights, lengths):
            elevations.append(calculate_solar_elevation_from_shadow(height, length))
            elevations_range = max(elevations) - min(elevations)

    try:
        for i in range(0, len(times)):
            tests.append((pd.Timestamp(times[i]), 
                        azimiuths[i],
                        elevations[i],
                        [lats[i], lons[i]],
                        names[i]))
    except:
        print("Txt file gives invalid values")
        sys.exit(1)

    return tests, elevations_range.ceil()
                




def run_test(datetime_value, solar_azimuth, solar_elevation, intended_lat_lon, city_name, elevations_range = None):
    i = 1
    while i < len(sys.argv):
        if(sys.argv[i] == "-fileName" and i < len(sys.argv) - 1):
            i += 1
            percent_error = elevations_range
        else:
            percent_error = 3
        i += 1

    filename = f"Tests/{timestamp}"

    with open(filename + "/test_results.txt", "a") as f:
        f.write("!" * 100)
        f.write(f"\nIntended Target: {city_name};\nCoords: {intended_lat_lon};\naz/el: [{solar_azimuth}, {solar_elevation}]\n")

    args = [
        sys.executable,
        'find_position_Error.py',
        str(datetime_value),
        str(solar_azimuth),
        str(solar_elevation),
        str(intended_lat_lon[0]),
        str(intended_lat_lon[1]),
        str(int(percent_error * 2 * 100)),
        str(percent_error),
        str(city_name),
        str(filename)
    ]
    
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        sys.exit(1)


def main():
    runs = None
    testing_filename = None

    i = 1
    while i < len(sys.argv):
        if(sys.argv[i] == "-locations" and i < len(sys.argv) - 1):
            i += 1
            runs = int(sys.argv[i])
        elif(sys.argv[i] == "-fileName" and i < len(sys.argv) - 1):
            i += 1
            testing_filename = str(sys.argv[i])
        else:
            print("ERROR: Invalid usage")
            sys.exit(1)
        i += 1

    if runs is not None and testing_filename is None:
        tests = random_locations(runs)
    elif runs is None and testing_filename is not None:
        tests, elevations_range = read_test_txt(testing_filename)
    else:
        print("ERROR: Invalid usage")
        sys.exit(1)


    # tests = [
    #     (pd.Timestamp('2024-05-13 17:00:00'), 135.69, 55.22, [46.817, -100.783], "Bismark, ND"),  # Bismark, ND
    #     (pd.Timestamp('2024-05-13 22:00:00'), 110.7, 82.97, [21.3, -157.85], "Honolulu, HI"),     # Honolulu, HW
    #     (pd.Timestamp('2024-05-13 16:00:00'), 107.97, 70.81, [25.77, -80.18], "Miami, FL"),   # Miami, Fl
    #     (pd.Timestamp('2024-05-13 19:00:00'), 149.57, 58.11, [47.6, -122.32], "Seattle, WA"),    # Seattle, WA
    #     (pd.Timestamp('2024-05-13 17:00:00'), 2.1, 59.31, [-12.05, -77.04], "Lima, Peru"),    # Lima, Peru
    #     (pd.Timestamp('2024-05-13 11:00:00'), 155.93, 55.22, [51.50, -0.12], "London, England"),    # London, England
    #     (pd.Timestamp('2024-05-13 10:00:00'), 1.43, 45.24, [-26.21, 28.03], "Johannesberg, South Africa")    # Johannesberg, South Africa
    # ]

    # Record the start time
    start_time = datetime.datetime.now()
    for test in tests:
        run_test(*test, elevations_range)

    # Record the end time
    end_time = datetime.datetime.now()

    # Calculate the runtime
    runtime = end_time - start_time

    write_stats(timestamp, str(runtime))
        

if __name__ == "__main__":
    main()
