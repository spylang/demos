cpdef void sobel(unsigned char[:,:,:] frame, unsigned char[:,:,:] output):
    cdef int height = frame.shape[0]
    cdef int width = frame.shape[1]
    cdef int x, y, i, j
    cdef float gx, gy, magnitude

    # Sobel kernels
    cdef int sobel_x[3][3]
    cdef int sobel_y[3][3]

    # Initialize Sobel kernels
    sobel_x[0][0] = -1; sobel_x[0][1] = 0; sobel_x[0][2] = 1
    sobel_x[1][0] = -2; sobel_x[1][1] = 0; sobel_x[1][2] = 2
    sobel_x[2][0] = -1; sobel_x[2][1] = 0; sobel_x[2][2] = 1

    sobel_y[0][0] = -1; sobel_y[0][1] = -2; sobel_y[0][2] = -1
    sobel_y[1][0] = 0;  sobel_y[1][1] = 0;  sobel_y[1][2] = 0
    sobel_y[2][0] = 1;  sobel_y[2][1] = 2;  sobel_y[2][2] = 1

    # Apply Sobel filter
    for y in range(1, height-1):
        for x in range(1, width-1):
            gx = 0
            gy = 0

            # Convert pixel to grayscale and apply kernel
            for i in range(3):
                for j in range(3):
                    # Simple grayscale conversion: average of RGB channels
                    pixel_value = (frame[y+i-1, x+j-1, 0] +
                                  frame[y+i-1, x+j-1, 1] +
                                  frame[y+i-1, x+j-1, 2]) / 3.0

                    gx += sobel_x[i][j] * pixel_value
                    gy += sobel_y[i][j] * pixel_value

            # Calculate gradient magnitude
            magnitude = (gx * gx + gy * gy) ** 0.5

            # Clamp values to 0-255 range
            if magnitude > 255:
                magnitude = 255
                if magnitude < 0:
                magnitude = 0

            output[y, x, :] = <unsigned char>magnitude

    # Set border pixels to 0
    for y in range(height):
        output[y, 0] = 0
        output[y, width-1] = 0

    for x in range(width):
        output[0, x] = 0
        output[height-1, x] = 0
