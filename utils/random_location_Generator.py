import random
import pandas as pd
from datetime import datetime
import geonamescache
from utils.functions import Functions

# Initialize geonamescache
gc = geonamescache.GeonamesCache()
cities = list(gc.get_cities().values())  # list of city dicts
countries = gc.get_countries()  # dict of countrycode -> info

def random_datetime(years_back=10):
    """Generate a random datetime within the last `years_back` years."""
    year = random.randint(datetime.now().year - years_back, datetime.now().year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(year, month, day, hour, minute, second)


def random_city():
    """Return a random city name, latitude, longitude, country, and state."""
    city_info = random.choice(cities)
    city_name = city_info["name"]
    latitude = float(city_info["latitude"])
    longitude = float(city_info["longitude"])
    country_code = city_info["countrycode"]
    country_name = countries.get(country_code, {}).get("name", "")
    return city_name, latitude, longitude, country_name


def generate_test_case(calc_fn):
    """Generate one random solar test case (datetime, location, solar position)."""
    dt = random_datetime()
    city_name, latitude, longitude, country = random_city()
    ts = pd.Timestamp(dt)

    azimuth, elevation = calc_fn(ts, latitude, longitude)

    return {
        "timestamp": str(ts.strftime("%Y-%m-%d %H:%M:%S")),
        "city": city_name,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "azimuth": azimuth,
        "elevation": elevation,
    }


def random_locations(runs=5, csv_path="random_locations.csv"):
    """Generate random solar test cases and save to CSV."""
    calc_fn = Functions().calculate_solar_position
    results = []

    while len(results) < runs:
        case = generate_test_case(calc_fn)
        if case["elevation"] >= 20:
            results.append(case)

    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)
    return df


if __name__ == "__main__":
    random_locations(5)
