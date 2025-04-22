# From: https://github.com/pandas-dev/pandas/blob/e5898b8d33ac943a60250e1466006c073a506e8c/pandas/_libs/algos.pyx
cimport cython
from cython cimport Py_ssize_t

import numpy as np

from numpy cimport (
    NPY_FLOAT64,
    NPY_INT8,
    NPY_INT16,
    NPY_INT32,
    NPY_INT64,
    NPY_OBJECT,
    NPY_UINT64,
    float32_t,
    float64_t,
    int8_t,
    int16_t,
    int32_t,
    int64_t,
    intp_t,
    ndarray,
    uint8_t,
    uint16_t,
    uint32_t,
    uint64_t,
)


@cython.boundscheck(False)
@cython.wraparound(False)
def groupsort_indexer(const intp_t[:] index, Py_ssize_t ngroups):
    """
    Compute a 1-d indexer.

    The indexer is an ordering of the passed index,
    ordered by the groups.

    Parameters
    ----------
    index: np.ndarray[np.intp]
        Mappings from group -> position.
    ngroups: int64
        Number of groups.

    Returns
    -------
    ndarray[intp_t, ndim=1]
        Indexer
    ndarray[intp_t, ndim=1]
        Group Counts

    Notes
    -----
    This is a reverse of the label factorization process.
    """
    cdef:
        Py_ssize_t i, label, n
        intp_t[::1] indexer, where, counts

    counts = np.zeros(ngroups + 1, dtype=np.intp)
    n = len(index)
    indexer = np.zeros(n, dtype=np.intp)
    where = np.zeros(ngroups + 1, dtype=np.intp)

    with nogil:

        # count group sizes, location 0 for NA
        for i in range(n):
            counts[index[i] + 1] += 1

        # mark the start of each contiguous group of like-indexed data
        for i in range(1, ngroups + 1):
            where[i] = where[i - 1] + counts[i - 1]

        # this is our indexer
        for i in range(n):
            label = index[i] + 1
            indexer[where[label]] = i
            where[label] += 1

    return indexer.base, counts.base