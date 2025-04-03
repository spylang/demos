import numpy as np

# Sobel kernels
sobel_x = np.array([[-1, 0, 1],
                     [-2, 0, 2],
                     [-1, 0, 1]])

sobel_y = np.array([[-1, -2, -1],
                     [ 0,  0,  0],
                     [ 1,  2,  1]])


def sobel(frame: np.ndarray, output: np.ndarray) -> np.ndarray:
    height, width, _ = frame.shape


    # Apply Sobel filter
    for y in range(1, height-1):
        for x in range(1, width-1):
            gx, gy = 0, 0

            for i in range(3):
                for j in range(3):
                    pixel_value = np.mean(frame[y+i-1, x+j-1, :])
                    gx += sobel_x[i, j] * pixel_value
                    gy += sobel_y[i, j] * pixel_value

            magnitude = np.sqrt(gx * gx + gy * gy)
            magnitude = np.clip(magnitude, 0, 255)
            output[y, x, :] = magnitude.astype(np.uint8)

    # Set border pixels to 0
    output[0, :] = 0
    output[-1, :] = 0
    output[:, 0] = 0
    output[:, -1] = 0

    return output
