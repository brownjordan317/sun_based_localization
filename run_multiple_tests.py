import subprocess
import sys
import pandas as pd
import random
import datetime
import ephem
import math
from datetime import date, datetime
import time
import os

timestamp = time.strftime('%Y_%m_%d__%H_%M_%S', time.localtime())
directory = f"Tests/{timestamp}"
# Create the directory if it doesn't exist
os.makedirs(directory, exist_ok=True)

def run_test(datetime_value, solar_azimuth, solar_elevation, intended_lat_lon, city_name):
    percent_error = 3

    filename = f"Tests/{timestamp}"

    with open(filename + "/test_results.txt", "a") as f:
        f.write("!" * 100)
        f.write(f"\nIntended Target: {city_name} {intended_lat_lon}\n")

    args = [
        sys.executable,
        'find_position_Error.py',
        str(datetime_value),
        str(solar_azimuth),
        str(solar_elevation),
        str(intended_lat_lon[0]),
        str(intended_lat_lon[1]),
        str(percent_error * 2 * 100),
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
    tests = [
        (pd.Timestamp('2024-05-13 17:00:00'), 135.69, 55.22, [46.817, -100.783], "Bismark, ND"),  # Bismark, ND
        (pd.Timestamp('2024-05-13 22:00:00'), 110.7, 82.97, [21.3, -157.85], "Honolulu, HI"),     # Honolulu, HW
        (pd.Timestamp('2024-05-13 16:00:00'), 107.97, 70.81, [25.77, -80.18], "Miami, FL"),   # Miami, Fl
        (pd.Timestamp('2024-05-13 19:00:00'), 149.57, 58.11, [47.6, -122.32], "Seattle, WA"),    # Seattle, WA
        (pd.Timestamp('2024-05-13 17:00:00'), 2.1, 59.31, [-12.05, -77.04], "Lima, Peru"),    # Lima, Peru
        (pd.Timestamp('2024-05-13 11:00:00'), 155.93, 55.22, [51.50, -0.12], "London, England"),    # London, England
        (pd.Timestamp('2024-05-13 10:00:00'), 1.43, 45.24, [-26.21, 28.03], "Johannesberg, South Africa")    # Johannesberg, South Africa
    ]

    for test in tests:
        run_test(*test)

if __name__ == "__main__":
    main()
