import numpy as np
from pyodide.ffi import to_js, create_proxy
import _sobel_spy
from _sobel_spy import ffi

output_gray = None

# preallocate output_gray
def init(H, W):
    global output_gray
    output_gray = np.zeros((H, W), dtype=np.uint8)

def sobel_spy(buf, height, width, outbuf):
    assert output_gray is not None
    pixels = buf.reshape((height, width, 4))
    gray = np.mean(pixels[:, :, :3], axis=2, dtype=np.uint8)  # convert to grayscale

    ptr_gray = ffi.from_buffer(gray)
    ptr_output_gray = ffi.from_buffer(output_gray)
    _sobel_spy.lib.sobel(ptr_gray, width, height, ptr_output_gray)

    # convert output back to RGBA
    output = outbuf.reshape((height, width, 4))
    output[:, :, 0] = output_gray
    output[:, :, 1] = output_gray
    output[:, :, 2] = output_gray
    output[:, :, 3] = 255  # Full opacity
