import numpy as np
from pyodide.ffi import to_js, create_proxy
import _sobel_spy
from _sobel_spy import ffi

def init(H, W):
    pass

def sobel_spy(in_buf, height, width, out_buf):
    rgba = True
    ptr_in_buf = ffi.from_buffer(in_buf)
    ptr_out_buf = ffi.from_buffer(out_buf)
    _sobel_spy.lib.sobel(ptr_in_buf, width, height, ptr_out_buf, rgba)
