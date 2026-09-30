# Changelog

All notable changes to `survey-aesthetics` are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).
Tags are never mutated.

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
