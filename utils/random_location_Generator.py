import math
from datetime import date, datetime
import datetime
import random
import pandas as pd
import ephem
import pytz
from timezonefinder import TimezoneFinder
from random_city_return import return_random_city

def random_locations(runs):
    tests = []

    def calc_declenation_angle(dElapsedJulianDays, day_of_year):
        """
        Calculate the solar declination angle for a given day of the year.

        Args:
            day_of_year (int): The day of the year (1-365/366).

        Returns:
            float: The solar declination angle in degrees.
        """

        dOmega = 2.1429 - 0.0010394594 * dElapsedJulianDays
        dMeanLongitude = 4.8950630 + 0.017202791698 * dElapsedJulianDays  # Radians
        dMeanAnomaly = (6.2400600 + 0.0172019699 * dElapsedJulianDays)
        dEclipticLongitude = dMeanLongitude + 0.03341607 * math.sin(dMeanAnomaly) + 0.00034894 * math.sin(2 * dMeanAnomaly) - 0.0001134 - 0.0000203 * math.sin(dOmega)
        dEclipticObliquity = 0.4090928 - 6.2140e-9 * dElapsedJulianDays + 0.0000396 * math.cos(dOmega)

        dSin_EclipticLongitude = math.sin(dEclipticLongitude)
        dY = math.cos(dEclipticObliquity) * dSin_EclipticLongitude
        dX = math.cos(dEclipticLongitude)
        dRightAscension = math.atan2(dY, dX)
        if dRightAscension < 0.0:
            dRightAscension += (2 * math.pi)
        dDeclination = math.asin(math.sin(dEclipticObliquity) * dSin_EclipticLongitude)

        declination_angle = dDeclination
        # print(declination_angle)
        # declination_angle = math.radians(23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365)))
        # print(declination_angle)
        return declination_angle

    def calculate_solar_position(date_time, latitude, longitude):
        """
        Calculate the solar azimuth and altitude angles for a given datetime, latitude, and longitude.

        Args:
            datetime (datetime): The date and time for which to calculate solar position.
            latitude (float): The latitude of the location in degrees (-90 to 90).
            longitude (float): The longitude of the location in degrees (-180 to 180).

        Returns:
            tuple: A tuple containing the solar azimuth angle (in degrees) and solar altitude angle (in degrees).
        """
        # Calculate the number of days since the start of the year
        day_of_year = date_time.timetuple().tm_yday
        year = date_time.timetuple().tm_year
        month = date_time.timetuple().tm_mon
        day = date_time.timetuple().tm_mday

        dElapsedJulianDays = (date(year, month, day) - date(2000, 1, 1)).days

        # Calculate the solar declination angle
        declination_angle = calc_declenation_angle(dElapsedJulianDays, day_of_year)

        # Calculate the solar hour angle
        # Local Standad Time Meridian
        LSTM = 15 * abs(0) # LSTM = 15 * UTC Difference
        # Equation of time
        B = math.radians((360/365) * (day_of_year - 81))
        EoT = 9.87*math.sin(2*B) - 7.53*math.cos(B) - 1.5*math.sin(B)
        # Time Correction Factor
        TC = 4 * (longitude - LSTM) + EoT
        # Local Solar Time
        LST = ((60 * date_time.hour) + date_time.minute + TC) / 60
        # Hour Angle
        hour_angle = math.radians(15 * (LST - 12))
        # hour_angle = math.radians(15 * (datetime.hour - 12) + (datetime.minute / 4) - longitude)

        latitude = math.radians(latitude)
        longitude = math.radians(longitude)
        
        
        altitude_angle = math.asin(math.sin(latitude) * math.sin(declination_angle) +
                                   math.cos(latitude) * math.cos(declination_angle) * math.cos(hour_angle))

        
        # Calculate solar azimuth angle
        azimuth_angle = math.atan2(-math.cos(declination_angle) * math.sin(hour_angle),
                                math.cos(latitude) * math.sin(declination_angle) -
                                math.sin(latitude) * math.cos(declination_angle) *
                                math.cos(hour_angle))

        # Convert angles to degrees
        altitude_deg = math.degrees(altitude_angle)
        azimuth_deg = math.degrees(azimuth_angle)

        return azimuth_deg, altitude_deg


    # Randomly generate latitude and longitude 50 times
    total = runs
    count = 1
    while total > 0:
        # noon = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        # random_offset = datetime.timedelta(hours=random.randint(-12, 12))
        # dt = noon + random_offset

        # Set the range for the year
        year = random.randint(datetime.datetime.now().year - 10, datetime.datetime.now().year)
        
        # Set the month, day, hour, minute, and second randomly
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Assume February has maximum of 28 days for simplicity
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
    
        # Create and return the datetime object
        dt = datetime.datetime(year, month, day, hour, minute, second)

        city_name, latitude, longitude = return_random_city()

        # Format the datetime
        formatted_dt = dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        
        azimuth, elevation = calculate_solar_position(pd.Timestamp(formatted_dt), latitude, longitude)
    
        if elevation >= 20:
            tests.append((pd.Timestamp(formatted_dt), azimuth, elevation, [latitude, longitude], f"Random city {city_name} at {formatted_dt}"))
            print((pd.Timestamp(formatted_dt), azimuth, elevation, [latitude, longitude], f"Random city {city_name} at {formatted_dt}"))
            print()
            total -= 1
            count += 1

    print('Targets generated\n')
    return tests

if __name__ == "__main__":
    random_locations(5)