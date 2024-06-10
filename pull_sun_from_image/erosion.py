import sys
from PIL import Image, ImageDraw
import math
import os
import cv2
import numpy as np

from PIL import Image, ImageEnhance, ImageOps
import numpy as np
from collections import Counter


def edit_image(image_path):
    """
    Edit the input image to enhance the sun's features.

    Args:
        image_path (str): The path to the input image.

    Returns:
        PIL.Image: The edited image.
    """
    # Load the input image
    image = Image.open(image_path)

    # Minimize exposure
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(0.5)  # Decrease the brightness (0.5 is an arbitrary low value)

    # Maximize contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # Increase the contrast (2.0 is an arbitrary high value)

    # Minimize saturation
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(0.0)  # Decrease the color (0.0 removes all color)

    # Maximizing shadows and highlights involves enhancing specific areas
    # Apply auto contrast to enhance shadows and highlights
    image = ImageOps.autocontrast(image)

    # Return the edited image
    return image

def extract_white_and_darker_pixels(input_image, sun_name):
    """
    Extract white and darker pixels from the input image.

    Args:
        input_image (str): The path to the input image.

    Returns:
        tuple: A tuple containing the new image with only white and darker pixels,
               the path to the saved image, and a dictionary containing each intensity
               and its frequency of occurrence.
    """
    with Image.open(input_image) as im:
        # Convert image to grayscale
        im = im.convert("L")
        intensity_values = list(im.getdata())

        # # Create a new image with the same size and mode as input image
        # white_image = Image.new("RGB", im.size)

        white_points = []  # List to store coordinates of white pixels

        brightest_intensity = max(intensity_values)

        # Calculate ratio compared to total pixels
        total_pixels = im.width * im.height

        # Calculate mean, median, and mode of intensities
        mean_intensity = np.mean(intensity_values)
        intensity_counter = Counter(intensity_values)
        # print(f"Mean intensity: {mean_intensity}")
        # print(f"Median intensity: {median_intensity}")
        # print(f"Mode intensity: {mode_intensity}")

        # Initialize a new list to store intensities with count >= 100
        high_frequency_intensities = []

        reached = 0
        # print("Intensity frequencies (sorted by intensity, cutoff after first intensity count under a threshold):")
        sorted_intensities = sorted(intensity_counter.items(), key=lambda x: x[0], reverse=True)
        for intensity, frequency in sorted_intensities:
            # print(f"Intensity: {intensity}, Frequency: {frequency}")
            if frequency > total_pixels * 0.000045:
                reached += 1
            if frequency < total_pixels * 0.000045 and reached >= 1:
                break
                # pass
            else:
                high_frequency_intensities.append(intensity)


        im_array = np.array(im)
        height, width = im_array.shape
        
        if len(high_frequency_intensities) > 255 // 2:
            sub = 5
        else:
            sub = len(high_frequency_intensities)

        threshold = brightest_intensity - sub

        # Create a mask for the pixels that should be white
        mask = im_array >= threshold

        # Create an output image array and set the white pixels
        white_image_array = np.zeros((height, width, 3), dtype=np.uint8)
        white_image_array[mask] = [255, 255, 255]

        # # Get the coordinates of white pixels
        # white_points = np.column_stack(np.where(mask))

        white_image = Image.fromarray(white_image_array, 'RGB')

        # Save the output image
        directory = f"images/sun_pulled_images/{sun_name}"
        if not os.path.exists(directory):
            os.makedirs(directory)

        output_image = f"{directory}/extracted_{os.path.splitext(os.path.basename(input_image))[0]}.jpg"
        white_image.save(output_image)
        # print(f"White pixels and the next darker shades extracted and saved to {output_image}")

        return white_image, output_image, mean_intensity

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
        dilated = cv2.dilate(canny, (3, 3), iterations=1)
            
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
            (cnt, hierarchy) = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            num_shapes_list.append(len(cnt))
            # Check if there is only one contour
            if len(cnt) <= 2:
                taken = iterations 

        # Increment kernel size by 2 (ensures odd number)
        kernel_size += 2
        iterations += 1

    # Define how many iterations back you want to go
    if len(set(num_shapes_list)) == 1:
        x_iterations_back = iterations + 1
    elif iterations:
        x_iterations_back = iterations - taken
    else:
        x_iterations_back = 0

    # Ensure we do not access out of bounds in the history list
    if x_iterations_back <= iterations:
        result_image = history[-x_iterations_back]
    else:
        # Handle the case where the requested number of iterations back is not available
        result_image = history[0] if history else np.zeros_like(input_image)

    return result_image


def detect_circles(image):
    """
    Detect circles, half-circles, and quarter-circles in the given image using Hough Circle Transform and RANSAC.

    Args:
        image (numpy.ndarray): The input image to detect circles in.

    Returns:
        numpy.ndarray: The image with detected circles, half-circles, and quarter-circles drawn.
        tuple: The center point of the largest detected circle (x, y).
        float: The radius of the largest detected circle.
    """
    # Convert to grayscale if needed
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    color_image = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)

    # Calculate the maximum distance between white pixels
    white_pixels = np.column_stack(np.where(gray_image > 250))
    if white_pixels.size > 0:
        max_distance = np.max(np.linalg.norm(white_pixels[:, None] - white_pixels, axis=2))
        mean_x = round(np.mean(white_pixels[:, 1]) if white_pixels.size > 0 else None)
        mean_y = round(np.mean(white_pixels[:, 0]) if white_pixels.size > 0 else None)
    else:
        max_distance = 0
        mean_x, mean_y = None, None

    max_radius_allowed = 5 * max_distance
    max_radius, max_center = 0, None

    # Hough Circle Transform
    circles = cv2.HoughCircles(gray_image, cv2.HOUGH_GRADIENT, 1.2, 20, param1=50, param2=30, minRadius=1, maxRadius=int(max_radius_allowed))
    if circles is not None:
        for circle in np.uint16(np.around(circles))[0, :]:
            if circle[2] <= max_radius_allowed:
                cv2.circle(color_image, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
                if circle[2] > max_radius:
                    max_radius, max_center = circle[2], (circle[0], circle[1])

    _, thresholded_image = cv2.threshold(gray_image, 250, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        radius = np.sqrt(cv2.contourArea(contour) / np.pi)
        if radius <= max_radius_allowed:
            if radius > max_radius:
                max_radius = radius
                x, y, w, h = cv2.boundingRect(contour)
                max_center = (x + w // 2, y + h // 2)
                cv2.circle(color_image, (x+w//2, y+h//2), int(radius), (255, 0, 0), 2)

    if max_radius == 0 and max_distance > 0:  # No circles found, use max distance between white pixels
        # print("No circles found, using max distance between white pixels")
        max_radius = max_distance / 2
        max_center = (mean_x, mean_y)

    if max_center:
        cv2.circle(color_image, max_center, int(max_radius), (255, 255, 0), 2)

    return color_image, max_center, max_radius

def draw_red_point_at_center_of_densest_area(circle_detected_image, output_image, center, radius):
    """
    Draw a red point at the center of the densest area of white pixels in the given image.

    Args:
        circle_detected_image (numpy.ndarray): The image where the red point will be drawn.
        output_image (str): The path to where the output image will be saved.

    Returns:
        None
    """

    center_x, center_y = center if center else (None, None)

    if center_x is None or center_y is None:
        white_pixels = np.column_stack(np.where(circle_detected_image > 0))
        center_x, center_y = tuple(map(lambda x: int(round(np.mean(x))), [white_pixels[:, 1], white_pixels[:, 0]])) if white_pixels.size > 0 else (None, None)

    if center_x is not None and center_y is not None:
        cv2.circle(circle_detected_image, (center_x, center_y), math.ceil(radius * 0.05), (0, 0, 255), -1)

    cv2.imwrite(output_image, circle_detected_image)
    # print("Point added at the center of densest area of white points.")


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
    directory = "images/overlayed_images"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the overlayed image
    new_img.save(f"{directory}/{os.path.splitext(os.path.basename(input_image))[0]}_overlay.png", "PNG")

def crop_image_around_center(image, center, radius, scale_factor=2):
    """
    Crop the image around the specified center with a given radius and a scale factor,
    replacing pixels outside the cropping boundary with black pixels.

    Args:
        image (numpy.ndarray): The input image.
        center (tuple): The center coordinates (x, y) around which to crop.
        radius (float): The radius of the circle around which to crop.
        scale_factor (float): The scaling factor for cropping. Default is 2.

    Returns:
        numpy.ndarray: The cropped image with pixels outside the boundary replaced by black pixels.
    """
    x, y = center
    height, width = image.shape[:2]  # Get the height and width of the input image
    
    # Create a black mask with the same size as the input image
    mask = np.zeros_like(image, dtype=np.uint8)
    
    # Calculate cropping coordinates within the bounds of the image
    y_min = max(0, int(y - scale_factor * radius))
    y_max = min(height, int(y + scale_factor * radius))
    x_min = max(0, int(x - scale_factor * radius))
    x_max = min(width, int(x + scale_factor * radius))
    
    # Perform cropping and replace pixels outside the boundary with black pixels in the mask
    cropped_image = image[y_min:y_max, x_min:x_max]
    mask[y_min:y_max, x_min:x_max] = cropped_image
    
    return mask


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_image>")
        sys.exit(1)

    input_image_path = sys.argv[1]

    directory = "images/edited_images"
    if not os.path.exists(directory):
        os.makedirs(directory)

    sun_name = os.path.splitext(os.path.basename(input_image_path))[0]

    edited_image = np.array(edit_image(input_image_path))
    edited_image_path = f"{directory}/edited_{sun_name}.jpg"
    cv2.imwrite(edited_image_path, edited_image)

    mean_intensity_values = []  # Store mean intensity values
    white_image, output_image, mean_intensity = extract_white_and_darker_pixels(edited_image_path, sun_name)
    mean_intensity_values.append(mean_intensity)
    
    try:
        eroded_image = apply_erosion(cv2.imread(output_image, cv2.IMREAD_GRAYSCALE))
        circle_detected_image, center, radius = detect_circles(eroded_image)
    except Exception as e:
        print(f"Error: {e}")
        circle_detected_image, center, radius = detect_circles(cv2.imread(output_image, cv2.IMREAD_GRAYSCALE))

    # cv2.imwrite('output_image_with_circles1.jpg', circle_detected_image)
    # Comment out two lines below if cropping
    draw_red_point_at_center_of_densest_area(circle_detected_image, output_image, center, math.ceil(radius))
    overlay_images(input_image_path, output_image)

    # count = 1
    # while True:
    #     cropped_image = crop_image_around_center(edited_image, center, radius)
        
    #     cropped_directory = f"images/cropped_images/{sun_name}"
    #     if not os.path.exists(cropped_directory):
    #         os.makedirs(cropped_directory)
        
    #     cropped_image_path = f'{cropped_directory}/cropped_{sun_name}_{count}.jpg'
    #     cv2.imwrite(cropped_image_path, cropped_image)
        
    #     white_image, output_image, mean_intensity = extract_white_and_darker_pixels(cropped_image_path, sun_name)
    #     mean_intensity_values.append(mean_intensity)
        
    #     if mean_intensity in mean_intensity_values[:-1] or count >= 10:  # Check if mean intensity repeats
    #         print(f"Mean intensity repeated after {count} iterations or max reached.")
    #         break
        
    #     try:
    #         eroded_image = apply_erosion(cv2.imread(output_image, cv2.IMREAD_GRAYSCALE))
    #         circle_detected_image, center, radius = detect_circles(eroded_image)
    #     except Exception as e:
    #         print(f"Error: {e}")
    #         circle_detected_image, center, radius = detect_circles(cv2.imread(output_image, cv2.IMREAD_GRAYSCALE))

    #     # cv2.imwrite(f'output_image_with_circles{count}.jpg', circle_detected_image)
    #     draw_red_point_at_center_of_densest_area(circle_detected_image, output_image, center, math.ceil(radius))
    #     overlay_images(input_image_path, output_image)
        
    #     count += 1
