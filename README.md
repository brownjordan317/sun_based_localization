# Solar Localization Project

## Purpose

The purpose of these scripts is to derive your general location given your current UTC time, a solar azimuth, and a solar elevation. For our use case, we assume the solar azimuth will be calculated in one of two ways:

### 1. Using Angular Measurements
- Assumptions: True north can be determined.

- Method :
  - A good method to automate this process is still a work in process. A likely solution with be using gimbal measurements in conjuntion with its own shadow. In theory, if we know true north, centering the gimbal retical with the tip of its shadow should provide the solar azimuth. It would do so by taking the gimbal heading from north and adding/subtracting 180 degrees. A similar method could combine the known height of the gimbal and its angle pointed to the center of its shadow to determine eleveation with basic trig functions. While these method may work in theory, they have not been tested.
  - In place of doing this manually, the is a cite listed [here](https://gml.noaa.gov/grad/solcalc/). This is a website hosted by NOAA that provides updating solar azimuths and elevations at a select few locations

### 2. Using Shadow Angles and Object Heights
- Assumptions: True north can be determined.
- Method:
  - Measure an object height and its corresponding shadow length.
  - Measure the angle from north.


## Operation

<details>
<summary>Using a prefilled yaml</summary>

Running the main file is as simple as filling out a config.yaml and running the following within a terminal:

```
python3 main.py --config <path/to/your/config/>
```

The config file in question should be filled out in one of two ways. The two options correspond to the two methods which were previously discussed. 

### Config for running with angular measurements
```yaml
mode: angles
testname: "*.html"
datetime: "2025-01-01 00:00:00"
solar_azimuth: 12.34
solar_elevation: 12.34
gt_lat: 12.34
gt_lon: 12.34

```

### Config for running with shadow measurements
```yaml
mode: shadow
testname: "*.html"
datetime: "2025-01-01 00:00:00"
height_of_object: 12.34
length_of_shadow: 12.34
solar_azimuth: 12.34
gt_lat: 12.34
gt_lon: 12.34
```

### Yaml Arg Descriptions
#### ALL Modes
| Parameter         | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **mode**          | Either `angles` or `shadows`. Determines which functions the script runs.   |
| **datetime**      | UTC time measurements were taken, format: `YYYY-MM-dd HH:mm:ss`.            |
| **testname**      | Name for the test. Output files saved under `results\` with this name.      |
| **solar_azimuth** | Angle from north to the sun’s position in the sky.                          |
| **gt_lat**        | Ground truth latitude of the test.                                          |
| **gt_lon**        | Ground truth longitude of the test.                                         |

---

#### Angles Mode Only
| Parameter           | Description                                  |
|---------------------|----------------------------------------------|
| **solar_elevation** | Measured angle from the horizon to the sun.  |

---

#### Shadows Mode Only
| Parameter             | Description                                |
|-----------------------|--------------------------------------------|
| **height_of_object**  | Height of the object.                      |
| **length_of_shadow**  | Corresponding shadow length of the object. |

</details>

<details>
<summary>Using with a csv</summary>

This mode of running is intended primarily for testing multiple locations at once. Running the main file is as simple as filling out a locations.csv and running the following within a terminal:

```
python3 main.py --config <path/to/your/config/>
```

The config file in question should be filled out in one of two ways. The two options correspond to the two methods which were previously discussed. 

1. Manually: If desired, you can fill out a config file on your own. The config should follow the structure below:

```csv
timestamp,city,country,latitude,longitude,azimuth,elevation
2016-01-04 19:20:42,Raleigh,United States,35.7721,-78.63861,-149.33242809137204,24.91624736708923
2023-07-11 09:29:03,Eersel,Netherlands,51.3575,5.31806,125.5224702275622,50.81739594993413
2025-02-11 09:29:50,Niwai,India,26.36073,75.91836,-135.98811165935723,37.6272194811857
.
.
.
```
2. The prefered options for testing would likely be to generate this csv and not fill it out manually, this
option is accounted for. To use it, run the program with the following command:

```
python3 main.py --random <number of rows to generate>
```
This will automatically generate the csv on runtime and save it named as the time it was generated at

</details>

<details>
<summary>Additional arguments</summary>

| Parameter           | Type    | Description                                      |
|--------------------|---------|--------------------------------------------------|
| --config            | string  | Path to the YAML configuration file             |
| --random            | int     | Number of random locations to run on            |
| --skip_map          | flag    | Skip map generation                              |
| --open_map          | flag    | Open the map in a web browser                   |
| --agent_description | flag    | Print navigation description                     |
| --doe               | int     | Degrees of Error (DOE) creates a table of added error to check|
| --step              | float   | Step size for degrees of error (DOE)             |

</details>