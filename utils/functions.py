import math
from datetime import date

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
        # Calculate the number of days since the start of the year
        day_of_year = datetime.timetuple().tm_yday
        year = datetime.timetuple().tm_year
        month = datetime.timetuple().tm_mon
        day = datetime.timetuple().tm_mday

        dElapsedJulianDays = (date(year, month, day) - date(2000, 1, 1)).days

        # Calculate the solar declination angle
        declination_angle = self.calc_declenation_angle(dElapsedJulianDays)

        # Calculate the solar hour angle
        # Local Standad Time Meridian
        LSTM = 15 * abs(0) # LSTM = 15 * UTC Difference
        # Equation of time
        B = math.radians((360/365) * (day_of_year - 81))
        EoT = 9.87*math.sin(2*B) - 7.53*math.cos(B) - 1.5*math.sin(B)
        # Time Correction Factor
        TC = 4 * (longitude - LSTM) + EoT
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

    def find_location(self, local_datetime, solar_azimuth, solar_elevation, lat_min,
                                                                            lat_max, 
                                                                            lon_min, 
                                                                            lon_max,
                                                                            step_size):
        """
        Find the locations with the closest solar azimuth and elevation angles to the given values.

        Args:
            local_datetime (datetime): The local date and time for which to find the locations.
            solar_azimuth (float): The desired solar azimuth angle in degrees.
            solar_elevation (float): The desired solar elevation angle in degrees.

        Returns:
            list: A list of tuples containing the latitude and longitude of the closest locations.
        """
        # Convert local datetime to UTC
        utc_datetime = local_datetime.tz_localize('UTC')
        # print(utc_datetime)

        # Define a range of latitudes and longitudes
        latitudes = []  
        longitudes = []  

        # Generate latitudes
        lat = lat_min
        while lat <= lat_max:
            latitudes.append(lat)
            lat += step_size

        # Generate longitudes
        lon = lon_min
        while lon <= lon_max:
            longitudes.append(lon)
            lon += step_size


        # Initialize variables to track the closest locations and their corresponding azimuth and altitude
        closest_locations = []
        closest_azimuths = []
        closest_altitudes = []
        closest_weighted_differences = []
        max_locations = 1
        min_weighted_differences = [float('inf')] * max_locations

        # Iterate over latitudes and longitudes
        for latitude in latitudes:
            for longitude in longitudes:
                # Calculate solar position for the current UTC datetime and location
                calculated_azimuth, calculated_elevation = self.calculate_solar_position(utc_datetime, latitude, longitude)

                # Calculate the difference between calculated and provided angles
                azimuth_difference = abs(calculated_azimuth - solar_azimuth)
                elevation_difference = abs(calculated_elevation - solar_elevation)

                # Calculate the weighted difference
                weighted_difference = 1 * azimuth_difference + 1 * elevation_difference

                # Check if the current location is among the top five closest
                for i in range(max_locations):
                    if weighted_difference < min_weighted_differences[i]:
                        min_weighted_differences.insert(i, weighted_difference)
                        min_weighted_differences = min_weighted_differences[:max_locations]
                        closest_locations.insert(i, (latitude, longitude))
                        closest_azimuths.insert(i, calculated_azimuth)
                        closest_altitudes.insert(i, calculated_elevation)
                        closest_weighted_differences.insert(i, weighted_difference)
                        closest_locations = closest_locations[:max_locations]
                        closest_azimuths = closest_azimuths[:max_locations]
                        closest_altitudes = closest_altitudes[:max_locations]
                        closest_weighted_differences = closest_weighted_differences[:max_locations]

        # Print the closest locations and their corresponding azimuth and altitude
        # print(step_size)
        # for location, azimuth, altitude, weighted_difference in zip(closest_locations, closest_azimuths, closest_altitudes, closest_weighted_differences):
        #     print(f"Location: {location}, Azimuth: {azimuth:.2f}, Altitude: {altitude:.2f}, Weighted Difference: {weighted_difference:.6f}")

        return closest_locations[0]
