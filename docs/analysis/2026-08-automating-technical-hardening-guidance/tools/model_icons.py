#!/usr/bin/env python3
"""One icon per OSCAL model, taken from assets/images and stripped to geometry.

The eight files in assets/images are the authored source. They carry their
colour as literal hex and their chip as a filled rect, which is the one thing
this site does not do anywhere else: colour is written in the token block of
assets/site.css and nowhere else, so that one edit changes both themes and the
contrast checker can find every pair.

An SVG loaded through <img src> is a separate document and cannot see the page's
custom properties, so a token-driven icon has to be inline. This generator does
that conversion once, into data/model-icons.json, and every surface that draws a
model reads it from there:

  - the stroke colours become currentColor, set by .micon from a layer token
  - the second, lighter tone becomes a class the stylesheet colours
  - the chip goes entirely, because a rounded rect with a fill is a CSS box
  - <line> becomes <path>, and the two curved icons are redrawn with straight
    segments, both so tools/svgrender.py can draw them for the grayscale review

The layer is the argument the colour is making. Catalog, profile and mapping
collection are Control; component definition and system security plan are
Implementation; the two assessment models and the POA&M are Assessment. That is
the same three-way split the whole site turns on, so the icons are carrying it
rather than decorating with it.
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
IMAGES = os.path.join(SITE, "assets", "images")
OUT = os.path.join(SITE, "data", "model-icons.json")

SVG = "{http://www.w3.org/2000/svg}"

#  filename stem -> the model name the site uses for it. The site says
#  mapping-collection and component-definition; the files say control_mapping
#  and component. The site's names are the OSCAL root elements and are what
#  every other data file is keyed on, so they win.
MODELS = {
    "catalog_model": ("catalog", "control"),
    "profile_model": ("profile", "control"),
    "control_mapping_model": ("mapping-collection", "control"),
    "component_model": ("component-definition", "implementation"),
    "system_security_plan_model": ("system-security-plan", "implementation"),
    "assessment_plan_model": ("assessment-plan", "assessment"),
    "assessment_results_model": ("assessment-results", "assessment"),
    "plan_of_action_and_milestones_model": (
        "plan-of-action-and-milestones", "assessment"),
}

#  The lighter of the two tones in each icon. Everything else is the primary and
#  becomes currentColor. Listed rather than inferred, because "the lighter one"
#  is a judgement about the drawing and not something to guess from a hex value.
SOFT = {"#60A5FA", "#34D399", "#FBBF24"}

#  The chip. Dropped, not recoloured: it is a rounded rectangle behind the
#  glyph, which is a CSS box with a border-radius and a background, and keeping
#  it in the SVG would have meant the icon carrying a colour again.
CHIP = {"x": "6", "y": "6", "width": "52", "height": "52", "rx": "12"}

#  Two icons are drawn with cubic curves, which tools/svgrender.py cannot draw:
#  it implements M L H V Z and their relative forms and nothing else, so a
#  curve would render as a straight line to the last control point and the
#  grayscale review would show a shape nobody drew. Redrawn here as straight
#  segments that follow the same silhouette.
#
#  The book covers: the original rounded the spine with C34 18 34 22 34 22,
#  a two-unit turn at the top of a 30-unit spine. Two segments read the same at
#  the sizes this is used, 18px in a tile and 22px in a heading.
REDRAWN = {
    "catalog": [
        "M18 18H30L34 22V48L27 45H18V18Z",
        "M46 18H34L30 22V48L37 45H46V18Z",
    ],
    #  The shield. Only the one curved path is listed: the page outline and the
    #  folded corner beside it are already straight and are left alone. The
    #  original was one C-curve per side from the shoulder down to the point;
    #  four segments a side hold the silhouette at icon size.
    "system-security-plan": [
        "M32 30V40M32 30L28 31L26 33L26 36L28 39L32 42L36 39L38 36L38 33L36 31L32 30Z",
    ],
}


def read(stem: str) -> tuple[list[dict], str]:
    """One file, as a list of shapes plus the viewBox."""
    path = os.path.join(IMAGES, stem + ".svg")
    root = ET.parse(path).getroot()
    shapes: list[dict] = []
    for el in root:
        tag = el.tag[len(SVG):] if el.tag.startswith(SVG) else el.tag
        if tag == "rect" and all(el.get(k) == v for k, v in CHIP.items()):
            continue                                    # the chip, dropped
        shapes.append(shape(tag, el))
    return shapes, root.get("viewBox", "0 0 64 64")


def shape(tag: str, el) -> dict:
    """One element, with its colour replaced by a role."""
    soft = (el.get("stroke") in SOFT) or (el.get("fill") in SOFT)
    out: dict = {"tag": "path" if tag == "line" else tag, "soft": soft}

    if tag == "line":
        #  A line is a path with two points. Converting it here means every
        #  stroked shape in the file is one of three tags rather than four,
        #  and svgrender draws paths and not lines.
        out["d"] = (f'M{el.get("x1")} {el.get("y1")}'
                    f'L{el.get("x2")} {el.get("y2")}')
    elif tag == "path":
        out["d"] = el.get("d")
    else:
        for k in ("x", "y", "width", "height", "rx", "cx", "cy", "r"):
            if el.get(k) is not None:
                out[k] = el.get(k)

    #  A fill that is not "none" is a solid shape: the dot at the centre of the
    #  POA&M, and the knockouts on the profile that hide the line behind each
    #  marker. The first takes the ink colour, the second the chip colour, and
    #  the difference is whether the fill was the tint.
    fill = el.get("fill")
    if fill and fill != "none":
        out["fill"] = "chip" if fill in ("#EFF6FF", "#ECFDF5", "#FFFBEB") else "ink"
    for k in ("stroke-width", "stroke-linecap", "stroke-linejoin",
              "stroke-dasharray"):
        if el.get(k):
            out[k] = el.get(k)
    return out


def redraw(model: str, shapes: list[dict]) -> list[dict]:
    """Swap the curved paths for the straight-segment versions."""
    if model not in REDRAWN:
        return shapes
    want = list(REDRAWN[model])
    out = []
    for s in shapes:
        if s["tag"] == "path" and "C" in (s.get("d") or "") and want:
            s = dict(s, d=want.pop(0))
        out.append(s)
    if want:
        raise SystemExit(f"{model}: {len(want)} redrawn path(s) had nothing to "
                         f"replace; the source icon has changed shape")
    return out


CURVE = re.compile(r"[CcSsQqTtAa]")

# --------------------------------------------------------------------------- #
# Cropping, which is the whole of why these are legible at 16px                #
# --------------------------------------------------------------------------- #
#
#  Every icon is drawn on a 64-unit canvas and seven of the eight use only the
#  middle 32 to 35 units of it. Roughly half of each file is empty margin. Drawn
#  in a chip about 21px across, with the SVG inset inside that, the glyph came
#  out around 8px: two nested shapes where the outer one had taken most of the
#  room and the inner one carried all the information.
#
#  So the viewBox is cropped to what is actually drawn, squared up, and given a
#  small even margin. Nothing is redrawn and no proportion changes; the same
#  drawing is simply not surrounded by nothing. That alone is worth about twice
#  the rendered size, and it scales the strokes with it, which is what decides
#  legibility at this scale.

NUM = re.compile(r"-?\d*\.?\d+")

#  A margin inside the chip, as a fraction of the glyph. Enough that the drawing
#  is not touching the rounded corners, and no more: this is the number that was
#  effectively 45 per cent before, once the empty canvas and the CSS inset were
#  multiplied together.
MARGIN = 0.09

#  The stroke, as a fraction of the finished box. Cropping alone would leave the
#  POA&M finer than the rest, because its tick marks reach further out so it
#  crops less and its strokes scale up less. Normalising here keeps one weight
#  across the set, and keeps the relative weights inside an icon: the clock hand
#  drawn at 1.5 against a body of 2 stays three quarters of it.
STROKE_RATIO = 0.055


def points(s: dict) -> list[tuple[float, float]]:
    """The extreme points of one shape, ignoring its stroke."""
    if s["tag"] == "rect":
        x, y = float(s["x"]), float(s["y"])
        return [(x, y), (x + float(s["width"]), y + float(s["height"]))]
    if s["tag"] == "circle":
        cx, cy, r = float(s["cx"]), float(s["cy"]), float(s["r"])
        return [(cx - r, cy - r), (cx + r, cy + r)]

    #  M L H V and their relative forms, which is the subset every path here is
    #  held to so that tools/svgrender.py can draw it. Z closes back to a point
    #  already counted, so it adds nothing to the extent.
    out, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r"([MmLlHhVvZz])([^MmLlHhVvZz]*)", s["d"]):
        n = [float(v) for v in NUM.findall(args)]
        if cmd in "MmLl":
            for i in range(0, len(n) - 1, 2):
                x, y = ((n[i], n[i + 1]) if cmd.isupper()
                        else (x + n[i], y + n[i + 1]))
                out.append((x, y))
        elif cmd in "Hh":
            for v in n:
                x = v if cmd == "H" else x + v
                out.append((x, y))
        elif cmd in "Vv":
            for v in n:
                y = v if cmd == "V" else y + v
                out.append((x, y))
    return out


def crop(shapes: list[dict]) -> tuple[str, float]:
    """A square viewBox around what is drawn, and the scale factor it implies."""
    xs, ys = [], []
    for s in shapes:
        half = float(s.get("stroke-width", 0)) / 2
        for px, py in points(s):
            xs += [px - half, px + half]
            ys += [py - half, py + half]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    #  Squared around the centre, so a wide glyph and a tall one are drawn at
    #  the same scale and sit in the chip the same way.
    span = max(x1 - x0, y1 - y0) * (1 + 2 * MARGIN)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    box = f"{cx - span / 2:g} {cy - span / 2:g} {span:g} {span:g}"
    return box, span


def build() -> dict:
    icons = {}
    for stem, (model, layer) in sorted(MODELS.items(), key=lambda kv: kv[1][0]):
        shapes, authored_box = read(stem)
        shapes = redraw(model, shapes)
        for s in shapes:
            if s["tag"] == "path" and CURVE.search(s["d"]):
                raise SystemExit(
                    f"{model}: path uses a command tools/svgrender.py cannot "
                    f"draw: {s['d']}. Add it to REDRAWN.")
        view_box, span = crop(shapes)
        #  One stroke weight across the set, and the weights inside an icon held
        #  in proportion to each other.
        widest = max(float(s.get("stroke-width", 0)) for s in shapes) or 1.0
        k = (STROKE_RATIO * span) / widest
        for s in shapes:
            if "stroke-width" in s:
                s["stroke-width"] = f'{float(s["stroke-width"]) * k:.2f}'
        #  Cropping moved the edges in and the strokes then grew, so the box is
        #  recomputed against what will actually be drawn.
        view_box, _ = crop(shapes)
        icons[model] = {"layer": layer, "source": stem + ".svg",
                        "authored_box": authored_box, "view_box": view_box,
                        "shapes": shapes}
    return {
        "note": ("One icon per OSCAL model, generated by tools/model_icons.py "
                 "from the authored files in assets/images. Geometry only: the "
                 "colour is a layer token applied by the stylesheet, and the "
                 "chip behind the glyph is a CSS box. Do not edit this file; "
                 "edit the SVG and regenerate."),
        "layers": {
            "control": {"label": "Control layer",
                        "models": ["catalog", "profile", "mapping-collection"]},
            "implementation": {"label": "Implementation layer",
                               "models": ["component-definition",
                                          "system-security-plan"]},
            "assessment": {"label": "Assessment layer",
                           "models": ["assessment-plan", "assessment-results",
                                      "plan-of-action-and-milestones"]},
        },
        "icons": icons,
    }


STROKE_ATTRS = ("stroke-width", "stroke-linecap", "stroke-linejoin",
                "stroke-dasharray")

#  The class name is the layer, spelled out. The token names shorten
#  implementation to impl; the class does not, because it appears in markup a
#  reader may inspect and "micon--impl" is a guess where the full word is not.
_LOADED: dict | None = None


def icons() -> dict:
    global _LOADED
    if _LOADED is None:
        with open(OUT, encoding="utf-8") as fh:
            _LOADED = json.load(fh)
    return _LOADED


def model_icon(model: str, extra: str = "") -> str:
    """One model's icon, as inline SVG inside its chip.

    Inline rather than <img src>, because an SVG loaded through an img is a
    separate document and cannot see the page's custom properties. Inline, the
    ink is currentColor and the second tone is a class, so the stylesheet
    colours both from the layer tokens and the icon follows the theme.
    """
    icon = icons()["icons"].get(model)
    if icon is None:
        raise SystemExit(f"no icon for model {model!r}. Add one to "
                         f"assets/images and rerun tools/model_icons.py")
    out = []
    for s in icon["shapes"]:
        attrs = [f'{k}="{s[k]}"' for k in STROKE_ATTRS if k in s]
        #  Classes are collected and written once. A shape can want two of them,
        #  and the profile does: its markers are stroked in the second tone and
        #  filled with the chip colour to hide the rule running behind them.
        #  Emitting them as two class attributes on one element is invalid and
        #  silently drops the second, so the markers lost their knockout and the
        #  rule showed through every one of them.
        classes = []
        if s.get("soft"):
            classes.append("model-icon__soft")
        else:
            attrs.append('stroke="currentColor"')
        #  A filled shape is either the ink, for a solid dot, or the chip, for a
        #  knockout hiding the line that runs behind a marker.
        fill = s.get("fill")
        if fill == "ink":
            attrs.append('fill="currentColor"')
        elif fill == "chip":
            classes.append("model-icon__knockout")
        else:
            attrs.append('fill="none"')
        if classes:
            attrs.insert(0, f'class="{" ".join(classes)}"')
        if s["tag"] == "path":
            out.append(f'<path d="{s["d"]}" {" ".join(attrs)}/>')
        else:
            geom = " ".join(f'{k}="{v}"' for k, v in s.items()
                            if k in ("x", "y", "width", "height", "rx",
                                     "cx", "cy", "r"))
            out.append(f'<{s["tag"]} {geom} {" ".join(attrs)}/>')
    cls = f'model-icon model-icon--{icon["layer"]}' + (f" {extra}" if extra else "")
    return (f'<span class="{cls}">'
            f'<svg viewBox="{icon["view_box"]}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg></span>')


def model_tile(model: str, kind: str | None = None) -> str:
    """One model as a chip: the icon, the name, and the type if it has one.

    The unit a reader learns once and then recognises everywhere. It began on
    the stakeholder tables and was defined there, which was fine while one page
    drew it. The worked scenario names the same seven models three times over,
    in a table and in three lists, and was setting them as bare <code>, so the
    same seven names had two appearances on one site depending on which page you
    were reading.

    Defined here, beside the icon it wraps, so both pages get it from one place.
    A tile built by copying the markup into a second generator is a tile that
    drifts, and the string that carries the runtime mark has already done that
    once.
    """
    k = f'<span class="mtile__kind">{kind}</span>' if kind else ""
    return (f'<span class="mtile">{model_icon(model)}'
            f'<span class="mtile__name">{model}</span>{k}</span>')


def main() -> int:
    doc = build()
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        have = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if have != text:
            print(f"{OUT} is stale; run python tools/model_icons.py")
            return 1
        print(f"{OUT} is current")
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    n = len(doc["icons"])
    shapes = sum(len(i["shapes"]) for i in doc["icons"].values())
    print(f"data/model-icons.json  {n} models, {shapes} shapes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
