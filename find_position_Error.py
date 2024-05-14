import pandas as pd
import random
from haversine import haversine, Unit
import datetime
import calc_sun_local_funcs as sun
import multiprocessing
import sys

def add_percent_error(number, percent_error):
    random_number = random.uniform(-percent_error, percent_error) / 100 / 100
    result = number * (1 + random_number)
    return result, random_number

# Define a function to perform the task for each iteration
def process_iteration(iteration, error_on_run, percent_error):
    solar_azimuth, azimuth_percent_error = add_percent_error(initial_solar_azimuth, percent_error)
    solar_elevation, solar_elevation_percent_error = add_percent_error(initial_solar_elevation, percent_error)

    closest_location = calculator.find_location(datetime_value, solar_azimuth, solar_elevation, lat_min=-90,
                                                lat_max=90,
                                                lon_min=-180,
                                                lon_max=180,
                                                step_size=10)

    j = 10
    while j >= 10 / (10 ** 10):
        closest_location = calculator.find_location(datetime_value, solar_azimuth, solar_elevation,
                                                    lat_min=max((closest_location[0] - j), -90),
                                                    lat_max=min((closest_location[0] + j), 90),
                                                    lon_min=max((closest_location[1] - j), -180),
                                                    lon_max=min((closest_location[1] + j), 180),
                                                    step_size=j / 10)
        j /= 10

    error_on_run[closest_location] = [haversine(intended_lat_lon, closest_location, unit=Unit.MILES),
                                       azimuth_percent_error, solar_elevation_percent_error]

 # Create an instance of the functions class
calculator = sun.functions()

# # Example usage:
# datetime_value = pd.Timestamp('2024-05-13 17:00:00')  # Example datetime

# solar_azimuth= 135.69 # Bismark, ND 05/12/2024 17:00:00 utc
# solar_elevation= 55.22 # Bismark, ND 05/12/2024 17:00:00 utc
# intended_lat_lon = [46.817, -100.783]
# max_runs = 1000

if len(sys.argv) != 8:
    print("Usage: python find_position_Error.py <datetime_value> <solar_azimuth> <solar_elevation> <latitude longitude> <max_runs>")
    sys.exit(1)
    
datetime_value_str = sys.argv[1]
solar_azimuth = float(sys.argv[2])
solar_elevation = float(sys.argv[3])
latitude = float(sys.argv[4])
longitude = float(sys.argv[5])
max_runs = int(sys.argv[6])
percent_error = float(sys.argv[7])

try:
    datetime_value = pd.Timestamp(datetime_value_str)
except ValueError:
    print("Error: Invalid datetime format. Please provide datetime in 'YYYY-MM-DD HH:MM:SS' format.")
    sys.exit(1)

intended_lat_lon = [latitude, longitude]

# Initialize error_on_run and start time
manager = multiprocessing.Manager()
error_on_run = manager.dict()
start_time = datetime.datetime.now()
date, time, hour, minute = start_time.date(), start_time.time(), start_time.hour, start_time.minute

# Set the initial solar azimuth and elevation
initial_solar_azimuth = solar_azimuth
initial_solar_elevation = solar_elevation

# Create a pool of processes
pool = multiprocessing.Pool()

# Perform the iterations in parallel
pool.starmap(process_iteration, [(i, error_on_run, percent_error) for i in range(max_runs)])

# Close the pool
pool.close()
pool.join()

# Record the end time
end_time = datetime.datetime.now()

# Calculate the runtime
runtime = end_time - start_time

hours = runtime.seconds // 3600
minutes = (runtime.seconds % 3600) // 60
seconds = runtime.seconds % 60
milliseconds = runtime.microseconds // 1000

i = 1
# with open("test_results.txt", "a") as f:
#     for key, value in error_on_run.items():
#         f.write(f"Run {i: >2} using \n" + 
#                 f"{(value[1] * 10000): >20}% azimuth error\n" + 
#                 f"{(value[2] * 10000): >20}% elevation error\nReturns:\n" + 
#                 f"( {key[0]}, {key[1]} )\nwhich is {value[0]} miles away\n\n")
#         i += 1

i = 1
for key, value in error_on_run.items():
    print(f"Run {i: >2} using \n" + 
          f"{(value[1] * 10000): >20}% azimuth error\n" + 
          f"{(value[2] * 10000): >20}% elevation error\nReturns:\n" + 
          f"( {key[0]}, {key[1]} )\nwhich is {value[0]} miles away\n\n")
    i += 1

values = [data[0] for data in error_on_run.values()]

# Calculate mean
mean_value = sum(values) / len(values)

# Calculate median
sorted_values = sorted(values)
n = len(sorted_values)
if n % 2 == 0:
    median_value = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
else:
    median_value = sorted_values[n//2]

# Calculate minimum and maximum
min_value = min(values)
max_value = max(values)

# Write statistics to file
with open("test_results.txt", "a") as f:
    f.write(f"\nTest started at {date}:{time}\n")
    f.write(f"Completed {max_runs} runs with a maximum of {percent_error}% error\n")
    f.write(f"Took {hours}:{minutes}:{seconds}.{milliseconds}\n")
    f.write("\nStatistics:\n")
    f.write("Distances from Intended in Miles:\n")
    f.write(f"Mean: {mean_value}\n")
    f.write(f"Median: {median_value}\n")
    f.write(f"Minimum: {min_value}\n")
    f.write(f"Maximum: {max_value}\n")
    f.write("!" * 100)
    f.write("\n\n\n")

print("Mean:", mean_value)
print("Median:", median_value)
print("Minimum:", min_value)
print("Maximum:", max_value)