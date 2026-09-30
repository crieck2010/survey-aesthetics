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
   but a changing seed shimmers the texture).
3. **`aspect="auto"`** on every `imshow` that uses
   `transform=ax.transAxes`.
4. **Furniture after rotation.** Titles, legends, and `frame_furniture`
   are drawn on the final frame, never on the pre-rotation canvas.
5. **Brand is the user's.** Pass the page handle to `frame_furniture`;
   there is no default brand.
