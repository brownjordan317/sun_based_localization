import cv2
import matplotlib
import numpy as np
import scipy.misc
from scipy import ndimage
import matplotlib.pyplot as plt


def where_is_sun(im, threshold_value):
	# Rotate to correct positions if required
	lx, ly, _ = im.shape
	if lx>ly:
		print ('Rotating')
		im = ndimage.rotate(im, -90)

	# Finding the centroid of sun position polygon
	red = im[:,:,2]
	green = im[:,:,1]
	blue = im[:,:,0]
	all_coord = np.where( red > threshold_value )
	all_coord = np.asarray(all_coord)
	length = np.shape(all_coord)[1]
	sum_x = np.sum(all_coord[0,:])
	sum_y = np.sum(all_coord[1,:])
			
	if (sum_x == 0 or sum_y == 0):
		centroid_x = np.nan
		centroid_y = np.nan
		print ('Sun is not visible in this image')
	else:
		centroid_x = int(sum_x/length)
		centroid_y = int(sum_y/length)
		print ('Sun\'s location in the image is [', str(centroid_x), ',', str(centroid_y), ']')


	return (centroid_x, centroid_y)

# Mention your sky/cloud image path here. Please make sure that your input image is inside "image" folder.
image_location = '/home/undadmin/Documents/GitHub/sun_based_localization/pull_sun_from_image/initial_images/sun16.jpg'

im = cv2.imread(image_location)
threshold_value = 250

# This is the main component that performs the computation for sun position in the image. 
(centroid_x,centroid_y) = where_is_sun(im, threshold_value)


plt.figure(1)
plt.imshow(im[:,:, [2,1,0]])
plt.scatter(x=[centroid_y], y=[centroid_x], c='r', s=40)
plt.show()

print ('Note the reference axis definition')
print ('X value = ', str(centroid_y))
print ('Y value = ', str(centroid_x))