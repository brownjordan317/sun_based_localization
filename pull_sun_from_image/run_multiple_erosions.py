import os
import subprocess
import time

# Directory containing the images
image_dir = 'initial_images'

# Iterate over each file in the directory
for filename in os.listdir(image_dir):
    # Construct the full file path
    filepath = os.path.join(image_dir, filename)
    
    # Print the path of the file being processed
    print(f"Processing {filepath}")
    
    start_time = time.time()

    # Run the erosion.py script for the image
    result = subprocess.run(['python3', 'erosion.py', filepath], capture_output=True, text=True)

    end_time = time.time()

    # Print the elapsed time
    print(f"Elapsed time: {end_time - start_time} seconds")
    
    # Print the output of the erosion.py script
    print(f"Output for {filepath}:")
    print(result.stdout)
    if result.stderr:
        print(f"Error for {filepath}:")
        print(result.stderr)
