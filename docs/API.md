# API — the survey-viz consumer contract

This document is the exact call pattern `survey-viz` should use. It is
written against `survey-aesthetics` 0.1.0; breaking changes will bump the
minor version and be noted in `CHANGELOG.md`.

## Dark flow frame (currents / wind)

```python
from datetime import datetime
from aesthetics import (
    preset_figure, lic_texture, draw_title, draw_subtitle, draw_readout,
    gradient_bar, timeline, place_labels, draw_north_arrow,
    draw_coastlines, frame_furniture, fig_to_rgba,
)
from aesthetics.backgrounds import close

fig, ax, preset = preset_figure("dark_flow", 1080, 1920)  # or ("dark_flow", w, h)

# --- data layer -------------------------------------------------------
# u, v, scalar: 2D numpy arrays, identical shape, in map projection order.
# NaN = missing (renders transparent). vmin/vmax/speed_max are REEL-WIDE
# fixed values — never per-frame data min/max (that flickers).
tex = lic_texture(
    u, v, scalar,
    vmin=SEA_TEMP_MIN, vmax=SEA_TEMP_MAX,   # fixed for the whole reel
    cmap=preset.cmap,                       # "turbo" for dark_flow
    seed=7,                                 # fixed for the whole reel
    speed_max=SPEED_MAX,                    # fixed for the whole reel
)
# NOTE: aspect="auto" is required with transform=ax.transAxes on non-square
# canvases; the imshow default ("equal") letterboxes.
ax.imshow(tex, extent=[lon0, lon1, lat0, lat1], origin="upper", zorder=2)
# ...or extent=[0, 1, 0, 1], transform=ax.transAxes for pre-projected arrays.

# --- map dressing ------------------------------------------------------
draw_coastlines(ax, coastline_segments, color="#3a3f4a", linewidth=0.8)  # survey-viz underlay format
place_labels(ax, [{"x": lon, "y": lat, "text": "HALIFAX", "priority": 5}, ...])
draw_north_arrow(ax, 0.06, 0.80, angle_deg=rotation)

# --- editorial ----------------------------------------------------------
lay = preset.legend_layout
draw_title(ax, title, *lay["title"], size=preset.title_size, color="white")
draw_subtitle(ax, window_label, *lay["subtitle"], size=preset.subtitle_size, color="white")
gradient_bar(ax, lay["gradient_bar"], preset.cmap, SEA_TEMP_MIN, SEA_TEMP_MAX,
             label="water temperature", unit="°F")
timeline(ax, lay["timeline"], t_start, t_end, t_now)
frame_furniture(ax, brand=user_handle, holder=user_name, year=2026,
                data_source="SOURCE LINE 1\nSOURCE LINE 2",
                encoding=preset.encoding)   # "BRIGHTNESS = SPEED"

rgba = fig_to_rgba(fig)  # (1920, 1080, 4) float64 in [0, 1]
close(fig)
```

## Dark glow frame (lightning / quakes / beams)

```python
from aesthetics import preset_figure, accumulate_glow, glow_from_grid, light_beam

fig, ax, preset = preset_figure("dark_glow", 1080, 1920)

# Raw events in pixel coordinates:
glow = accumulate_glow(xs, ys, values, (1920, 1080),
                       vmin=0.0, vmax=FLASH_VMAX,  # reel-wide fixed
                       cmap=preset.cmap, sigma=5.0,
                       bloom_sigma=22.0, bloom_gain=0.55)

# ...or pre-aggregated counts already rasterized to the render grid:
glow = glow_from_grid(counts_grid, vmin=0.0, vmax=FLASH_VMAX, ...)

ax.imshow(glow, extent=[0, 1, 0, 1], origin="upper",
          transform=ax.transAxes, aspect="auto", zorder=2)

# Directional sources, additive:
beams = sum(light_beam((1920, 1080), x, y, angle, length_px, width_px)
            for x, y, angle in lights)
ax.imshow(np.clip(beams, 0, 1), extent=[0, 1, 0, 1], origin="upper",
          transform=ax.transAxes, aspect="auto", zorder=3)

counter(ax, 0.06, 0.10, total_flashes, label="flashes on land")
date_dial(ax, 0.80, 0.78, 0.075, current_date)
```

`accumulate_glow` bins raw points; `glow_from_grid` skips binning for data
that already arrives per-pixel (e.g. GOES flash counts per cell
rasterized with `np.kron`). Both blur linear energy, then colormap.

## Paper prism frame (precipitation / any scalar-as-height)

```python
from aesthetics import prism_frame, get_preset, new_canvas, vertical_scale_bar

rgba = prism_frame(rain_grid, vmin=0.0, vmax=40.0, cmap="Blues",
                   width_px=1080, height_px=1920)
preset = get_preset("paper_prism")
fig, ax = new_canvas(1080, 1920, background=preset.bg_rgb)
ax.imshow(rgba, extent=[0, 1, 0, 1], origin="upper",
          transform=ax.transAxes, aspect="auto", zorder=1)
vertical_scale_bar(ax, 0.10, 0.32, 0.28, 0.0, 40.0,
                   label="rain", unit="mm/day", color="black")
encoding_statement(ax, 0.5, 0.115, preset.encoding, color="black")
```

## Rotated framing (elongated regions)

```python
from aesthetics import (optimal_rotation, rotated_render_size,
                        rotate_frame_fill, new_canvas, fig_to_rgba)

angle = optimal_rotation(lon0, lon1, lat0, lat1, canvas_wh=(1080, 1920))
rw, rh = rotated_render_size(angle, (1080, 1920))

fig, ax = new_canvas(rw, rh, background="black")
# ... draw the NORTH-UP map at (rw, rh) ...
map_rgba = fig_to_rgba(fig); close(fig)

rgba = rotate_frame_fill(map_rgba, angle, (1080, 1920))  # exactly 1080x1920

fig2, ax2 = new_canvas(1080, 1920, background="black")
ax2.imshow(rgba, extent=[0, 1, 0, 1], origin="upper",
           transform=ax2.transAxes, aspect="auto", zorder=1)
# ... titles, legends, furniture drawn here, unrotated ...
draw_north_arrow(ax2, 0.06, 0.80, angle_deg=angle)  # honest rotated arrow
```

## Conventions the caller must honor

1. **Fixed scales per reel.** `vmin`, `vmax`, `speed_max` are computed
   once (from the full reel domain or the survey-timescales suggestion),
   then reused for every frame.
2. **Fixed seed per reel** for `lic_texture` (or vary it deliberately —
   but a changing seed shimmers the texture). `render_strands` uses no
   RNG at all — but keep the *particle seeding* in survey-flow fixed per
   reel for the same reason.
3. **`aspect="auto"`** on every `imshow` that uses
   `transform=ax.transAxes`.
4. **Furniture after rotation.** Titles, legends, and `frame_furniture`
   are drawn on the final frame, never on the pre-rotation canvas.
5. **Brand is the user's.** Pass the page handle to `frame_furniture`;
   there is no default brand.
6. **Strands are drawn once per data timestep**, not per animation
   frame. The strand field evolves slowly (hourly model output), so
   render one strand texture per timestep and let survey-animate's
   crossfade carry the motion between them.

## Dark strands frame (wind / currents — the warming.watch look)

Thousands of fine advected trails, colored by a scalar, clipped to a
mask so the geography emerges from the data with no visible basemap.

```python
from flow.advect import AdvectionConfig, ParticleSet  # survey-flow (peer)
from aesthetics import (
    preset_figure, render_strands, draw_title, draw_subtitle,
    gradient_bar, timeline, frame_furniture, fig_to_rgba,
)
from aesthetics.backgrounds import close
import numpy as np

fig, ax, preset = preset_figure("dark_strands", 1080, 1920)

# --- advect (survey-flow owns this; the engine only renders) -------------
cfg = AdvectionConfig(dt_seconds=3600, trail_length=12, seed=7)  # fixed/reel
field_t = tvf.at(t)                       # TimeVaryingField at this timestep
ps = ParticleSet(N_PARTICLES, field_t, cfg, seed=7)
for _ in range(SPINUP_STEPS):
    ps.step(field_t)
segs, valid = ps.trail_segments()         # (n, L-1, 2, 2) lon/lat

# --- lon/lat segments -> axes-fraction polylines (survey-viz bridge) ------
lon0, lon1, lat0, lat1 = spec.bbox
def _frac(lon, lat):
    return ((lon - lon0) / (lon1 - lon0), 1.0 - (lat - lat0) / (lat1 - lat0))

trails, head_lons, head_lats = [], [], []
for s, ok in zip(segs, valid):
    # One particle's (L-1) segments -> one polyline: first segment's
    # start, then each segment's end. Dead links (ok=False) split the
    # polyline; the engine also splits on NaN, so pass them through.
    pts = [_frac(*s[0][0])] + [_frac(*seg[1]) for seg in s]
    trails.append(np.array(pts))
    head_lons.append(s[-1][1][0])
    head_lats.append(s[-1][1][1])
# Scalar at each trail head (temperature / speed overlay on the field):
head_vals = field_t.sample_scalar(np.array(head_lons), np.array(head_lats))
# Speed at each trail head, normalized REEL-WIDE to [0, 1] (never per-frame):
#   head_speed01 = np.clip((head_speed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN), 0, 1)
# with SPEED_MIN/SPEED_MAX fixed for the whole reel, exactly like vmin/vmax.

# --- mask: landmass for wind, ocean for currents --------------------------
# Build once per reel from the field landmask on a coarse grid:
#   mask = ~field.is_land(lon_grid, lat_grid)  # (my, mx) bool, row 0 = top
# True keeps strands; the country's shape emerges with no basemap drawn.

# --- render ---------------------------------------------------------------
rgba = render_strands(
    trails, head_vals,
    vmin=TMIN, vmax=TMAX,                 # reel-wide fixed, never per-frame
    cmap=preset.cmap,                     # "turbo" for dark_strands
    width_px=1080, height_px=1920,
    linewidth=1.4, head_alpha=0.8, tail_alpha=0.04,
    brightness=head_speed01,              # (n,) bivariate channel: HUE = temp, BRIGHTNESS = speed
    mask=landmask_bool,                   # or None for unclipped strands
    mask_feather=3.0,                     # soft mask edge (px); 0 = hard
)
ax.imshow(rgba, extent=[0, 1, 0, 1], origin="upper",
          transform=ax.transAxes, aspect="auto", zorder=2)

# --- map dressing: none by default ----------------------------------------
# preset.basemap is NO_BASEMAP (coastlines off). To add hairlines:
#   from aesthetics import draw_basemap, VOID_BLACK
#   draw_basemap(ax, coastline_segments, VOID_BLACK)

# --- editorial ------------------------------------------------------------
lay = preset.legend_layout
draw_title(ax, title, *lay["title"], size=preset.title_size, color="white")
draw_subtitle(ax, window_label, *lay["subtitle"], size=preset.subtitle_size)
gradient_bar(ax, lay["gradient_bar"], preset.cmap, TMIN, TMAX,
             label="air temperature", unit="°C")
timeline(ax, lay["timeline"], t_start, t_end, t_now)
frame_furniture(ax, brand=user_handle, holder=user_name, year=2026,
                data_source="ERA5 reanalysis · 10 m wind · 2 m temperature",
                encoding="COLOR = AIR TEMPERATURE")

rgba = fig_to_rgba(fig)
close(fig)
```

**Cost honesty.** ~1.3 s per strand frame (4000 trails x 12 points at
1080x1920) — essentially the same as one LIC frame at 540x540,
`kernel=12`. It is the most expensive preset per frame; keep trail
counts modest on the daily automation.

## Basemap styles

```python
from aesthetics import draw_basemap, get_basemap, VOID_BLACK, NO_BASEMAP, SUBTLE_LAND

# Styled replacement for draw_coastlines; presets carry one as preset.basemap.
draw_basemap(ax, coastline_segments, VOID_BLACK)          # v0.1.0 look
draw_basemap(ax, coastline_segments, NO_BASEMAP)          # nothing drawn
draw_basemap(ax, coastline_segments, SUBTLE_LAND, mask=landmask_bool)
```

`BasemapStyle` fields: `coastlines` (bool), `coastline_color`,
`coastline_width`, `coastline_alpha`, `land_fill` (+`land_fill_alpha`,
needs `mask`), `ocean_fill`, `background`. Custom styles are just
`BasemapStyle(name=..., ...)` — frozen dataclass, no registry needed.

## Furniture layout (collision-aware placement)

```python
from aesthetics import place_furniture, text_spec, box_spec, fit_font_size

specs = [
    text_spec(ax, "title", title, 0.06, 0.94, family="DejaVu Serif",
              size=preset.title_size, weight="bold", priority=10),
    text_spec(ax, "subtitle", window_label, 0.06, 0.875, priority=9),
    box_spec("date_dial", (0.78, 0.70, 0.16, 0.09), priority=5,
             alternatives=[(0.78, 0.55, 0.16, 0.09)], optional=True),
    # ... gradient_bar, timeline, counter, encoding ...
]
placed = {p.kind: p for p in place_furniture(specs, pad=0.012)}
title_size = preset.title_size * placed["title"].scale
draw_title(ax, title, *placed["title"].rect[:2], size=title_size)
# Pass placed furniture rects so city labels avoid the dial too:
place_labels(ax, label_dicts,
             obstacles=[p.rect for p in placed.values() if p.placed])
```

`text_spec` measures the real rasterized extent; over-long titles shrink
through `(0.92, 0.85, 0.78, 0.70)` before colliding. See `docs/LAYOUT.md`
for the algorithm and its limits.
