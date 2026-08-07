format:
	ruff format *.spy *.py


rs_array1d:
	spy rs --linearize use_array1d.spy | ./simplify_rs_output.py | ./spy_ruff_format.py

rs_ndarray:
	spy rs --linearize use_ndarray.spy | ./simplify_rs_output.py | ./spy_ruff_format.py

rs_simple:
	spy rs --linearize use_array1d_simple.spy | ./simplify_rs_output.py | ./spy_ruff_format.py


rs_lib_array1d:
	spy rs --linearize lib_array1d.spy | ./simplify_rs_output.py | ./spy_ruff_format.py

rs_lib_ndarray:
	spy rs --linearize lib_ndarray.spy | ./simplify_rs_output.py | ./spy_ruff_format.py

rs_lib_simple:
	spy rs --linearize lib_array1d_simple.spy | ./simplify_rs_output.py | ./spy_ruff_format.py


test_array1d:
	spy lib_array1d.spy

test_ndarray:
	spy lib_ndarray.spy

test_simple:
	spy lib_array1d_simple.spy

test_build_array1d:
	spy build -x lib_array1d.spy

test_build_ndarray:
	spy build -x lib_ndarray.spy

test_build_simple:
	spy build -x lib_array1d_simple.spy

test: test_array1d test_ndarray test_simple test_build_array1d test_build_ndarray test_build_simple


bench_spy:
	spy build --release -x bench_spy.spy

bench_numpy:
	python bench_numpy.py

bench_spy_loop:
	spy build --release -x bench_spy_loop.spy

bench_numpy_loop:
	python bench_numpy_loop.py
