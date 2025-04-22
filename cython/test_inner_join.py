import numpy as np

import pyximport; pyximport.install(setup_args={'include_dirs': np.get_include()})

from cython_inner_join import inner_join as cython_inner_join

import pytest

# From: https://github.com/pandas-dev/pandas/blob/e5898b8d33ac943a60250e1466006c073a506e8c/pandas/tests/libs/test_join.py#L118-L138

@pytest.mark.parametrize('impl_inner_join',
                         [cython_inner_join, 
                          # Put SPy version here
                          ])
def test_cython_inner_join(impl_inner_join):
    left = np.array([0, 1, 2, 1, 2, 0, 0, 1, 2, 3, 3], dtype=np.intp)
    right = np.array([1, 1, 0, 4, 2, 2, 1, 4], dtype=np.intp)
    max_group = 5

    ls, rs = impl_inner_join(left, right, max_group)

    exp_ls = left.argsort(kind="mergesort")
    exp_rs = right.argsort(kind="mergesort")

    exp_li = np.array([0, 1, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 7, 7, 8, 8])
    exp_ri = np.array([0, 0, 0, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 5, 4, 5, 4, 5])

    exp_ls = exp_ls.take(exp_li)
    exp_ls[exp_li == -1] = -1

    exp_rs = exp_rs.take(exp_ri)
    exp_rs[exp_ri == -1] = -1

    np.testing.assert_array_equal(ls, exp_ls)
    np.testing.assert_array_equal(rs, exp_rs)
