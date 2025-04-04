import numpy as np
from pyodide.ffi import to_js, create_proxy
from js import Uint8ClampedArray, ImageData

def sobel_np(img_data):
    # Convert JS ImageData to numpy array
    width = img_data.width
    height = img_data.height
    data = np.array(img_data.data)
    pixels = data.reshape((height, width, 4))

    # Create output array
    output = np.zeros_like(pixels)

    # Convert to grayscale for processing
    gray = np.mean(pixels[:, :, :3], axis=2)

    # Sobel kernels
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    # Apply Sobel operator
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Extract 3x3 neighborhood
            neighborhood = gray[y-1:y+2, x-1:x+2]

            # Calculate gradients
            gx = np.sum(neighborhood * kernel_x)
            gy = np.sum(neighborhood * kernel_y)

            # Calculate magnitude
            magnitude = np.sqrt(gx**2 + gy**2)
            normalized = min(255, magnitude)

            # Set RGB channels to the same value
            output[y, x, 0] = normalized
            output[y, x, 1] = normalized
            output[y, x, 2] = normalized
            output[y, x, 3] = 255

    # Flatten the array and create a new ImageData object
    flat_output = output.flatten().astype(np.uint8)
    js_array = Uint8ClampedArray.new(to_js(flat_output))
    return ImageData.new(js_array, width, height)
