import numpy as np
from pyodide.ffi import to_js, create_proxy


def init(H, W):
    pass

def sobel_np(buf, height, width, outbuf):
    pixels = buf.reshape((height, width, 4))  # RGBA
    apply_sobel(pixels, height, width, outbuf)

def apply_sobel(pixels, height, width, output):
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            # Extract 3x3 neighborhood for each RGB channel
            gx_total = 0.0
            gy_total = 0.0
            #for c in range(3):  # R, G, B
            for c in (1,): # G
                neighborhood = pixels[y-1:y+2, x-1:x+2, c]
                gx = np.sum(neighborhood * kernel_x)
                gy = np.sum(neighborhood * kernel_y)
                gx_total += gx ** 2
                gy_total += gy ** 2

            magnitude = np.sqrt(gx_total + gy_total)
            normalized = min(255, magnitude)

            # Write result as grayscale to output
            output[y, x, 0] = normalized
            output[y, x, 1] = normalized
            output[y, x, 2] = normalized
            output[y, x, 3] = 255
