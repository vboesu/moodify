"""
    Python wrapper for cluster.c

    Adapted from https://github.com/numberoverzero/kmeans/
"""

import os
import ctypes
import sysconfig
import random
import copy

import numpy as np

from ctypes import c_uint64, POINTER

__all__ = ["apply"]

# ====================================================
# Hook up c module
HERE = os.path.dirname(os.path.realpath(__file__))
"""http://www.python.org/dev/peps/pep-3149/"""

SO_PATH = os.path.join(HERE, "apply.so")
LIB = ctypes.CDLL(SO_PATH)
# ====================================================


def _apply(image_array, source, target):
    """
        Applies a color palette to an image

        @params:
            image_array: numpy array of RGB values
            source: list of RGB tuples
            target: list of RGB tuples
        
        @returns:
            numpy array of RGB values in original shape
    """

    if len(source) != len(target):
        raise ValueError(f"source and palette have to be of same length, received lengths {len(source)} and {len(target)}")

    shape = image_array.shape
    n_palettes = len(source)

    # convert into 1-D array
    image_array = image_array.astype(np.int64).reshape(1, -1)[0]
    source = np.array(source).astype(np.int64).reshape(1, -1)[0]
    target = np.array(target).astype(np.int64).reshape(1, -1)[0]

    n_points = len(image_array)

    # Turn Python arrays into C arrays
    image = image_array.ctypes.data_as(POINTER(c_uint64))
    source = source.ctypes.data_as(POINTER(c_uint64))
    target = target.ctypes.data_as(POINTER(c_uint64))

    # Call library
    LIB.apply(image, source, target, n_points, 3, n_palettes)

    out = np.ctypeslib.as_array(image, shape=shape)
    out = out.astype(np.uint8)

    return out


def apply(image_array, source, target):
    return _apply(image_array, source, target)