
import math
import pandas as pd

def calc_declenation_angle(day_of_year):
        """
        Calculate the solar declination angle for a given day of the year.

        Args:
            day_of_year (int): The day of the year (1-365/366).

        Returns:
            float: The solar declination angle in degrees.
        """
        declination_angle = -23.45 * math.cos(math.radians(360 * (10 + day_of_year) / 365))
        return declination_angle

def calculate_solar_position(datetime, latitude, longitude):
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
        day_of_year = datetime.timetuple().tm_yday

        # Calculate the solar declination angle
        declination_angle = math.radians(calc_declenation_angle(day_of_year))

        # Calculate the solar hour angle
        # Local Standad Time Meridian
        LSTM = 15 * abs(0) # LSTM = 15 * UTC Difference
        # Equation of time
        B = math.radians((360/365) * (day_of_year - 81))
        EoT = 9.87*math.sin(2*B) - 7.53*math.cos(B) - 1.5*math.sin(B)
        print(EoT)
        # Time Correction Factor
        TC = 4 * (longitude - LSTM) + EoT
        print(TC)
        # Local Solar Time
        LST = ((60 * datetime.hour) + datetime.minute + TC) / 60
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

datetime_value = pd.Timestamp('2024-05-08 19:00:00')  # Example datetime
lat = 37.77
lon = -122.42

az, alt = calculate_solar_position(datetime_value, lat, lon)
print(az)
print(alt)
