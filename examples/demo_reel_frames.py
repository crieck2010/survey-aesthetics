"""Demo: render one sample frame per preset into examples/output/.

Usage:
    python examples/demo_reel_frames.py [--outdir examples/output]

Deterministic: every frame uses fixed seeds, so re-running produces
byte-identical PNGs. This script is also the fresh-clone verification
render (see README).
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
from PIL import Image

from aesthetics import (
    accumulate_glow,
    counter,
    date_dial,
    draw_readout,
    draw_subtitle,
    draw_title,
    encoding_statement,
    fig_to_rgba,
    frame_furniture,
    get_preset,
    glow_from_grid,
    gradient_bar,
    lic_texture,
    light_beam,
    new_canvas,
    preset_figure,
    prism_frame,
    timeline,
    vertical_scale_bar,
)
from aesthetics.backgrounds import close
from aesthetics.framing import optimal_rotation, rotate_frame_fill, rotated_render_size

W, H = 1080, 1920  # the reel canvas


def save(rgba: np.ndarray, path: Path) -> None:
    u8 = (np.clip(rgba, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(u8).save(path)
    print(f"wrote {path}  ({u8.shape[1]}x{u8.shape[0]})")


def _synthetic_bay(ny=480, nx=270, seed=0):
    """Gyre + tidal jet through a strait, with an L-shaped landmass (NaN)."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:ny, 0:nx].astype(float)
    u = np.sin(x / 28.0) * 2.0 + np.exp(-((y - ny / 2) ** 2) / 3200.0) * 3.0
    v = np.cos(y / 36.0) * 1.6
    temp = 58.0 + 0.05 * x + 2.0 * np.sin(y / 60.0)
    land = (x < nx * 0.21) | ((y < ny * 0.25) & (x < nx * 0.52))
    u = np.where(land, np.nan, u)
    v = np.where(land, np.nan, v)
    temp = np.where(land, np.nan, temp)
    return u, v, temp


def demo_dark_flow(outdir: Path) -> None:
    """LIC current streaks on black — the 'week of currents' look."""
    u, v, temp = _synthetic_bay()
    fig, ax, preset = preset_figure("dark_flow", W, H)
    tex = lic_texture(u, v, temp, vmin=58.0, vmax=72.0, cmap=preset.cmap,
                      seed=7, speed_max=4.0)
    ax.imshow(tex, extent=[0, 1, 0, 1], origin="upper", transform=ax.transAxes,
              aspect="auto", zorder=2)
    lay = preset.legend_layout
    draw_title(ax, "Demo Bay", *lay["title"], size=preset.title_size,
               color=preset.text_color)
    draw_subtitle(ax, "A Week of Currents", *lay["subtitle"],
                  size=preset.subtitle_size, color=preset.text_color)
    gradient_bar(ax, lay["gradient_bar"], preset.cmap, 58.0, 72.0,
                 label="water temperature", unit="\u00b0F",
                 color=preset.text_color)
    timeline(ax, lay["timeline"], datetime(2026, 9, 19), datetime(2026, 9, 26),
             datetime(2026, 9, 20, 7), color=preset.text_color)
    frame_furniture(ax, brand="demo-page", holder="Demo Holder", year=2026,
                    data_source="SYNTHETIC DEMO FIELD\nNOT REAL DATA",
                    encoding=preset.encoding, color=preset.text_color)
    save(fig_to_rgba(fig), outdir / "demo_dark_flow.png")
    close(fig)


def demo_dark_glow(outdir: Path) -> None:
    """Event glow with bloom + lighthouse beams on black.

    Flashes are simulated the way GOES delivers them: gridded counts per
    cell (heavy-tailed), not raw points — dense cells burn bright.
    """
    rng = np.random.default_rng(11)
    cell = 6  # px per grid cell
    gw, gh = W // cell, H // cell
    yy, xx = np.mgrid[0:gh, 0:gw].astype(float)
    # A storm band arcing across the frame, with scattered hot cells.
    dist = np.abs(yy - gh * 0.42 - 40.0 * np.sin(xx / gw * 6.0))
    density = np.exp(-((dist / 45.0) ** 2))
    counts = rng.poisson(density * 260.0).astype(float)
    hot = rng.uniform(0.0, 1.0, (gh, gw)) < 0.02
    counts[hot] += rng.uniform(400.0, 1400.0, hot.sum())
    # Rasterize cells to pixels (each pixel carries its cell's count —
    # this is how gridded count data feeds the glow layer).
    counts_px = np.kron(counts, np.ones((cell, cell)))

    fig, ax, preset = preset_figure("dark_glow", W, H)
    glow = glow_from_grid(counts_px, vmin=0.0, vmax=1000.0,
                          cmap=preset.cmap, sigma=4.0,
                          bloom_sigma=24.0, bloom_gain=0.55)
    ax.imshow(glow, extent=[0, 1, 0, 1], origin="upper", transform=ax.transAxes,
              aspect="auto", zorder=2)
    coast = np.zeros((H, W, 4))
    for i, ang in enumerate([35.0, 60.0, 120.0]):
        coast += light_beam((H, W), 200 + i * 260, 1300 - i * 170, ang,
                            length_px=420.0, width_px=18.0, intensity=0.9)
    ax.imshow(np.clip(coast, 0.0, 1.0), extent=[0, 1, 0, 1], origin="upper", transform=ax.transAxes,
              aspect="auto", zorder=3)
    lay = preset.legend_layout
    draw_title(ax, "Demo Lights", *lay["title"], size=preset.title_size,
               color=preset.text_color)
    draw_subtitle(ax, "Every Flash, One Year", *lay["subtitle"],
                  size=preset.subtitle_size, color=preset.text_color)
    cx, cy = lay["counter"]
    counter(ax, cx, cy, 128_400, label="flashes", color=preset.text_color)
    dcx, dcy, dr = lay["date_dial"]
    date_dial(ax, 0.72, dcy, 0.062, datetime(2026, 3, 27),
              color=preset.text_color, date_size=26)
    frame_furniture(ax, brand="demo-page", holder="Demo Holder", year=2026,
                    data_source="SYNTHETIC DEMO FIELD\nNOT REAL DATA",
                    color=preset.text_color)
    save(fig_to_rgba(fig), outdir / "demo_dark_glow.png")
    close(fig)


def demo_paper_prism(outdir: Path) -> None:
    """Prism extrusion on paper — the 'years of rain' look."""
    rng = np.random.default_rng(5)
    ny, nx = 44, 32
    y, x = np.mgrid[0:ny, 0:nx].astype(float)
    rain = (18.0 * np.exp(-((x - 11) ** 2 + (y - 29) ** 2) / 90.0)
            + 30.0 * np.exp(-((x - 22) ** 2 + (y - 12) ** 2) / 60.0)
            + rng.uniform(0, 3, (ny, nx)))
    rain[rain < 4.0] = np.nan  # dry cells show paper

    rgba = prism_frame(rain, vmin=0.0, vmax=40.0, width_px=W, height_px=H)

    preset = get_preset("paper_prism")
    fig, ax = new_canvas(W, H, background=preset.bg_rgb)
    ax.imshow(rgba, extent=[0, 1, 0, 1], origin="upper", transform=ax.transAxes,
              aspect="auto", zorder=1)
    lay = preset.legend_layout
    draw_title(ax, "Demo Rain", *lay["title"], size=preset.title_size,
               color=preset.text_color)
    draw_subtitle(ax, "Three Years of Rain", *lay["subtitle"],
                  size=preset.subtitle_size, color=preset.text_color)
    draw_readout(ax, "27 OCT 2023", 0.62, 0.865, size=30,
                 color=preset.text_color)
    vertical_scale_bar(ax, 0.10, 0.32, 0.28, 0.0, 40.0,
                       label="rain", unit="mm/day",
                       color=preset.text_color)
    encoding_statement(ax, 0.5, 0.115, preset.encoding,
                       color=preset.text_color)
    frame_furniture(ax, brand="demo-page", holder="Demo Holder", year=2026,
                    data_source="SYNTHETIC DEMO FIELD\nNOT REAL DATA",
                    color=preset.text_color)
    save(fig_to_rgba(fig), outdir / "demo_paper_prism.png")
    close(fig)


def demo_rotated_frame(outdir: Path) -> None:
    """Rotated auto-fit framing: render the map oversized, rotate the
    composite, then dress the frame (titles/legends stay unrotated)."""
    angle = optimal_rotation(-79.8, -76.0, 43.2, 44.1, canvas_wh=(W, H))
    print(f"optimal rotation for demo region: {angle:.1f}°")
    rw, rh = rotated_render_size(angle, (W, H))

    # 1. Render the north-up map oversized.
    u, v, temp = _synthetic_bay(ny=rh // 4, nx=rw // 4)
    fig, ax = new_canvas(rw, rh, background="black")
    tex = lic_texture(u, v, temp, vmin=58.0, vmax=72.0, seed=7, speed_max=4.0)
    ax.imshow(tex, extent=[0, 1, 0, 1], origin="upper", transform=ax.transAxes,
              aspect="auto", zorder=2)
    rgba = fig_to_rgba(fig)
    close(fig)
    # 2. Rotate with center-crop -> exactly W x H, full-bleed.
    rgba = rotate_frame_fill(rgba, angle, (W, H))
    assert rgba.shape == (H, W, 4), rgba.shape

    # 3. Dress the rotated frame; furniture stays unrotated.
    fig2, ax2 = new_canvas(W, H, background="black")
    ax2.imshow(rgba, extent=[0, 1, 0, 1], origin="upper",
               transform=ax2.transAxes, aspect="auto", zorder=1)
    draw_title(ax2, "Demo Bay", 0.06, 0.94, size=64, color="white")
    draw_subtitle(ax2, "A Week of Currents", 0.06, 0.875, size=26,
                  color="white")
    frame_furniture(ax2, brand="demo-page", holder="Demo Holder", year=2026,
                    data_source="SYNTHETIC DEMO FIELD",
                    encoding="BRIGHTNESS = SPEED", color="white")
    save(fig_to_rgba(fig2), outdir / "demo_rotated.png")
    close(fig2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="examples/output")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    demo_dark_flow(outdir)
    demo_dark_glow(outdir)
    demo_paper_prism(outdir)
    demo_rotated_frame(outdir)
    print("done.")


if __name__ == "__main__":
    main()
