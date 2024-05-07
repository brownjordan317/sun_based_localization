import math

class functions:
    def __init__(self):
        pass

    def calc_declenation_angle(self, day_of_year):
        declination_angle = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        return declination_angle

    def calculate_solar_elevation_from_shadow(self, height_of_object, length_of_shadow):
        # Ensure height_of_object and length_of_shadow are non-zero
        if height_of_object <= 0 or length_of_shadow <= 0:
            return None
        
        # Calculate the angle in radians
        angle_radians = math.atan(height_of_object / length_of_shadow)
        
        # Convert radians to degrees
        angle_degrees = math.degrees(angle_radians)
        
        # Calculate solar elevation angle
        solar_elevation = 90 - angle_degrees
        return max(0, solar_elevation)  # Ensure solar elevation is non-negative

    
    def calculate_solar_elevation_with_lat(self, latitude, day_of_year):
        # Check if latitude is within the valid range
        if latitude < -90 or latitude > 90:
            raise ValueError("Latitude must be between -90 and +90 degrees.")

        # Calculate the solar declination angle
        declination_angle = self.calc_declenation_angle(day_of_year)

        # Calculate tangent of latitude and declination angle
        tan_latitude = math.tan(math.radians(latitude))
        tan_declination = math.tan(math.radians(declination_angle))

        # Ensure that the products of tangent functions fall within the valid range
        product_tan = tan_latitude * tan_declination
        product_tan = max(-1, min(product_tan, 1))  # Clamp the value to [-1, 1]

        # Calculate solar elevation angle
        hour_angle = math.degrees(math.acos(-product_tan))
        solar_elevation = 90 - hour_angle
        # print(solar_elevation)
        return max(0, solar_elevation)  # Ensure solar elevation is non-negative

    def find_latitude_for_solar_elevations(self, day_of_year, target_elevation):
        # Define latitude range
        min_latitude = -90
        max_latitude = 90

        # Initialize variables to track closest solar elevation and corresponding latitude
        closest_solar_elevation = float('inf')
        latitude_closest_to_target = None

        # Iterate through latitudes with a step of 0.25 and calculate solar elevation
        for latitude in range(-90, 91, 1):
            solar_elevation = self.calculate_solar_elevation_with_lat(latitude, day_of_year)

            # Check if the current solar elevation is closer to the target elevation
            if abs(solar_elevation - target_elevation) < abs(closest_solar_elevation - target_elevation):
                closest_solar_elevation = solar_elevation
                latitude_closest_to_target = latitude

        return latitude_closest_to_target, closest_solar_elevation


# Sample implementation
if __name__ == "__main__":
    # Create an instance of the functions class
    calculator = functions()

    # Example value
    day_of_year = 150  # Example day of the year

    # Example usage:
    height_of_object = 10  # Height of the object in meters
    length_of_shadow = 5   # Length of the shadow in meters

    target_elevation = calculator.calculate_solar_elevation_from_shadow(height_of_object, length_of_shadow)
    print("Estimated solar elevation angle:", target_elevation, "degrees")

    # Find latitude where solar elevation is closest
    latitude, closest_elevation = calculator.find_latitude_for_solar_elevations(day_of_year, target_elevation)

    if latitude is not None:
        print(f"Latitude where solar elevation is closest: {latitude}")
        print(f"Gives solar elevation of: {closest_elevation}")
    else:
        print("Error finding nearby latitude")
