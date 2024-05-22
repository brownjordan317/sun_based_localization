import pandas as pd
import random
from haversine import haversine, Unit
import datetime
import calc_sun_local_funcs as sun
import multiprocessing
import sys
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from folium.plugins import MousePosition
from folium.plugins import HeatMap, MousePosition, MeasureControl, MarkerCluster
import os
import numpy as np


def add_percent_error(number, percent_error):
    random_number = random.uniform(-percent_error, percent_error)
    # print("error", random_number)
    result = number + random_number
    # print("number", number)
    # print("result", result)
    return result, random_number

# Define a function to perform the task for each iteration
def process_iteration(iteration, error_on_run, change):
    if iteration is not None:
        if change == 'azimuth' or change == 'both':
            solar_azimuth, azimuth_percent_error = add_percent_error(initial_solar_azimuth, (iteration / 100))
        else:
            solar_azimuth = initial_solar_azimuth
            azimuth_percent_error = 0  # or any default value you prefer

        if change == 'elevation' or change == 'both':
            solar_elevation, solar_elevation_percent_error = add_percent_error(initial_solar_elevation, (iteration / 100))
            solar_elevation = max(solar_elevation, 20)
        else:
            solar_elevation = initial_solar_elevation
            solar_elevation_percent_error = 0  # or any default value you prefer
    else:
        solar_elevation = initial_solar_elevation
        solar_azimuth = initial_solar_azimuth



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

    error_on_run[closest_location] = [[haversine(intended_lat_lon, closest_location, unit=Unit.MILES),
                                       azimuth_percent_error, solar_elevation_percent_error], iteration]

 # Create an instance of the functions class
calculator = sun.functions()

if len(sys.argv) != 10:
    print("Usage: python find_position_Error.py <datetime_value> <solar_azimuth> <solar_elevation> <latitude longitude> <max_runs>")
    sys.exit(1)
    
datetime_value_str = sys.argv[1]
solar_azimuth = float(sys.argv[2])
solar_elevation = float(sys.argv[3])
latitude = float(sys.argv[4])
longitude = float(sys.argv[5])
max_runs = int(sys.argv[6])
percent_error = float(sys.argv[7])
city_name = str(sys.argv[8])
filename = str(sys.argv[9])

try:
    datetime_value = pd.Timestamp(datetime_value_str)
except ValueError:
    print("Error: Invalid datetime format. Please provide datetime in 'YYYY-MM-DD HH:MM:SS' format.")
    sys.exit(1)

intended_lat_lon = [latitude, longitude]
start_time = datetime.datetime.now()

manager = multiprocessing.Manager()
error_on_run_master = manager.dict()
date, time, hour, minute = start_time.date(), start_time.time(), start_time.hour, start_time.minute

# Set the initial solar azimuth and elevation
initial_solar_azimuth = solar_azimuth
initial_solar_elevation = solar_elevation

# Create a pool of processes
pool = multiprocessing.Pool()

for change_type in ["both", "azimuth", "elevation"]:
    # Create a new dictionary for each run with a unique name
    error_on_run = manager.dict()
    dict_name = f"error_on_run_{change_type}"
    locals()[dict_name] = error_on_run  # Store the dictionary with a unique name in locals()
    
    # Perform the iterations in parallel
    pool.starmap(process_iteration, [(i, error_on_run, change_type) for i in range(int(percent_error * -100), int(percent_error * 100))])

    
    # Merge the data from the individual dictionary into the master dictionary
    for key, value in error_on_run.items():
        error_on_run_master[key] = value


# Close the pool of processes
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

directory = f"{filename}/{city_name}"
# Create the directory if it doesn't exist
os.makedirs(directory, exist_ok=True)

for change_type in ["both", "azimuth", "elevation"]:
    # Get the corresponding error_on_run dictionary
    error_on_run = locals()[f"error_on_run_{change_type}"]
    
    # Extract values
    values = [data[0][0] for data in error_on_run.values()]
    
    # Calculate statistics
    mean_value = sum(values) / len(values)
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        median_value = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        median_value = sorted_values[n//2]
    min_value = min(values)
    max_value = max(values)
    
    # Extract x and y values
    x_values = [data[1] / 100 for data in error_on_run.values()]
    y_values = values
    
    # Create scatter plot
    plt.scatter(x_values, y_values, marker='o')
    
    # Add labels and title
    plt.xlabel('Degree Difference (Scaled by 100)')
    plt.ylabel('Distance (Miles)')
    plt.title(f'{city_name} - {change_type}\nGraph of Distance in Miles Values')
    
    # Annotate the plot with statistical values
    textstr = '\n'.join((
        f'Mean: {mean_value:.2f}',
        f'Median: {median_value:.2f}',
        f'Min: {min_value:.2f}',
        f'Max: {max_value:.2f}',
    ))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    
    # Save the plot to a file
    plt.savefig(directory + "/" + city_name + f"_{change_type}_scatter_plot.png")
    
    # Optionally, close the plot to free up memory
    plt.close()


points = error_on_run_master.keys()

try:
    # Create a Folium map centered around the average of the points
    center = [sum([p[0] for p in points]) / len(points), sum([p[1] for p in points]) / len(points)]
    
    # Create heatmap layer
    heat_layer = HeatMap(points)

    # Create marker layer for all points
    marker_cluster = MarkerCluster(name='Points')
    for point in points:
        folium.Marker(point).add_to(marker_cluster)

    # Create the map
    m = folium.Map(location=center, zoom_start=5)
    MousePosition().add_to(m)
    m.add_child(MeasureControl())
    
    folium.Marker(intended_lat_lon, 
                  tooltip=f"Intended: {intended_lat_lon} \n@ {datetime_value_str}", 
                  icon=folium.Icon(color='blue', icon='home'), 
                  popup=f"Intended: {intended_lat_lon} \n@ {datetime_value_str}").add_to(m)

    # Add heatmap layer to the map
    heat_layer.add_to(m)
    
    # Add marker cluster layer to the map
    marker_cluster.add_to(m)

    # Save the map to an HTML file
    m.save(directory + "/" + city_name + "_map" + '.html')

    # # Open the saved HTML file in the default web browser
    # webbrowser.open(directory + "/" + city_name + "_map" + '.html')

except Exception as e:
    print(f'Map unable to be generated for {city_name}: {e}')

# Write statistics to file
with open(filename + "/test_results.txt", "a") as f:
    f.write(f"\nTest started at {date}:{time}\n")
    f.write(f"Completed {max_runs} runs with with error from\n")
    f.write(f"{-percent_error} degrees error\n")
    f.write(f"to\n{percent_error} degrees error\n")
    f.write(f"Took {hours}:{minutes}:{seconds}.{milliseconds}\n")
    f.write("\nStatistics:\n")
    f.write("Distances from Intended in Miles:\n")
    f.write(f"Mean: {mean_value}\n")
    f.write(f"Median: {median_value}\n")
    f.write(f"Minimum: {min_value}\n")
    f.write(f"Maximum: {max_value}\n")
    f.write("!" * 100)
    f.write("\n\n\n")

values = [haversine(point, intended_lat_lon, unit=Unit.MILES) for point in points]

if values:
    max_value = max(values)
    bins = np.arange(0, max_value + 50, 50)
    
    plt.figure(figsize=(15, 9))
    counts, _, patches = plt.hist(values, bins=bins, edgecolor='black')
    plt.title(f'Histogram of Distances with 50-Step Bins')
    plt.xlabel('Distance from intended target in miles')
    plt.ylabel('Frequency')
    plt.xticks(bins, rotation=90, fontsize=6)
    plt.grid(True)
    # Add count labels to each bar
    for count, patch in zip(counts, patches):
        plt.text(patch.get_x() + patch.get_width() / 2, count, int(count), 
                    ha='center', va='bottom', fontsize=8)
    plt.savefig(directory + "/" + city_name + "distro_map" + '.png')
    # plt.show()
else:
    print(f"No distance values found in the file.")
