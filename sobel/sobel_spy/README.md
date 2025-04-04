# Build _spy_sobel for CPython

1. create a venv `spy-venv` and install spy in it, as described by
   github.com/spylang/spy

2. `. spy-venv/bin/activate`

3. `pip install cffi`

4. `export SPY_ROOT=$(python -c 'import spy; print(spy.ROOT)')`

5. `pip wheel .`


# Build _spy_sobel for pyodide

1. create a venv `spy-venv` and install spy in it, as described by
   github.com/spylang/spy

2. `. spy-venv/bin/activate`

3. Install `pyodide` into `spy-venv`: `pip install pyodide`

4. Use the `pyodide` CLI tool to create a pyodide venv:
   `pyodide venv pyodide-venv`

5. Run `./build.sh` and finger crossed

   - this first invokes `spy --cwrite sobel.spy` to generate `build/sobel.c`

   - then it called `pyodide build` to generated a CFFI bindings of it

6. `ls dist/*.wasm32.whl`
