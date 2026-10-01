"""Advected particle strands: the warming.watch wind-strand look.

Renders flow as thousands of fine hair-like trails — each strand an
advected particle path, colored by a scalar (e.g. air temperature),
bright head fading to a transparent tail, on black. Strands can be
clipped to a 2D boolean mask (axes-fraction aligned) so the geography
emerges from the data itself with no visible basemap.

This module does **not** advect anything: it renders pre-computed trail
polylines. Advection belongs to ``survey-flow`` (``flow.advect``:
``ParticleSet`` with RK2/RK4, ``trail_segments()``); the caller converts
survey-flow's ``(n, L-1, 2, 2)`` lon/lat segments into axes-fraction
polylines (see ``docs/API.md`` for the exact bridge pattern). Keeping
advection out of the renderer preserves the engine's dependency-free
contract and lets survey-viz own the field sampling.

Determinism: no RNG is used anywhere here — identical inputs give
bit-identical RGBA.
"""

from typing import Optional, Sequence, Tuple, Union

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

ColormapLike = Union[str, matplotlib.colors.Colormap]

Polyline = np.ndarray  # (M, 2) float array, axes-fraction coords in [0, 1]


def _as_cmap(cmap: ColormapLike) -> matplotlib.colors.Colormap:
    if isinstance(cmap, str):
        try:
            return matplotlib.colormaps[cmap]
        except KeyError as exc:
            raise ValueError(f"unknown colormap {cmap!r}") from exc
    return cmap


def _split_nan(poly: np.ndarray) -> list:
    """Split a polyline at NaN vertices.

    Returns a list of ``(sub_polyline, start_index)`` where
    ``start_index`` is the vertex offset inside the original polyline
    (so per-point values can be sliced to match). Sub-polylines have
    at least 2 finite points.
    """
    pts = np.asarray(poly, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError(
            f"each trail must be an (M, 2) array, got shape {pts.shape}")
    finite = np.isfinite(pts).all(axis=1)
    runs, start = [], None
    for i, ok in enumerate(finite):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(pts)))
    return [(pts[a:b], a) for a, b in runs if b - a >= 2]


def _resample_mask(mask: np.ndarray, height_px: int,
                   width_px: int) -> np.ndarray:
    """Nearest-neighbor resample of a (my, mx) axes-fraction-aligned bool
    mask to (H, W) pixels. Mask row 0 is the top (y-fraction 1)."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2:
        raise ValueError(f"mask must be 2D, got shape {mask.shape}")
    my, mx = mask.shape
    # Pixel row j -> y-fraction 1 - (j+0.5)/H (y up); mask row 0 is the
    # top, so row = (1 - y_frac) * my = ((j+0.5)/H) * my.
    jj = np.clip((((np.arange(height_px) + 0.5) / height_px) * my
                  ).astype(int), 0, my - 1)
    ii = np.clip((((np.arange(width_px) + 0.5) / width_px) * mx
                  ).astype(int), 0, mx - 1)
    return mask[jj[:, None], ii[None, :]]


def render_strands(
    trails: Sequence[Polyline],
    values,
    *,
    vmin: float,
    vmax: float,
    cmap: ColormapLike = "turbo",
    width_px: int = 1080,
    height_px: int = 1920,
    dpi: int = 100,
    linewidth: float = 1.4,
    head_alpha: float = 0.8,
    tail_alpha: float = 0.04,
    mask: Optional[np.ndarray] = None,
    mask_feather: float = 0.0,
    background: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> np.ndarray:
    """Render advected particle trails as fine bright strands.

    Parameters
    ----------
    trails : sequence of (M, 2) float arrays
        Trail polylines in axes-fraction coordinates in [0, 1]; the
        **last point is the head**. Trails with fewer than 2 finite
        points are skipped; NaN vertices split a trail into sub-trails.
        Trails may extend outside [0, 1] — matplotlib clips them.
    values : (n,) array or sequence of (M,) arrays
        Scalar per trail (one value per trail) or per point (one value
        per vertex, averaged at segment midpoints). NaN values render
        transparent.
    vmin, vmax : float
        Fixed scalar range for the colormap. **Pass reel-wide fixed
        values, not per-frame data min/max**, or the reel will flicker.
    cmap : colormap name or Colormap, default ``"turbo"``.
    width_px, height_px : int
        Output resolution.
    linewidth : float
        Strand width in points (1–2 reads as hair-like at 1080x1920).
    head_alpha, tail_alpha : float
        Alpha ramp along each trail: bright head fading to near-
        transparent tail (the comet look of the reference).
    mask : (my, mx) bool array or None
        Optional clip mask, axes-fraction aligned (row 0 = top).
        ``True`` keeps strands; ``False`` erases them. Use a landmask
        for wind-over-land or an oceanmask for currents — the geography
        then emerges from the data with no basemap drawn.
    mask_feather : float, default 0.0
        Gaussian sigma in pixels applied to the clip mask edge, for the
        soft feathery mask boundary of the reference (try 2–4 px).
        ``0`` keeps a hard pixel edge. Deterministic.
    background : (r, g, b) float tuple
        Canvas color the strands composite over.

    Returns
    -------
    (H, W, 4) float64 RGBA array in [0, 1], opaque.

    Cost
    ----
    One ``LineCollection`` draw call. Benchmarked on a modest VM
    (2026-10-01): 4000 trails x 12 points at 1080x1920 renders in
    ~1.3 s — essentially the same as one LIC frame (``lic_texture``,
    540x540 grid, ``kernel=12``: ~1.3 s). Strands are drawn once per
    *data timestep*, not per animation frame, so a 30-frame daily
    reel costs ~40 s of strand rendering: viable, but the single
    most expensive preset per frame. Reduce trail count or
    ``linewidth`` to trade density for speed.
    """
    cmap_obj = _as_cmap(cmap)
    span = vmax - vmin
    if not span > 0:
        raise ValueError(f"need vmax > vmin, got vmin={vmin}, vmax={vmax}")

    trails = list(trails)
    n = len(trails)
    per_point = (
        n > 0 and not np.isscalar(values)
        and len(values) == n
        and all(hasattr(v, "__len__") for v in values)
    )
    if not per_point:
        values = np.asarray(values, dtype=float)
        if values.shape != (n,):
            raise ValueError(
                f"values must be (n,)={n} or per-point sequences, "
                f"got shape {values.shape}")

    segments: list = []
    seg_rgba: list = []

    for i, poly in enumerate(trails):
        full = np.asarray(poly, dtype=float)
        if per_point:
            pvals = np.asarray(values[i], dtype=float)
            if pvals.shape[0] != full.shape[0]:
                raise ValueError(
                    f"per-point values[{i}] has length {pvals.shape[0]} "
                    f"but trail has {full.shape[0]} points")
        for sub, a0 in _split_nan(poly):
            m = len(sub)
            vsub = pvals[a0:a0 + m] if per_point else np.full(m, float(values[i]))
            # Vectorized: one segment per consecutive pair, alpha ramping
            # tail -> head, color from the segment-midpoint scalar.
            seg_t = (vsub[:-1] + vsub[1:]) / 2.0
            finite_t = np.isfinite(seg_t)
            tnorm = np.clip((seg_t - vmin) / span, 0.0, 1.0)
            ramp = (np.arange(1, m) / (m - 1)).astype(float)
            alphas = tail_alpha + (head_alpha - tail_alpha) * ramp
            cols = cmap_obj(tnorm)  # (m-1, 4)
            cols[:, 3] = np.clip(alphas, 0.0, 1.0)
            keep = finite_t
            if keep.all():
                segments.append(np.stack([sub[:-1], sub[1:]], axis=1))
                seg_rgba.append(cols)
            elif keep.any():
                segments.append(np.stack([sub[:-1][keep], sub[1:][keep]], axis=1))
                seg_rgba.append(cols[keep])
            # all-NaN values: nothing drawn for this sub-trail

    fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor((0, 0, 0, 0))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    if segments:
        all_segs = np.concatenate(segments, axis=0)
        all_cols = np.concatenate(seg_rgba, axis=0)
        lc = LineCollection(
            all_segs, colors=all_cols, linewidths=linewidth,
            capstyle="round", joinstyle="round", antialiased=True,
            zorder=2,
        )
        ax.add_collection(lc)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba(), dtype=np.float64) / 255.0
    plt.close(fig)

    fg_rgb, fg_a = buf[..., :3], buf[..., 3:4]
    if mask is not None:
        keep = _resample_mask(mask, height_px, width_px)[..., None].astype(float)
        if mask_feather > 0:
            from scipy.ndimage import gaussian_filter
            keep = gaussian_filter(keep, sigma=(mask_feather, mask_feather, 0))
        fg_a = fg_a * keep
    bg = np.asarray(background, dtype=float).reshape(1, 1, 3)
    out_rgb = fg_rgb * fg_a + bg * (1.0 - fg_a)
    out = np.concatenate([out_rgb, np.ones_like(fg_a)], axis=2)
    return out
