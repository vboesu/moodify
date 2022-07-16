"""
    Python wrapper for cluster.c

    Adapted from https://github.com/numberoverzero/kmeans/
"""

import os
import ctypes
import sysconfig
import random

import numpy as np

from ctypes import c_uint64, POINTER

__all__ = ["cluster"]

# Hook up c module
HERE = os.path.dirname(os.path.realpath(__file__))
"""http://www.python.org/dev/peps/pep-3149/"""

SO_PATH = os.path.join(HERE, "cluster.so")
LIB = ctypes.CDLL(SO_PATH)


def _cluster(data, k, centers, tolerance, max_iter):
    if centers is not None:
        if k != len(centers):
            raise ValueError(f"Provided {len(centers)} centers but k is {k}")

    else:
        centers = random.choices(data, k=k)

    centers = np.array(centers)

    data_shape = data.shape
    center_shape = centers.shape

    if data_shape[0] < 1:
        raise ValueError(f"Empty data")

    if data_shape[1] != center_shape[1]:
        raise ValueError(f"Dimension of data and centers have to be the same")


    # Turn Python arrays into 1-D arrays
    data = data.flatten()
    centers = centers.flatten()

    # Get C pointers to numpy arrays
    points = data.ctypes.data_as(POINTER(c_uint64))
    centers = centers.ctypes.data_as(POINTER(c_uint64))

    # Call library
    LIB.cluster(points, data_shape[0], data_shape[1], centers, k, tolerance, max_iter)

    # Convert back to numpy
    out = np.ctypeslib.as_array(centers, shape=center_shape)
    
    # Remove last column of zeros
    out = out.T[:-1].T.astype(int)

    # Convert to tuple of tuples
    out = tuple(tuple(int(i) for i in n) for n in out)

    return out


def cluster(data, k, centers=None, tolerance=64, max_iter=32):
    return _cluster(data, k, centers=centers, tolerance=tolerance, max_iter=max_iter)


def palette_from_image(img, n=5):
    # Resize to max 256x256
    img.thumbnail((256, 256))
    img = img.convert("RGB")

    # Prepare array for clustering
    arr = np.array(img).reshape(-1, 3)
    arr = np.vstack([arr.T, np.zeros((1, arr.shape[0]))]).T.astype(np.int64)

    return cluster(arr, n)