import sys
from PIL import Image, ImageDraw
import math
import os
import cv2
import numpy as np
from scipy.spatial import distance


def extract_white_and_darker_pixels(input_image):
    """
    Extract white and darker pixels from the input image.

    Args:
        input_image (str): The path to the input image.

    Returns:
        tuple: A tuple containing the new image with only white and darker pixels, and the path to the saved image.
    """
    with Image.open(input_image) as im:
        # Ensure input image is RGB
        if im.mode != "RGB":
            print("Error: Input image must be RGB.")
            sys.exit(1)

        # Create a new image with the same size and mode as input image
        white_image = Image.new("RGB", im.size)

        white_points = []  # List to store coordinates of white pixels

        brightest_pixel = None
        brightest_intensity = 0

        brightest_pixel = None
        brightest_intensity = 0

        # Find the brightest pixel in the input image
        for x in range(im.width):
            for y in range(im.height):
                # Get pixel color
                pixel = im.getpixel((x, y))
                # Calculate intensity as the sum of RGB values
                intensity = sum(pixel)
                # Check if current pixel is brighter than the brightest one found so far
                if intensity > brightest_intensity:
                    brightest_pixel = pixel
                    brightest_intensity = intensity

        # Loop through each pixel again to find white or slightly darker pixels
        for x in range(im.width):
            for y in range(im.height):
                # Get pixel color
                pixel = im.getpixel((x, y))
                # Check if pixel is white or the next three darker shades
                if all(channel >= brightest_pixel[i] - 5 for i, channel in enumerate(pixel)):
                    # Set pixel to white in output image
                    white_image.putpixel((x, y), pixel)
                    # Store coordinates of white pixel
                    white_points.append((x, y))


        # Create the directory if it doesn't exist
        directory = "sun_pulled_images"
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_name = os.path.basename(input_image)
        base_name = os.path.splitext(file_name)[0]
        # Save the image to the directory
        output_image = f"{directory}/{base_name}_extracted.jpg"

        # Save the output image
        white_image.save(output_image)
        print(f"White pixels and the next darker shades extracted and saved to {output_image}")

        return white_image, output_image



def apply_erosion(input_image):
    """
    Apply erosion to the input image until there is only one contour left.

    Args:
        input_image (numpy.ndarray): The input image to apply erosion to.

    Returns:
        numpy.ndarray: The final image after applying erosion.
    """
    # Initialize variables
    iterations = 0
    taken = None
    kernel_size = 3
    history = []
    num_shapes_list = []

    while True:
        # Create a structuring element with the current kernel size
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        # Apply the morphological opening operation to the image
        opening = cv2.morphologyEx(input_image, cv2.MORPH_OPEN, kernel)

        # Blur the image to reduce noise
        blur = cv2.GaussianBlur(opening, (11, 11), 0)
        # Detect edges in the image
        canny = cv2.Canny(blur, 30, 150, 3)
        # Dilate the image to make edges thicker
        dilated = cv2.dilate(canny, (1, 1), iterations=1)
            
        # Uncomment to display the image
        # cv2.imshow("opening", opening)
        # cv2.waitKey(0)

        # Check if the image is completely black
        if np.sum(dilated) == 0:
            break

        # Store the result in history
        history.append(dilated.copy())

        if taken is None:
            # Find contours in the image
            (cnt, hierarchy) = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            num_shapes_list.append(len(cnt))
            # Check if there is only one contour
            if len(cnt) <= 1:
                taken = iterations 

        # Increment kernel size by 2 (ensures odd number)
        kernel_size += 2
        iterations += 1

    # Define how many iterations back you want to go
    if len(set(num_shapes_list)) == 1:
        x_iterations_back = iterations + 1
    elif iterations:
        x_iterations_back = iterations - taken

    # Ensure we do not access out of bounds in the history list
    if x_iterations_back <= iterations:
        result_image = history[-x_iterations_back]
    else:
        # Handle the case where the requested number of iterations back is not available
        result_image = history[0] if history else np.zeros_like(input_image)



    return result_image

def detect_circles(image):
    """
    Detect circles, half-circles, and quarter-circles in the given image using Hough Circle Transform.

    Args:
        image (numpy.ndarray): The input image to detect circles in.

    Returns:
        numpy.ndarray: The image with detected circles, half-circles, and quarter-circles drawn.
        tuple: The center point of the largest detected circle (x, y).
    """
    # Convert image to grayscale if it's not already
    if len(image.shape) == 3:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = image.copy()


    # Initialize variables to keep track of the largest circle
    max_radius = 0
    max_center = None
    
    # Convert grayscale image to color (BGR) image
    color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    circles = cv2.HoughCircles(
                image, cv2.HOUGH_GRADIENT, 1.2, 20, param1=50, param2=30, minRadius=1, maxRadius=1000
            )
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            # Draw the circle
            cv2.circle(color_image, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
            print("Circle drawn at center:", circle[0], circle[1])
            
            # Check if the current circle is the largest
            if circle[2] > max_radius:
                max_radius = circle[2]
                max_center = (circle[0], circle[1])
    
    else: 
        # Threshold the grayscale image to get white or slightly darker pixels
        _, thresholded_image = cv2.threshold(gray_image, 250, 255, cv2.THRESH_BINARY)
        
        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Iterate through contours
        for contour in contours:
            # Calculate the radius of the circle using the contour area
            radius = np.sqrt(cv2.contourArea(contour) / np.pi)
            # Check if the current circle is the largest
            if radius > max_radius:
                max_radius = radius
                # Get the center of the circle by finding its bounding box
                x, y, w, h = cv2.boundingRect(contour)
                max_center = (x + w // 2, y + h // 2)
        
        # Draw the largest circle
        if max_center is not None:
            cv2.circle(color_image, max_center, int(max_radius), (0, 255, 0), 2)
            # Draw the center of the circle
            cv2.circle(color_image, max_center, 2, (0, 255, 0), 3)
            print("Largest circle drawn at center:", max_center[0], max_center[1])
    
    return color_image, max_center, max_radius


def draw_red_point_at_center_of_densest_area(circle_detected_image, output_image, center,radius):
    """
    Draw a red point at the center of the densest area of white pixels in the given image.

    Args:
        circle_detected_image (numpy.ndarray): The image where the red point will be drawn.
        output_image (str): The path to where the output image will be saved.

    Returns:
        None
    """

    if center is None:
        # Find the average x and y coordinates of all white pixels
        white_pixels = np.column_stack(np.where(circle_detected_image > 0))

        if white_pixels.size > 0:
            # Calculate the average x and y coordinates of all white pixels
            center_x = int(round(np.mean(white_pixels[:, 1])))
            center_y = int(round(np.mean(white_pixels[:, 0])))
            print(f"Average x: {center_x}, Average y: {center_y}")
        else:
            print("No white pixels found in the image.")

    else:
        center_x = center[0]
        center_y = center[1]

    # Calculate the size of each segment based on the image size
    height = circle_detected_image.shape[0]
    width = circle_detected_image.shape[1]
    exponent = len(str(max(width, height))) - 2
    segment_size = math.floor(width / height * math.pow(10, exponent))

    cv2.circle(circle_detected_image, (center_x, center_y), (math.ceil(radius * 0.05)), (0, 0, 255), -1)

    # Save the output image
    cv2.imwrite(output_image, circle_detected_image)
    print(f"Point added at the center of densest area of white points.")


def overlay_images(input_image, output_image):
    """
    Overlay the two images with 50% transparency and save the result.

    Args:
        input_image (str): The path to the background image.
        output_image (str): The path to the foreground image.

    Returns:
        None
    """
    # Open the background image
    background = Image.open(input_image).convert("RGBA")

    # Open the foreground image
    overlay = Image.open(output_image).convert("RGBA")

    # Overlay the two images with 50% transparency
    new_img = Image.blend(background, overlay, 0.5)

    # Create the directory if it doesn't exist
    directory = "overlayed_images"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the overlayed image
    new_img.save(f"{directory}/{os.path.splitext(os.path.basename(input_image))[0]}_overlay.png", "PNG")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_image>")
        sys.exit(1)

    input_image = sys.argv[1]
    white_image, output_image = extract_white_and_darker_pixels(input_image)
    eroded_image = apply_erosion(cv2.imread(output_image, cv2.IMREAD_GRAYSCALE))
    circle_detected_image, center, radius = detect_circles(eroded_image)
    cv2.imwrite('output_image_with_circles.jpg', circle_detected_image)
    draw_red_point_at_center_of_densest_area(circle_detected_image, output_image, center, math.ceil(radius))
    overlay_images(input_image, output_image)

