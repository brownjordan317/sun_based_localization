import math
from datetime import date
import numpy as np

class Functions:
    def __init__(self):
        pass

    def calc_declenation_angle(self, dElapsedJulianDays): 
        """
        Calculate the solar declination angle for a given day of the year.

        Args:
            dElapsedJulianDays (float): The number of days since January 1, 2000.

        Returns:
            float: The solar declination angle in radians.
        """
        dOmega = 2.1429 - 0.0010394594 * dElapsedJulianDays
        dMeanLongitude = 4.8950630 + 0.017202791698 * dElapsedJulianDays  # Radians
        dMeanAnomaly = (6.2400600 + 0.0172019699 * dElapsedJulianDays)

        dEclipticLongitude = (
            dMeanLongitude
            + 0.03341607 * np.sin(dMeanAnomaly)
            + 0.00034894 * np.sin(2 * dMeanAnomaly)
            - 0.0001134
            - 0.0000203 * np.sin(dOmega)
        )
        dEclipticObliquity = (
            0.4090928
            - 6.2140e-9 * dElapsedJulianDays
            + 0.0000396 * np.cos(dOmega)
        )

        dSin_EclipticLongitude = np.sin(dEclipticLongitude)
        dY = np.cos(dEclipticObliquity) * dSin_EclipticLongitude
        dX = np.cos(dEclipticLongitude)
        dRightAscension = np.arctan2(dY, dX)
        dRightAscension = np.where(dRightAscension < 0, dRightAscension + 2 * np.pi, dRightAscension)
        dDeclination = np.arcsin(np.sin(dEclipticObliquity) * dSin_EclipticLongitude)

        return dDeclination

    def calculate_solar_elevation_from_shadow(self, height_of_object, length_of_shadow):
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
        return max(0, solar_elevation)  # Ensure solar elevation is non-negative
     
    def calculate_solar_position(self, datetime, latitude, longitude):
        """
        Calculate the solar azimuth and altitude angles for a given datetime, latitude, and longitude.

        Args:
            datetime (datetime): The date and time for which to calculate solar position.
            latitude (float): The latitude of the location in degrees (-90 to 90).
            longitude (float): The longitude of the location in degrees (-180 to 180).

        Returns:
            tuple: A tuple containing the solar azimuth angle (in degrees) and solar altitude angle (in degrees).
        """
        day_of_year = datetime.timetuple().tm_yday
        year = datetime.timetuple().tm_year
        month = datetime.timetuple().tm_mon
        day = datetime.timetuple().tm_mday

        dElapsedJulianDays = (date(year, month, day) - date(2000, 1, 1)).days

        # declination angle (vectorized now)
        declination_angle = self.calc_declenation_angle(dElapsedJulianDays)

        # Equation of time
        B = np.radians((360/365) * (day_of_year - 81))
        EoT = 9.87*np.sin(2*B) - 7.53*np.cos(B) - 1.5*np.sin(B)

        # Local Solar Time
        LSTM = 15 * abs(0)   # UTC offset = 0
        TC = 4 * (longitude - LSTM) + EoT
        LST = ((60 * datetime.hour) + datetime.minute + TC) / 60
        hour_angle = np.radians(15 * (LST - 12))

        # Convert lat/lon to radians
        latitude = np.radians(latitude)
        longitude = np.radians(longitude)

        # Altitude angle
        altitude_angle = np.arcsin(
            np.sin(latitude) * np.sin(declination_angle) +
            np.cos(latitude) * np.cos(declination_angle) * np.cos(hour_angle)
        )

        # Azimuth angle
        azimuth_angle = np.arctan2(
            -np.cos(declination_angle) * np.sin(hour_angle),
            np.cos(latitude) * np.sin(declination_angle) -
            np.sin(latitude) * np.cos(declination_angle) * np.cos(hour_angle)
        )

        # Convert to degrees
        altitude_deg = np.degrees(altitude_angle)
        azimuth_deg = np.degrees(azimuth_angle)

        return azimuth_deg, altitude_deg

    def find_location(self, local_datetime, solar_azimuth, solar_elevation,
                  lat_min, lat_max, lon_min, lon_max, step_size):
        """
        Find the location with the given solar azimuth and elevation.

        Args:
            local_datetime (datetime): The local datetime for which to find the location.
            solar_azimuth (float): The solar azimuth angle in degrees.
            solar_elevation (float): The solar elevation angle in degrees.
            lat_min (float): The minimum latitude to search.
            lat_max (float): The maximum latitude to search.
            lon_min (float): The minimum longitude to search.
            lon_max (float): The maximum longitude to search.
            step_size (float): The step size of the grid to search.

        Returns:
            tuple: A tuple containing the best latitude and longitude.
        """
        utc_datetime = local_datetime.tz_localize("UTC")

        # Meshgrid
        latitudes = np.arange(lat_min, lat_max + step_size, step_size)
        longitudes = np.arange(lon_min, lon_max + step_size, step_size)
        LAT, LON = np.meshgrid(latitudes, longitudes, indexing="ij")

        # Vectorized solar position
        azimuths, elevations = self.calculate_solar_position(utc_datetime, LAT, LON)

        # Weighted diff
        weighted_diff = np.abs(azimuths - solar_azimuth) + np.abs(elevations - solar_elevation)

        # Best location
        idx = np.argmin(weighted_diff)
        best_lat, best_lon = LAT.ravel()[idx], LON.ravel()[idx]

        return (best_lat, best_lon)