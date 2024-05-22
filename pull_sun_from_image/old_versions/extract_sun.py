import sys
from PIL import Image, ImageDraw
import math
import os
import cv2
import numpy as np

def extract_white_and_darker_pixels(input_image):
    with Image.open(input_image) as im:
        # Ensure input image is RGB
        if im.mode != "RGB":
            print("Error: Input image must be RGB.")
            sys.exit(1)

        # Create a new image with the same size and mode as input image
        white_image = Image.new("RGB", im.size)

        white_points = []  # List to store coordinates of white pixels

        # Loop through each pixel
        for x in range(im.width):
            for y in range(im.height):
                # Get pixel color
                pixel = im.getpixel((x, y))
                # Check if pixel is white or the next three darker shades
                if all(channel >= 240 for channel in pixel):
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
        print(f"White pixels and the next three darker shades extracted and saved to {output_image}")

        # Find the densest area of white points by segmenting the image
        if white_points:
            # Segment the image into smaller segments
            height = white_image.height
            width = white_image.width
            exponent = len(str(max(width, height))) - 2
            segment_size = math.floor(width / height * math.pow(10, exponent))
            segments = {}
            for point in white_points:
                segment_x = point[0] // segment_size
                segment_y = point[1] // segment_size
                segment = (segment_x, segment_y)
                if segment not in segments:
                    segments[segment] = 0
                segments[segment] += 1

            # Find the segment with the highest density of white points
            max_density_segment = max(segments, key=segments.get)

            # Calculate the center of the densest segment
            center_x = (max_density_segment[0] * segment_size) + (segment_size // 2)
            center_y = (max_density_segment[1] * segment_size) + (segment_size // 2)

        white_image_cv2 = cv2.imread(output_image)
        white_image_gray = cv2.cvtColor(white_image_cv2, cv2.COLOR_RGB2GRAY)

        kernel_size = 1  # Start with the smallest odd kernel size
        max_iterations = 50  # Maximum number of iterations
        iterations = 0
        circle_found = False

        while iterations < max_iterations:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            opening = cv2.morphologyEx(white_image_gray, cv2.MORPH_OPEN, kernel)

            # Blur the image to reduce noise
            gray_blurred = cv2.blur(opening, (3, 3))
            detected_circles = cv2.HoughCircles(
                gray_blurred, cv2.HOUGH_GRADIENT, 1.2, 20, param1=50, param2=30, minRadius=1, maxRadius=200
            )
            # cv2.imshow('Opening', opening)
            # cv2.waitKey(0)

            if detected_circles is not None:
                detected_circles = np.uint16(np.around(detected_circles))
                opening_colored = cv2.cvtColor(opening, cv2.COLOR_GRAY2BGR)
                for pt in detected_circles[0, :]:
                    a, b, r = pt[0], pt[1], pt[2]
                    cv2.circle(opening_colored, (a, b), r, (0, 255, 0), 2)
                    cv2.circle(opening_colored, (a, b), 1, (0, 0, 255), 3)

                # Save the opened image with circles to the directory
                opening_output_path = f"{directory}/{base_name}_opening_with_circle.jpg"
                cv2.imwrite(opening_output_path, opening_colored)
                print(f"Opening image with circles saved to {opening_output_path}")

                cv2.imshow("Detected Circle", opening_colored)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

                circle_found = True
                break  # Stop after finding the first circle

            kernel_size += 2  # Increment kernel size by odd numbers
            iterations += 1

        if not circle_found:
            print("No circles detected after maximum iterations.")

            # Convert the white_image (PIL Image) to a numpy array to draw on it with OpenCV
            red_point_image_np = np.array(white_image)
            # Convert back to RGB mode if necessary
            if red_point_image_np.ndim == 2:
                red_point_image_np = cv2.cvtColor(red_point_image_np, cv2.COLOR_GRAY2RGB)

            # Draw the red point on the numpy array
            radius = segment_size // 7
            cv2.circle(red_point_image_np, (center_x, center_y), radius, (255, 0, 0), -1)

            # Convert back to PIL Image
            red_point_image = Image.fromarray(red_point_image_np)
            red_point_image.save(output_image)
            print(f"Red point added at the center of densest area of white points.")

            background = Image.open(input_image).convert("RGBA")
            overlay = Image.open(output_image).convert("RGBA")
            new_img = Image.blend(background, overlay, 0.5)

            directory = "overlayed_images"
            if not os.path.exists(directory):
                os.makedirs(directory)
            new_img.save(f"{directory}/{base_name}_overlay.png", "PNG")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_image>")
        sys.exit(1)

    input_image = sys.argv[1]
    extract_white_and_darker_pixels(input_image)
