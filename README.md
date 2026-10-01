# survey-aesthetics

The aesthetic rendering engine for the earthwatch-suite remote-sensing reel stack — the module that makes automatically generated reels look like mapped.earth frames **without any manual styling**.

`survey-aesthetics` is a pure-Python, UI-free library (numpy + matplotlib + scipy + pillow). It provides the render layers, typography, legends, framing, and preset bundles that [survey-viz](https://github.com/crieck2010/survey-viz) calls when drawing a frame, and that [reel-studio](https://github.com/crieck2010/reel-studio) will expose as one-click style choices. It never fetches data and never touches the network.

## What it does

| Layer | Module | The look |
|---|---|---|
| LIC flow streaks | `aesthetics.lic` | line-integral-convolution texture for `(u, v)` fields; **hue = scalar** (e.g. water temperature), **brightness = speed** |
| Additive glow + bloom | `aesthetics.glow` | event accumulation on black (lightning flashes, quake energy); `light_beam` for directional sources |
| 3D prism extrusion | `aesthetics.prism` | value rendered as physical height on warm paper |
| Rotated auto-fit framing | `aesthetics.framing` | rotate the map to maximize zoom for elongated regions (the Lake Ontario move), with honest rotated north arrows |
| Editorial typography | `aesthetics.typography` | serif display titles, letterspaced subtitles, monospace data readouts, collision-avoided dot-marker labels |
| Custom legends | `aesthetics.legends` | gradient bars, vertical scale bars, circular date dials, timeline scrubbers, running counters, encoding honesty-lines — never a default colorbar |
| Particle strands | `aesthetics.strands` | advected particle trails (warming.watch look); per-trail/point coloring, head→tail fade, mask clipping |
| Basemap styles | `aesthetics.basemap` | styled coastline/land/ocean/background treatments carried by each preset |
| Furniture layout | `aesthetics.layout` | collision-aware placement, title shrink-to-fit, real glyph measurement |
| Backgrounds | `aesthetics.backgrounds` | pure-black void and warm paper; chrome-free exact-pixel canvases; hairline coastlines |
| Presets | `aesthetics.presets` | `dark_flow`, `dark_glow`, `dark_strands`, `paper_prism` one-choice bundles |
| Watermark furniture | `aesthetics.watermark` | brand mark + © line + data-source footer in consistent placement |

Every public function is **deterministic**: same inputs + same seed → byte-identical output, so [survey-cache](https://github.com/crieck2010/survey-cache) fingerprints stay stable across every frame of a reel.

## Install

```bash
pip install survey-aesthetics
```

Requires Python ≥ 3.9 and (installed automatically) `numpy`, `matplotlib`, `scipy`, `pillow`.

## Quickstart

```python
from datetime import datetime
from aesthetics import (
    preset_figure, lic_texture, draw_title, draw_subtitle,
    gradient_bar, timeline, frame_furniture, fig_to_rgba,
)
from aesthetics.backgrounds import close

# 1. Canvas for the preset (1080x1920, black, zero chrome)
fig, ax, preset = preset_figure("dark_flow")

# 2. Data layer: LIC streaks, hue = temperature, brightness = speed.
#    vmin/vmax/speed_max are FIXED for the whole reel — never per-frame,
#    or the reel flickers.
tex = lic_texture(u, v, temperature, vmin=51.0, vmax=72.0,
                  cmap=preset.cmap, seed=7, speed_max=3.0)
ax.imshow(tex, extent=[0, 1, 0, 1], origin="upper",
          transform=ax.transAxes, aspect="auto", zorder=2)

# 3. Editorial layer.
lay = preset.legend_layout
draw_title(ax, "Lake Ontario", *lay["title"], size=64, color="white")
draw_subtitle(ax, "A Week of Currents", *lay["subtitle"], size=26, color="white")
gradient_bar(ax, lay["gradient_bar"], preset.cmap, 51.0, 72.0,
             label="water temperature", unit="°F")
timeline(ax, lay["timeline"], t_start, t_end, t_now)
frame_furniture(ax, brand="my-ocean-page", holder="Your Name", year=2026,
                data_source="NOAA GLOFS MODEL (LOOFS)\n16-23 SEPTEMBER 2026",
                encoding=preset.encoding)

rgba = fig_to_rgba(fig)   # (1920, 1080, 4) float array in [0, 1]
close(fig)
```

Rotated framing (elongated regions):

```python
from aesthetics.framing import optimal_rotation, rotated_render_size, rotate_frame_fill

angle = optimal_rotation(lon0, lon1, lat0, lat1, canvas_wh=(1080, 1920))
rw, rh = rotated_render_size(angle, (1080, 1920))
fig, ax = new_canvas(rw, rh, background="black")
# ... draw the north-up map ...
rgba = rotate_frame_fill(fig_to_rgba(fig), angle, (1080, 1920))  # full-bleed
# ... then draw titles/legends/furniture (unrotated) on the final frame ...
```

See `examples/demo_reel_frames.py` — it renders four sample frames
(`dark_flow`, `dark_glow`, `paper_prism`, rotated) and is the visual
verification script:

```bash
python examples/demo_reel_frames.py --outdir /tmp/aes_demo
```

## API overview

```python
# Render layers (numpy in, RGBA out)
lic_texture(u, v, scalar, *, vmin, vmax, cmap="turbo", seed=0, speed_max=None, ...)
accumulate_glow(xs, ys, values, shape, *, vmax, cmap="inferno", sigma=5.0, bloom_sigma=22.0, ...)
glow_from_grid(grid, *, vmax, ...)          # pre-aggregated counts per pixel
light_beam(shape, x, y, angle_deg, length_px, width_px, *, color=..., intensity=1.0)
prism_frame(values, *, vmin, vmax, cmap="Blues", width_px=1080, height_px=1920, ...)

# Framing
optimal_rotation(lon0, lon1, lat0, lat1, *, canvas_wh=(1080, 1920)) -> float
rotated_render_size(angle_deg, canvas_wh=(1080, 1920)) -> (w, h)
rotate_frame_fill(rgba, angle_deg, canvas_wh=(1080, 1920)) -> rgba   # rotate + center-crop
rotate_frame(rgba, angle_deg) -> rgba                                # same-size rotation
tight_bbox(lons, lats, mask, *, pad_frac=0.04) -> (lon0, lon1, lat0, lat1)
fit_extent_to_canvas(bbox, canvas_wh) -> bbox

# Typography & legends & furniture (all draw onto a chrome-free axes)
draw_title / draw_subtitle / draw_readout / draw_north_arrow / place_labels  # place_labels(..., obstacles=[...])
gradient_bar / vertical_scale_bar / date_dial / timeline / counter / encoding_statement
draw_watermark / draw_copyright / draw_data_source / frame_furniture

# Strands, basemaps, layout
render_strands(trails, values, vmin=..., vmax=..., mask=...) -> (H, W, 4) RGBA
draw_basemap(ax, segments, style)  # style: VOID_BLACK | NO_BASEMAP | SUBTLE_LAND
place_furniture(specs, pad=0.012)  # text_spec / box_spec builders; see docs/LAYOUT.md

# Presets
list_presets() -> ["dark_flow", "dark_glow", "dark_strands", "paper_prism"]
get_preset(name) -> Preset
preset_figure(name, width_px=1080, height_px=1920) -> (fig, ax, preset)
```

Full signatures and the survey-viz call pattern: `docs/API.md`.

## Design rules (the mapped.earth system this encodes)

1. **Zero chrome** — no axes, ticks, tick labels, or gridlines. Ever.
2. **Fixed scales** — `vmin`/`vmax`/`speed_max` are chosen once per reel. Per-frame rescaling flickers and is a bug.
3. **Every encoding stated in words** — `BRIGHTNESS = SPEED`, `Height is millimetres per day. Nothing else is encoded.`
4. **Deterministic** — seeded RNG, bundled DejaVu fonts, Agg backend. Byte-identical frames for identical inputs.
5. **Honest gaps** — NaN renders as transparent/background, never invented data.
6. **No hardcoded brands** — the watermark takes the user's handle as a parameter.

## Docs

- `docs/ARCHITECTURE.md` — module map and design decisions
- `docs/API.md` — exact call pattern for survey-viz (the consumer contract)
- `docs/INTEROP.md` — how this fits the earthwatch-suite (survey-viz, reel-studio, survey-cache, survey-flow)
- `docs/COLOR.md` — the color system: backgrounds, ramps, text

## Tests

```bash
pip install -e ".[dev]"
pytest            # 76 tests, all deterministic (no network)
```

## Changelog

See `CHANGELOG.md`. Versioning is semantic; tags are never mutated.

## License

MIT — see `LICENSE`.
