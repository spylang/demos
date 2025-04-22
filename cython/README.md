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
SPy equivalent:
Demonstrates:
* Multi-file linking
* Array access with wraparound and bounds-checking logic. 


Note that all these Cython examples and test files are copyright their original authors with their original license.