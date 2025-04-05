export SPY_ROOT=$(python -c 'import spy; print(spy.ROOT)')

rm -rf build
rm -f _sobel_spy.c
rm -f _sobel_spy.*.so
spy --cwrite sobel.spy || exit
./pyodide-venv/bin/pyodide build .
