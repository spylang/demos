rm -rf build
rm -f _sobel_spy.c
rm -f _sobel_spy.*.so
~/anaconda/spy/venv/bin/spy --cwrite sobel.spy && python cffi_build.py
