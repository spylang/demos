# From: https://github.com/pandas-dev/pandas/blob/e5898b8d33ac943a60250e1466006c073a506e8c/pandas/_libs/join.pyx#L24

cimport cython
from cython cimport Py_ssize_t
import numpy as np

cimport numpy as cnp
from numpy cimport (
    int64_t,
    intp_t,
    ndarray,
)

cnp.import_array()

from cython_group_sort_indexer import groupsort_indexer

@cython.wraparound(False)
@cython.boundscheck(False)
def inner_join(const intp_t[:] left, const intp_t[:] right,
               Py_ssize_t max_groups, bint sort=True):
    cdef:
        Py_ssize_t i, j, k, count = 0
        intp_t[::1] left_sorter, right_sorter
        intp_t[::1] left_count, right_count
        intp_t[::1] left_indexer, right_indexer
        intp_t lc, rc
        Py_ssize_t left_pos = 0, right_pos = 0, position = 0
        Py_ssize_t offset

    left_sorter, left_count = groupsort_indexer(left, max_groups)
    right_sorter, right_count = groupsort_indexer(right, max_groups)

    with nogil:
        # First pass, determine size of result set, do not use the NA group
        for i in range(1, max_groups + 1):
            lc = left_count[i]
            rc = right_count[i]

            if rc > 0 and lc > 0:
                count += lc * rc

    left_indexer = np.empty(count, dtype=np.intp)
    right_indexer = np.empty(count, dtype=np.intp)

    with nogil:
        # exclude the NA group
        left_pos = left_count[0]
        right_pos = right_count[0]
        for i in range(1, max_groups + 1):
            lc = left_count[i]
            rc = right_count[i]

            if rc > 0 and lc > 0:
                for j in range(lc):
                    offset = position + j * rc
                    for k in range(rc):
                        left_indexer[offset + k] = left_pos + j
                        right_indexer[offset + k] = right_pos + k
                position += lc * rc
            left_pos += lc
            right_pos += rc

        # Will overwrite left/right indexer with the result
        _get_result_indexer(left_sorter, left_indexer)
        _get_result_indexer(right_sorter, right_indexer)

    if not sort:
        # if not asked to sort, revert to original order
        if len(left) == len(left_indexer):
            # no multiple matches for any row on the left
            # this is a short-cut to avoid groupsort_indexer
            # otherwise, the `else` path also works in this case
            rev = np.empty(len(left), dtype=np.intp)
            rev.put(np.asarray(left_sorter), np.arange(len(left)))
        else:
            rev, _ = groupsort_indexer(left_indexer, len(left))

        return np.asarray(left_indexer).take(rev), np.asarray(right_indexer).take(rev)
    else:
        return np.asarray(left_indexer), np.asarray(right_indexer)


@cython.wraparound(False)
@cython.boundscheck(False)
cdef void _get_result_indexer(
    const intp_t[::1] sorter,
    intp_t[::1] indexer,
) noexcept nogil:
    """NOTE: overwrites indexer with the result to avoid allocating another array"""
    cdef:
        Py_ssize_t i, n, idx

    if len(sorter) > 0:
        # cython-only equivalent to
        #  `res = algos.take_nd(sorter, indexer, fill_value=-1)`
        n = indexer.shape[0]
        for i in range(n):
            idx = indexer[i]
            if idx == -1:
                indexer[i] = -1
            else:
                indexer[i] = sorter[idx]
    else:
        # length-0 case
        indexer[:] = -1
