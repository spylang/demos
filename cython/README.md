# Cython Examples

This directory contains examples of real Cython code used in other popular
Python packages.  The equivalent SPy code will (eventually) be found in the
file with the same name, but a `.spy` extension.  A pytest driver that runs
both the Cython and SPy files will have the pattern `test_[FILENAME].py`.

## Scikit-Learn

Test scenario: Specialized IntFloatDict class.

Cython: [cython_fast_dict.pyx](https://github.com/scikit-learn/scikit-learn/blob/af7df5ced0eb1124df12dd389cc4ef7a9042837e/sklearn/utils/_fast_dict.pyx)
SPy: *TBD*
Demonstrates:
* Building a fast container class for use from Python
* Passing arrays

## Pandas

Test scenario: Inner join.

Cython:
  * [cython_inner_join.pyx](https://github.com/pandas-dev/pandas/blob/e5898b8d33ac943a60250e1466006c073a506e8c/pandas/_libs/join.pyx)
  * [cython_group_sort_indexer.pyx](https://github.com/pandas-dev/pandas/blob/e5898b8d33ac943a60250e1466006c073a506e8c/pandas/_libs/algos.pyx)
)
SPy: *TBD*
Demonstrates:
* Multi-file linking
* Array access with wraparound and bounds-checking logic. 

## Scikit-image

Test scenario: Non-trivial array calculation used in larger algorithm.

Cython:
  * [cython_skimage_texture.pyx](https://github.com/scikit-image/scikit-image/blob/866c8794ba86477104e8ed679f66c8e0234677f0/skimage/feature/_texture.pyx
  )
    - Also includes [fused type definitions](https://github.com/scikit-image/scikit-image/blob/866c8794ba86477104e8ed679f66c8e0234677f0/skimage/_shared/fused_numerics.pxd) and a [custom definition of the round() function](https://github.com/scikit-image/scikit-image/blob/866c8794ba86477104e8ed679f66c8e0234677f0/skimage/_shared/interpolation.pxd#L25-L28).
SPy: *TBD*
Demonstrates:
* Complex array algorithm.
* Use of [fused types](https://cython.readthedocs.io/en/stable/src/userguide/fusedtypes.html) to automatically generate multiple specialized signatures of the same function.  (Similar to a C++ template function.)

## SciPy

Test scenario: Implementation of vector quantization, originally ported from C to Cython.

Cython:
  * [cython_vq.pyx](https://github.com/scipy/scipy/blob/7ecbcb8c2ebcbb8c87d2fc98a98bbc9f7e34f497/scipy/cluster/_vq.pyx#L5)
SPy: *TBD*
Demonstrates:
* Heavy use of fused-type templating across many internal functions.
* External C calls to BLAS functions.
* NumPy array allocation.

Note that all these Cython examples and test files are copyright their original authors with their original license.