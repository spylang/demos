# Based on: https://github.com/scikit-image/scikit-image/blob/866c8794ba86477104e8ed679f66c8e0234677f0/skimage/feature/texture.py#L15

import numpy as np

import pyximport; pyximport.install(setup_args={'include_dirs': np.get_include()})

from cython_skimage_texture import _glcm_loop as cython_glcm_loop
import pytest

def graycomatrix(impl_glcm_loop, image, distances, angles, levels=None, symmetric=False, normed=False):
    image = np.ascontiguousarray(image)

    image_max = image.max()

    if np.issubdtype(image.dtype, np.floating):
        raise ValueError(
            "Float images are not supported by graycomatrix. "
            "Convert the image to an unsigned integer type."
        )

    # for image type > 8bit, levels must be set.
    if image.dtype not in (np.uint8, np.int8) and levels is None:
        raise ValueError(
            "The levels argument is required for data types "
            "other than uint8. The resulting matrix will be at "
            "least levels ** 2 in size."
        )

    if np.issubdtype(image.dtype, np.signedinteger) and np.any(image < 0):
        raise ValueError("Negative-valued images are not supported.")

    if levels is None:
        levels = 256

    if image_max >= levels:
        raise ValueError(
            "The maximum grayscale value in the image should be "
            "smaller than the number of levels."
        )

    distances = np.ascontiguousarray(distances, dtype=np.float64)
    angles = np.ascontiguousarray(angles, dtype=np.float64)

    P = np.zeros(
        (levels, levels, len(distances), len(angles)), dtype=np.uint32, order='C'
    )

    # count co-occurences
    impl_glcm_loop(image, distances, angles, levels, P)

    # make each GLMC symmetric
    if symmetric:
        Pt = np.transpose(P, (1, 0, 2, 3))
        P = P + Pt

    # normalize each GLCM
    if normed:
        P = P.astype(np.float64)
        glcm_sums = np.sum(P, axis=(0, 1), keepdims=True)
        glcm_sums[glcm_sums == 0] = 1
        P /= glcm_sums

    return P

@pytest.fixture
def image():
    return np.array(
        [[0, 0, 1, 1], [0, 0, 1, 1], [0, 2, 2, 2], [2, 2, 3, 3]], dtype=np.uint8
    )

@pytest.mark.parametrize('impl_glcm_loop',
                         [cython_glcm_loop, 
                          # Put SPy version here
                          ])
def test_output_angles(image, impl_glcm_loop):
    result = graycomatrix(
        impl_glcm_loop,
        image, [1], [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4], 4
    )
    assert result.shape == (4, 4, 1, 4)
    expected1 = np.array(
        [[2, 2, 1, 0], [0, 2, 0, 0], [0, 0, 3, 1], [0, 0, 0, 1]], dtype=np.uint32
    )
    np.testing.assert_array_equal(result[:, :, 0, 0], expected1)
    expected2 = np.array(
        [[1, 1, 3, 0], [0, 1, 1, 0], [0, 0, 0, 2], [0, 0, 0, 0]], dtype=np.uint32
    )
    np.testing.assert_array_equal(result[:, :, 0, 1], expected2)
    expected3 = np.array(
        [[3, 0, 2, 0], [0, 2, 2, 0], [0, 0, 1, 2], [0, 0, 0, 0]], dtype=np.uint32
    )
    np.testing.assert_array_equal(result[:, :, 0, 2], expected3)
    expected4 = np.array(
        [[2, 0, 0, 0], [1, 1, 2, 0], [0, 0, 2, 1], [0, 0, 0, 0]], dtype=np.uint32
    )
    np.testing.assert_array_equal(result[:, :, 0, 3], expected4)