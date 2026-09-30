# Color system

## Backgrounds

| Name | RGB | Use |
|---|---|---|
| `BLACK` | `(0, 0, 0)` | void: land disappears, only the phenomenon glows (`dark_flow`, `dark_glow`) |
| `PAPER` | `(0.925, 0.882, 0.780)` | warm paper for the light style (`paper_prism`) |

Custom backgrounds are allowed (`new_canvas(..., background=(r, g, b))`),
but staying inside the two house colors keeps the page's reels visually
coherent.

## Data ramps (curated per preset, not defaults)

| Preset | Default cmap | Why |
|---|---|---|
| `dark_flow` | `turbo` | perceptually ordered rainbow for temperature-like scalars; luminous on black |
| `dark_glow` | `inferno` | black → deep purple → orange → white: events burn through the ramp |
| `paper_prism` | `Blues` | single-hue translucent columns on paper; height carries the value |

Rules:

- **Fixed per reel.** `vmin`/`vmax` are chosen once for the whole reel.
  Per-frame autoscaling flickers and is treated as a bug.
- **Robust LIC normalization.** The streak texture normalizes on the
  1st/99th percentiles so a few extreme streaks can't wash the field out.
- **NaN is transparent.** Missing data never takes a ramp color.

## Text

- Titles/subtitles/readouts: white at full/85%/75% alpha on dark;
  black at the same alphas on paper (`Preset.text_color`,
  `Preset.muted_color`).
- Map labels: white, 85% alpha, small — quiet by design.
- Coastlines: `#3a3f4a` hairlines on dark (barely-there geography).

## Choosing ramps for new variables

1. Sequential data (temperature, rain, concentration): single-hue or
   perceptually-uniform multi-hue (`Blues`, `turbo`, `viridis`).
2. Event density (flashes, quakes): black-body (`inferno`, `hot`) so
   accumulation reads as heat.
3. Diverging data (anomalies): use a diverging map (`RdBu_r`) with the
   zero point pinned — never let the midpoint drift per frame.
4. Never use the default `viridis`-with-colorbar look. If a new ramp is
   needed, add it to the preset, not inline.
