"""survey-aesthetics: aesthetic rendering engine for remote-sensing reels.

Deterministic, UI-free render layers that give survey-viz output the
mapped.earth look: LIC flow-field streaks, additive glow with bloom, 3D
prism extrusion, rotated auto-fit framing, editorial typography, custom
legends, curated backgrounds, and watermark furniture.

Every public function is deterministic: same inputs + same seed ->
byte-identical output, so survey-cache fingerprints stay stable across
frames of a reel.

Intended consumer: survey-viz (see docs/API.md for the call pattern).
"""

import matplotlib

matplotlib.use("Agg")  # headless render backend; no UI imports anywhere

from aesthetics.backgrounds import BLACK, PAPER, draw_coastlines, fig_to_rgba, new_canvas
from aesthetics.framing import (
    fit_extent_to_canvas,
    optimal_rotation,
    rotate_frame,
    rotate_frame_fill,
    rotated_render_size,
    tight_bbox,
)
from aesthetics.glow import accumulate_glow, glow_from_grid, light_beam
from aesthetics.legends import (
    counter,
    date_dial,
    encoding_statement,
    gradient_bar,
    timeline,
    vertical_scale_bar,
)
from aesthetics.lic import lic_texture
from aesthetics.presets import (
    DARK_FLOW,
    DARK_GLOW,
    PAPER_PRISM,
    Preset,
    get_preset,
    list_presets,
    preset_figure,
)
from aesthetics.prism import prism_frame
from aesthetics.typography import (
    draw_readout,
    draw_subtitle,
    draw_title,
    place_labels,
)
from aesthetics.watermark import (
    draw_copyright,
    draw_data_source,
    draw_watermark,
    frame_furniture,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # backgrounds
    "BLACK",
    "PAPER",
    "new_canvas",
    "draw_coastlines",
    "fig_to_rgba",
    # lic
    "lic_texture",
    # glow
    "accumulate_glow",
    "glow_from_grid",
    "light_beam",
    # prism
    "prism_frame",
    # framing
    "rotate_frame",
    "rotate_frame_fill",
    "optimal_rotation",
    "rotated_render_size",
    "tight_bbox",
    "fit_extent_to_canvas",
    # typography
    "draw_title",
    "draw_subtitle",
    "draw_readout",
    "place_labels",
    # legends
    "gradient_bar",
    "vertical_scale_bar",
    "date_dial",
    "timeline",
    "counter",
    "encoding_statement",
    # watermark
    "draw_watermark",
    "draw_copyright",
    "draw_data_source",
    "frame_furniture",
    # presets
    "Preset",
    "DARK_FLOW",
    "DARK_GLOW",
    "PAPER_PRISM",
    "get_preset",
    "list_presets",
    "preset_figure",
]
