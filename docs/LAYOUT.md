# Furniture layout — the collision-aware placement pass

## Problem

The v0.1.0 presets placed every furniture item (title, subtitle, date
dial, gradient bar, timeline, counter, encoding line, watermark) at a
fixed axes-fraction position. On real reels those fixed positions
collide: the date dial sat on the subtitle and on place labels
("Lagos"), and long titles overflowed the canvas width. Fixed positions
are a good *default* but a bad *law*.

## What `aesthetics.layout` does

`place_furniture(specs, pad=0.012)` takes a list of `FurnitureSpec`
(each: `kind`, preferred `rect`, `priority`, `alternatives`,
`optional`, `shrink_steps`) and returns one `PlacedItem` per spec in
input order.

**Algorithm** (deterministic, O(n²) rect arithmetic — microseconds):

1. Sort specs by descending priority (stable; ties keep input order).
2. For each spec, try the preferred rect, then each alternative rect,
   then each shrink scale applied to the preferred rect (text only —
   shrink scales w/h about the rect's top-left corner).
3. Accept the first candidate that lies inside [0, 1]² and does not
   overlap any already-placed rect (both expanded by `pad`).
4. If nothing fits: optional items are dropped (`placed=False`);
   required items fall back to their preferred rect, so a reel never
   renders empty-handed.

**Text measurement.** `text_spec` measures the real rasterized extent
via the Agg renderer (`text_extent_frac`), so the rect matches the
glyphs that will actually draw — the same measurement the final draw
uses, which keeps survey-cache fingerprints stable for a pinned
matplotlib version. `fit_font_size` binary-searches the largest size
whose width fits a `max_width_frac` budget (the title shrink-to-fit).

**Map labels.** The placer only handles furniture. City labels on the
map keep their own greedy avoidance in `place_labels`, which now
accepts `obstacles` — axes-fraction rects (e.g. the placed dial and
legend rects) that labels must avoid:

```python
placed = {p.kind: p for p in place_furniture(specs)}
place_labels(ax, label_dicts,
             obstacles=[p.rect for p in placed.values() if p.placed])
```

## Suggested priorities and alternatives (survey-viz contract)

| kind | priority | alternatives |
|---|---|---|
| title | 10 | — (shrinks instead) |
| subtitle | 9 | below title, right rail |
| date_dial | 5 | right rail mid, bottom right; optional |
| gradient_bar | 6 | right rail lower, bottom center |
| timeline | 6 | bottom center, right rail |
| counter | 7 | bottom left, bottom center |
| encoding | 4 | bottom center; optional |
| watermark | 3 | bottom right; optional |

The preset `legend_layout` dicts remain the *preferred* rects; callers
should attach 1–2 alternatives per item from the table above.

## Limits (honest)

- Overlap is tested on bounding rects, not glyph shapes; two rects that
  merely touch at the pad boundary can still look close.
- Shrink scales about the top-left corner; it never re-anchors text
  (a title anchored left stays left).
- `text_spec` supports `ha="left"`, `va="top"` only — the preset title
  grammar. Centered/right-aligned text needs its rect computed by hand.
- Each `text_spec`/`fit_font_size` call draws the canvas once (~10 ms
  at 1080x1920); a dozen furniture items cost ~0.1 s per frame — fine,
  but don't call it per animation frame for static furniture. Measure
  once per reel; furniture is static.
- Measurement is matplotlib-version-pinned: a matplotlib upgrade can
  shift DejaVu rasterization by a pixel and move a shrink decision.
  Survey-cache keys should include the renderer version on upgrades
  (same caveat as v0.1.0 byte-determinism).
