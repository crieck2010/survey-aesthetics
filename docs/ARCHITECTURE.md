# Architecture

`survey-aesthetics` is a **render-only** engine: numpy arrays and
parameters in, RGBA arrays and dressed matplotlib figures out. It owns no
data fetching, no scheduling, no UI, and no network calls.

```
survey-aesthetics/
  src/aesthetics/
    __init__.py      # Agg backend pin + curated public API
    lic.py           # LIC streak texture      (data layer)
    glow.py          # additive glow + bloom    (data layer)
    prism.py         # 3D prism extrusion      (data layer)
    framing.py       # rotation / zoom geometry (layout)
    backgrounds.py   # canvases + coastlines   (layout)
    typography.py    # title/subtitle/readout/labels
    legends.py       # bars, dials, timelines, counters
    watermark.py     # brand + © + data source furniture
    presets.py       # dark_flow / dark_glow / paper_prism bundles
  tests/             # 76 pytest tests, deterministic, no network
  examples/          # demo_reel_frames.py — visual verification
  docs/
```

## Layering

A frame is composed bottom-to-top:

1. **Canvas** (`backgrounds.new_canvas` or `presets.preset_figure`) —
   exact-pixel figure, axis off, background set. All drawing uses axes
   fraction coordinates in [0, 1].
2. **Data layer** — one of `lic_texture`, `accumulate_glow` /
   `glow_from_grid`, or `prism_frame`. These return RGBA numpy arrays;
   the caller composites with `ax.imshow(..., transform=ax.transAxes,
   aspect="auto")`. (`aspect="auto"` matters: the default
   `aspect="equal"` letterboxes non-square canvases.)
3. **Map dressing** — `draw_coastlines` (hairlines, never a heavy
   basemap), `place_labels`, `draw_north_arrow`.
4. **Editorial layer** — `draw_title`, `draw_subtitle`, legends,
   `encoding_statement`.
5. **Furniture** — `frame_furniture` (brand, ©, data source).

For rotated framing, steps 1–2 happen on an oversized canvas
(`rotated_render_size`), the composite is rotated
(`rotate_frame_fill`), and steps 3–5 are drawn afterwards on the final
frame so text stays upright. See `docs/API.md`.

## Key decisions

- **LIC via texture advection, not per-pixel Python loops.** The
  streamline integral is vectorized with
  `scipy.ndimage.map_coordinates`: the noise texture is advected forward
  and backward along the normalized direction field and averaged. Cost
  is ~6·kernel `map_coordinates` calls — seconds at 1080x1920, not hours.
- **Streaks are direction-normalized.** Streak length is uniform in
  pixels; *brightness* carries speed. This is the reference look: texture
  everywhere, light where the water moves.
- **Glow blurs linear energy, then colormaps.** Binning is additive and
  linear; the colormap is only the final display mapping, so dense
  regions burn through the ramp honestly and halos take the ramp's dim
  colors.
- **Prisms are hand-projected, not mplot3d.** Isometric projection with
  the painter's algorithm: deterministic, fast, no 3D toolkit quirks.
- **Fonts are DejaVu (bundled with matplotlib).** No system-font
  lottery — this is what keeps cross-machine renders identical.
- **Aspect-corrected dials.** Canvas pixels aren't square in axes
  fraction, so `date_dial` corrects by the figure aspect and draws a true
  circle via `Ellipse`.
- **Presets are frozen dataclasses.** A preset is data, not code paths:
  reel-studio can list, diff, and serialize them.

## Determinism contract

- Every stochastic input comes from `numpy.random.default_rng(seed)`
  with an explicit `seed` parameter.
- No wall-clock, no `time`, no unordered-set iteration in render paths.
- `matplotlib.use("Agg")` is pinned at package import.
- Verified by `test_composed_frame_byte_deterministic`: the full
  composed frame renders byte-identical PNGs across runs. (Across
  matplotlib versions, byte-identity is not promised — only within a
  pinned version, which is what survey-cache fingerprints assume.)
