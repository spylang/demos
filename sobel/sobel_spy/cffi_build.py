import os
from pathlib import Path
from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef("""
void sobel(uint8_t *frame, int32_t w, int32_t h, uint8_t *output, bool rgba);
""")

src = """
#include <stdbool.h>

#define sobel spy_sobel$sobel
void spy_sobel$sobel(uint8_t *frame, int32_t w, int32_t h, uint8_t *output, bool rgba);
"""

SPY_ROOT = Path(os.environ["SPY_ROOT"]).absolute()


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
    include_dirs=[f"{SPY_ROOT}/libspy/include"],
    library_dirs=[f"{SPY_ROOT}/libspy/build/{TARGET}/release"],
    #extra_compile_args = ['-O0', '-g'],
    extra_compile_args = ['-O3'],
)


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
