# Interop — survey-aesthetics in the earthwatch-suite

`survey-aesthetics` is the **render layer** of the remote-sensing reel
stack. It sits between data and video:

```
survey-currents (data) ──▶ survey-viz (frame composition) ──▶ survey-animate (video)
                                    │ calls
                                    ▼
                           survey-aesthetics (this repo: how frames look)
                                    │
survey-cache fingerprints ◀── deterministic PNGs ──┘
```

## survey-viz (consumer, integration pending)

`survey-viz` calls this package per the contract in `docs/API.md`:
numpy fields in, dressed figures out. Concretely:

- `viz/render.py` will gain an `aesthetic=` render path that replaces its
  default pcolormesh + colorbar with `lic_texture` / `glow_from_grid` /
  `prism_frame` + the preset editorial stack.
- Coastlines flow straight through: `draw_coastlines` consumes the exact
  `[{"lons": [...], "lats": [...]}]` segment format `viz/underlay.py`
  already produces — no adapter needed.
- The `timescale_reason` / fixed-window logic in survey-viz (backed by
  survey-timescales) supplies the reel-wide `vmin`/`vmax`/`speed_max`
  this engine requires for flicker-free reels.
- `Preset` dataclasses are plain data: survey-viz can serialize the
  chosen preset into its frame manifest.

## reel-studio (consumer, integration pending)

- The three presets (`dark_flow`, `dark_glow`, `paper_prism`) become
  one-click style choices in the Studio's style step.
- Every engine parameter (`seed`, `cmap`, `sigma`, rotation angle,
  title/subtitle text, brand handle) is a plain function argument, so
  Studio can expose any of them as a control without new engine code.
- `frame_furniture(brand=...)` takes the user's page handle — Studio
  supplies it from the user's publishing profile.

## survey-cache

The determinism contract (`docs/ARCHITECTURE.md`) exists for
survey-cache: identical inputs → byte-identical PNGs → stable content
hashes. Caveat: byte-identity holds within a pinned matplotlib version;
a matplotlib upgrade changes DejaVu rasterization subtly, so cache keys
should include the renderer version on major upgrades.

## survey-flow

`survey-flow` already advects particles for flow animation; this engine's
`lic` module is complementary, not a replacement: LIC gives the static
streak *texture* per frame (the mapped.earth still-frame look), while
survey-flow gives *motion*. A future survey-viz path can composite both
(LIC texture base + advected particle overlay).

## Scaling notes

- `lic_texture` at 1080x1920 with `kernel=12` takes a few seconds per
  frame (dominated by `map_coordinates`). For batch reel renders this is
  the cost center; `kernel` trades streak length for speed.
- `prism_frame` cost scales with grid cells (one Polygon per face);
  keep render grids ≤ ~60x44 for sane frame times.
- `accumulate_glow` binning is linear in point count; `glow_from_grid`
  is linear in pixels — prefer the grid path for dense data.
- No network calls, no threads, no global state: the engine is trivially
  parallelizable across frames with `multiprocessing`.
