import os
from pathlib import Path

from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef(
    """
    void sobel(uint8_t *frame, int32_t w, int32_t h, uint8_t *output);
    """
)

src = """
void spy_sobel$sobel(uint8_t *frame, int32_t w, int32_t h, uint8_t *output);

#define sobel spy_sobel$sobel
"""

#SPY_ROOT = Path(os.environ["SPY_ROOT"]).absolute()
SPY_ROOT = '/home/antocuni/anaconda/spy'

if "PYODIDE_ABI_VERSION" in os.environ:
    # building for pyodide
    TARGET = "emscripten"
else:
    TARGET = "native"

ffibuilder.set_source(
    "_sobel_spy",
    src,
    sources=["build/sobel.c"],
    libraries=["spy"],
    define_macros=[
        (f"SPY_TARGET_{TARGET.upper()}", None),
        ("SPY_RELEASE", None),
    ],
    include_dirs=[f"{SPY_ROOT}/spy/libspy/include"],
    library_dirs=[f"{SPY_ROOT}/spy/libspy/build/{TARGET}/release"],
    #extra_compile_args = ['-O0', '-g'],
)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
