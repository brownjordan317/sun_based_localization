import sys
from PIL import Image, ImageDraw
import math 
import os

def extract_white_and_darker_pixels(input_image, output_image):
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
                for i in range(235, 252):
                    if pixel[0] >= i and pixel[1] >= i and pixel[2] >= i:
                        # Set pixel to white in output image
                        white_image.putpixel((x, y), pixel)
                        # Store coordinates of white pixel
                        white_points.append((x, y))
                        break

        # Save the output image
        white_image.save(output_image)
        print(f"White pixels and the next three darker shades extracted and saved to {output_image}")
        
        # Find the densest area of white points by segmenting the image
        if white_points:
            # Segment the image into smaller segments
            height = white_image.height
            width = white_image.width
            exponent = len(str(max(white_image.width, white_image.height)))
            exponent -= 2
            segment_size = math.floor(width / height * math.pow(10, exponent) ) # Adjust segment size as needed
            # segment_size = 100
            print(segment_size)
            print(white_image.width, white_image.height)
            print(exponent)
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
            
            # Add a red point at the center
            red_point_image = white_image.copy()
            draw = ImageDraw.Draw(red_point_image)
            radius = segment_size = math.floor(width / height * (math.pow(10, exponent) / 3) )  # Adjust the radius to control the size of the red point
            draw.ellipse([(center_x - radius, center_y - radius),
                            (center_x + radius, center_y + radius)],
                            fill=(255, 0, 0))
            del draw
            red_point_image.save(output_image)
            print(f"Red point added at the center of densest area of white points.")

            background = Image.open(input_image).convert("RGBA")
            overlay = Image.open(output_image).convert("RGBA")

            new_img = Image.blend(background, overlay, 0.5)
            file_name = os.path.basename(input_image)
            base_name = os.path.splitext(file_name)[0]
            # Create the directory if it doesn't exist
            directory = "overlayed_images"
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Save the image to the directory
            print(f"{directory}/{base_name}.png")
            new_img.save(f"{directory}/{base_name}_overlay.png", "PNG")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_image> <output_image>")
        sys.exit(1)
    
    input_image = sys.argv[1]
    output_image = sys.argv[2]

    extract_white_and_darker_pixels(input_image, output_image)
