# Demo about array loop fusion with SPy

This demo is organized with 3 scripts using 3 implementations of minimal array libraries.

- `use_array1d.spy` (which uses `lib_array1d.spy`) is a minimal example (only 1d and only
  `__add__`).

- `use_array1d_simple.spy` (which uses `lib_array1d_simple.spy`) is a minimal example without
  loop fusion.

- `use_ndarray.spy` (which uses `lib_ndarray.spy`) is a more advanced example with 1d
  and 2d ndarray, `__add__` and `sin` (a transcendental function, which can be
  interesting for benchmark since C compilers do not automatically use SIMD for such
  functions even with -O3 IIUC)

To see what happens, one has to run redshift commands. Some useful commands have been
gathered in a Makefile.

The simplest way to see the loop fusion is to compare the outputs of `make rs_lib_simple`
and `make rs_lib_array1d` (with the `materialize` function).

For the lazy implementations, there is just one loop per array expression (for example
`out1: ndarray[f64] = x + x + x`).

There are of course many things that could be improved to be able to do that with nicer
code.

## TODO list before communicating on this demo

- [x] Generic struct in SPy (https://github.com/paugier/spy/tree/generic-class)

- [ ] avoid `@blue.generic` by using generic struct:

  - [ ] `nonlocal A = ndarray[DTYPE, NDIM]` syntax for generic struct & update the code

  - [ ] `__class_init__` for generic struct
    (https://github.com/spylang/spy/pull/448#issuecomment-4199438746) & update the code

- [x] Fix bug `assert w_func.w_functype.kind != "metafunc"`
  (https://github.com/spylang/spy/issues/463)

- [ ] Use metafunc methods

- [x] `hasattr` in SPy (https://github.com/spylang/spy/pull/462)

- [x] A `@force_inline` decorator to force inlining during redshifting
  (https://github.com/spylang/spy/issues/464) & update the code

- [x] `abs(1.2)` in SPy (https://github.com/spylang/spy/issues/461) & update the code

- [ ] `simplify_rs_output.py` as a rs flag (https://github.com/spylang/spy/issues/474).

- [x] Fix build (https://github.com/spylang/spy/issues/475)

### Less important

- [ ] `unroll` for blue loops

- [ ] something like `*args: Args[NDIM, i32]` for red functions

Last thing, it would be good to avoid too much repetitions (heritage, protocols?) which
would become unpractical to implement a full array library.
