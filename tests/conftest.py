"""Shared fixtures: deterministic synthetic fields."""

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest


@pytest.fixture()
def uv_scalar():
    """Small synthetic (u, v, scalar) grids with a known NaN hole."""
    rng = np.random.default_rng(42)
    ny, nx = 48, 64
    y, x = np.mgrid[0:ny, 0:nx].astype(float)
    u = np.sin(x / 8.0) * 2.0
    v = np.cos(y / 10.0) * 1.5
    scalar = 10.0 + 0.1 * x + 0.05 * y
    u[5:10, 5:10] = np.nan  # honest data gap
    v[5:10, 5:10] = np.nan
    scalar[5:10, 5:10] = np.nan
    return u, v, scalar


@pytest.fixture()
def glow_points():
    rng = np.random.default_rng(7)
    n = 60
    xs = rng.uniform(20, 100, n)
    ys = rng.uniform(20, 160, n)
    vals = rng.uniform(1, 10, n)
    return xs, ys, vals
