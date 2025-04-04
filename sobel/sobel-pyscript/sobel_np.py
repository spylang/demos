import numpy as np
from pyodide.ffi import to_js, create_proxy

# preallocate output_gray
output_gray = np.zeros((120, 160), dtype=np.uint8)


def sobel_np(buf, height, width, outbuf):
    pixels = buf.reshape((height, width, 4))
    gray = np.mean(pixels[:, :, :3], axis=2)  # convert to grayscale

    #apply_sobel(gray, height, width, output_gray)
    output_gray[:] = gray  # fake apply

    # convert output back to RGBA
    output = outbuf.reshape((height, width, 4))
    output[:, :, 0] = output_gray
    output[:, :, 1] = output_gray
    output[:, :, 2] = output_gray
    output[:, :, 3] = 255  # Full opacity


def apply_sobel(gray, height, width, output):
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

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

            output[y, x] = normalized
            ## # Set RGB channels to the same value
            ## output[y, x, 0] = normalized
            ## output[y, x, 1] = normalized
            ## output[y, x, 2] = normalized
            ## output[y, x, 3] = 255
