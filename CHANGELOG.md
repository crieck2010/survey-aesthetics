# Changelog

All notable changes to `survey-aesthetics` are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).
Tags are never mutated.

## [0.3.0] - 2026-10-01

Feature 1, step 1 of the mapped.earth richness program: bivariate strand
encoding (HUE = temperature, BRIGHTNESS = speed — fast water *glows*).

### Added
- `render_strands(..., brightness=...)` — optional brightness channel on the
  strand layer. Accepts a scalar, an `(n,)` per-trail array (broadcast
  across the trail's vertices), an `(n, max_M)` per-vertex array (the
  documented per-vertex convention), or a sequence of `(M,)` arrays
  (mirroring the per-point `values` convention). The gain scales each
  segment's LUMINANCE (multiplied into the RGB after colormapping) and,
  jointly, its effective alpha — brightness 0 renders near-invisible even
  where the head/tail alpha ramp is high, on any background color.
  Finite values clip to [0, 1] (no raise); NaN renders that vertex's
  adjacent segments (or the whole trail, for per-trail NaN) fully
  transparent. `brightness=None` (default) is exactly the 0.2.0 rendering —
  all-ones brightness is byte-identical to the legacy path. No RNG:
  identical inputs give bit-identical RGBA. Interop contract: survey-viz
  will pass reel-wide-normalized speed in [0, 1] sampled at trail heads;
  normalize reel-wide, not per-frame, or the reel will flicker.

### Docs
- New README section "Bivariate strand encoding" with a short example and
  the survey-viz interop contract; full `brightness` docstring (units,
  shapes, NaN/clip semantics) plus a `Notes` section on how the gain
  multiplies against the existing head/tail alpha ramp (~b^2 response).

## [0.2.0] - 2026-10-01

Backwards compatible with 0.1.0: all four v0.1.0 demo frames render
byte-identical under 0.2.0 (verified against the `v0.1.0` tag).

### Added
- `aesthetics.strands.render_strands` — advected particle trails in the
  warming.watch manner: thousands of hair-like strands, per-trail or
  per-point scalar coloring, bright head fading to transparent tail,
  optional 2D boolean clip mask (axes-fraction aligned, row 0 = top) so
  geography emerges from the data with no basemap. No RNG — identical
  inputs give bit-identical RGBA. ~1.3 s per frame (4000 trails x 12
  points at 1080x1920), essentially the same cost as one LIC frame.
- `aesthetics.basemap.BasemapStyle` — frozen dataclass replacing the
  hardcoded `#3a3f4a` hairlines: coastline color/width/alpha + toggle,
  land fill (via optional landmask), ocean fill, background. House
  styles: `VOID_BLACK` (the v0.1.0 look), `NO_BASEMAP` (nothing drawn),
  `SUBTLE_LAND` (faint landmass under hairlines). `draw_basemap`,
  `list_basemaps`, `get_basemap`.
- `aesthetics.layout` — collision-aware furniture placement:
  `place_furniture` (priority-ordered rect packing with fallback
  alternatives, optional-drop, and required-fallback), `text_spec` /
  `box_spec` builders, `text_extent_frac` (real Agg measurement) and
  `fit_font_size` (title shrink-to-fit). Documented in `docs/LAYOUT.md`.
- `dark_strands` preset — the warming.watch bundle (turbo strands on
  black, `NO_BASEMAP`, colorbar + timeline legend layout). Presets now
  carry a `basemap` style (`dark_flow`/`dark_glow` keep `VOID_BLACK`,
  so their pixels are unchanged).
- `place_labels(..., obstacles=...)` — city labels avoid furniture rects
  (e.g. the date dial no longer sits on "Lagos"). Backwards compatible
  (default empty).

### Docs
- `docs/API.md`: the survey-viz consumer contract for the strand frame
  (survey-flow `ParticleSet`/`trail_segments` -> axes-fraction polylines
  -> `render_strands`, with the landmask pattern), basemap styles, and
  the furniture layout call pattern.
- `docs/LAYOUT.md`: the placement algorithm, suggested priorities, and
  honest limits.

### Honest limits
- Strand rendering is the most expensive preset per frame (~1.3 s at
  4000 trails); keep trail counts modest on the daily automation.
- The layout placer tests bounding rects, not glyphs; shrink reflows
  nothing and only supports left/top-anchored text.
- Text measurement is matplotlib-version-pinned (same caveat as the
  v0.1.0 byte-determinism note).

## [0.1.0] - 2026-09-30

Initial release: the aesthetic rendering engine for the earthwatch-suite
reel stack.

### Added
- `aesthetics.lic.lic_texture` — line-integral-convolution streak layer for
  `(u, v)` vector fields; hue encodes a scalar field, brightness encodes
  speed; seeded RNG; NaN renders transparent.
- `aesthetics.glow.accumulate_glow` — additive point binning with Gaussian
  core + bloom for event data on black.
- `aesthetics.glow.glow_from_grid` — same glow pipeline for pre-aggregated
  per-pixel count grids (e.g. GOES flash counts per cell).
- `aesthetics.glow.light_beam` — anisotropic glowing wedge for directional
  sources (lighthouse beams).
- `aesthetics.prism.prism_frame` — isometric 3D prism extrusion on warm
  paper; height encodes value; NaN cells show paper.
- `aesthetics.framing` — `optimal_rotation` (area-maximizing rotation for
  elongated regions), `rotated_render_size`, `rotate_frame_fill`
  (rotate + center-crop to full-bleed), `rotate_frame`, `tight_bbox`,
  `fit_extent_to_canvas`.
- `aesthetics.typography` — serif `draw_title`, letterspaced
  `draw_subtitle`, monospace `draw_readout`, rotated `draw_north_arrow`,
  and `place_labels` with greedy collision avoidance.
- `aesthetics.legends` — `gradient_bar`, `vertical_scale_bar`,
  aspect-corrected circular `date_dial`, `timeline` scrubber, `counter`
  with thin-space separators, `encoding_statement` honesty-lines.
- `aesthetics.backgrounds` — `BLACK`/`PAPER` house colors, exact-pixel
  chrome-free `new_canvas`, `draw_coastlines` (consumes the survey-viz
  underlay segment format), `fig_to_rgba`.
- `aesthetics.presets` — frozen `Preset` dataclass; `dark_flow`,
  `dark_glow`, `paper_prism` bundles; `get_preset` / `list_presets` /
  `preset_figure`.
- `aesthetics.watermark` — `draw_watermark`, `draw_copyright`,
  `draw_data_source`, and one-call `frame_furniture`. Brand is always a
  parameter, never hardcoded.
- Determinism contract: seeded RNG everywhere, bundled DejaVu fonts, Agg
  backend — identical inputs produce byte-identical PNGs (verified by
  `test_composed_frame_byte_deterministic`).
- 76 pytest tests with real assertions (no network).
- `examples/demo_reel_frames.py` — renders four sample 1080x1920 frames,
  one per preset plus a rotated frame.
- Docs: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/INTEROP.md`,
  `docs/COLOR.md`.
