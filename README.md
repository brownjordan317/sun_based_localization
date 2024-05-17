# Solar Localization Project

## Purpose

The purpose of these scripts is to derive your general location given your current UTC time, a solar azimuth, and a solar elevation. For our use case, we assume the solar azimuth will be calculated in one of two ways:

### 1. Using Camera Gimble Measurements
- Assumptions: True north can be determined.
- Method:
  - Point the camera true north and measure the angle in degrees it needs to turn clockwise until centered with the sun. This gives the azimuth.
  - Measure the angle the camera needs to point up until centered with the sun. This gives the solar elevation.
  - Input these numbers along with your UTC time (in the form `YYYY-MM-dd HH:mm:ss`) into `calc_sun_local_funcs.py`.

### 2. Using Shadow Angles and Object Heights
- Assumptions: True north can be determined.
- Method:
  - Measure an object height and its corresponding shadow length.
  - Measure the angle from north.0
  - Submit the UTC time (in the form `YYYY-MM-dd HH:mm:ss`) along with these measurements into `calc_sun_local_funcs.py`.

## Sub Directories

### ../Single_run_results/
- Contains the .html folium map results of running `calc_sun_local_funcs.py`.

### ../Tests/
- Contains results of running tests with multiple sets of measurements.

### ../Tests/<time_stamp>/
- Contains results of specific test runs.

### ../Tests/<time_stamp>/<city_name>/
- Contains results specific to a city.

## Files

### calc_sun_local_funcs.py
- The primary script for calculating estimated positions.
- Takes in measurements from either method to generate a best guess estimated position.
- Outputs the coordinates of the estimated position.
- If testing accuracy, input your intended latitude and longitude to compare the estimated and actual points, along with the distance between them.

### find_position_Error.py
- Iterates through runs of `calc_sun_local_funcs.py` with degrees of error in a desired range and step size.
- Example: To range 5 degrees of error with a step size of 0.5, runs would be completed for [-5, -4.75, -4.5, ..., 4.5, 4.75, 5].
- Results are placed in the `/Tests/` directory, including scatter plots (for changed azimuths, elevations, and both) and an .html folium map depicting the range of outcomes.

### random_city_return.py
- Returns a list of length `n` containing random cities in the world and their corresponding latitude and longitude.

### random_location_Generator.py
- Calculates the azimuths and elevations for a random latitude and longitude at a random UTC time and returns the corresponding information.

### run_multiple_tests.py
- Controls how many tests are run and at how many random locations.
- Outputs test results from `find_position_error.py`.

### write_stats.py
- Updates the `test_results.txt` file in `/Tests/<time_stamp>/<city_name>/` to contain information relating to the overall results of the tests run.

## Operation

### calc_sun_local_funcs.py
Args
  - Using gimble
    - `-name <name_to_save>`: (String) The name you want the result to be saved as should include .html
    - `-time <your_utc_time>`: (String) A string containing the UTC time measurements were taken at in the form `YYYY-MM-dd HH:mm:ss`
    - `-az <solar_azimuth>`: (float) The measurement of a camera gimble in degrees clockwise from true north ***Convert to negative if greater than 180***
    - `-el <solar_elevation>`: (float) The measurement of a camera gimble pointed up to the sun
    Optional
    - `-lat <intended_lat>`: (float) The expected latitude you want to compare your findings against
    - `-lon <intended_lon>`: (float) The expected longitude you want to compare your findings against

  - Using Shadows
    - `-name <name_to_save>`: (String) The name you want the result to be saved as should include .html
    - `-time <your_utc_time>`: (String) A string containing the UTC time measurements were taken at in the form `YYYY-MM-dd HH:mm:ss`
    - `-height <object_height>`: (float) The measured height of an object in any unit
    - `-shadow <shadow_length>`: (float) The measured length of a shadow in the same unit as height
    - `-az <solar_azimuth>`: (float) The measurement in degrees that a shadow points clockwise from true north ***Convert to negative if greater than 180***
    Optional
    - `-lat <intended_lat>`: (float) The expected latitude you want to compare your findings against
    - `-lon <intended_lon>`: (float) The expected longitude you want to compare your findings against

### run_multiple_tests.py
Args
  - `-locations <number_of_locations>` (int): The number of random cities that will be tested.

Optionally You Can Use the Program with the Args
  - `-fileName <to_be_tested>`: A txt file containing specific locations with each location in the form:

    ```
    ### For measurements with a gimble
    line 1: Timestamp: YYYY-MM-dd HH:mm:ss
    line 2: Azimuth: XXX.xx...
    line 3: Elevation: XXX.xx...
    line 4: Latitude: XX.xxx...
    line 5: Longitude: XXX.xxx...
    Line 6: Name: abcdefg

    ### For measurements with shadows
    line 1: Timestamp: YYYY-MM-dd HH:mm:ss
    line 2: Azimuth: XXX.xx...
    line 3: Obj Height: XX.xxx...
    line 4: Shadow Length: XX.xx...
    line 5: Latitude: XX.xxx...
    line 6: Longitude: XXX.xxx...
    Line 7: Name: abcdefg
    ```


