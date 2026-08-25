#!/usr/bin/env python3
"""
svgrender.py: a small, deliberate SVG rasteriser for this site's own diagrams.

It exists for one reason. Plan section 7 requires that every distinction the
diagrams make survives grayscale, and the build guide's gate 3 asks a human to
look through build/grayscale/ and check exactly that. Checking it needs a
picture, and the sandbox this site is built in has no browser and no cairo. So
this renders the restricted SVG subset that tools/diagrams.py emits, and nothing
else. It is not a general SVG renderer and must not be used as one.

Supported, because that is all the generator emits:
    rect (with rx), circle, path (M m L l H h V v Z z), text, g with transform
    class-based styling from the diagram's own <style> block
    CSS custom properties, resolved from assets/site.css, both themes
    stroke-dasharray, approximated by segmenting
    marker-end, approximated by a filled arrowhead at the last segment

Unsupported and asserted against: gradients, filters, clip paths, transforms
other than translate and rotate, and any element the generator does not use.
"""

from __future__ import annotations

import math
import os
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

SVG_NS = "{http://www.w3.org/2000/svg}"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

_FONTS: dict[tuple, ImageFont.FreeTypeFont] = {}


def font(mono: bool, size: int, bold: bool):
    key = (mono, size, bold)
    if key not in _FONTS:
        p = MONO if mono else (SANS_BOLD if bold else SANS)
        _FONTS[key] = ImageFont.truetype(p, size)
    return _FONTS[key]


# --------------------------------------------------------------------------- #
# tokens                                                                       #
# --------------------------------------------------------------------------- #

def read_tokens(css_path: str) -> dict[str, dict[str, str]]:
    """Return {"light": {...}, "dark": {...}} of every custom property."""
    css = re.sub(r"/\*.*?\*/", "", open(css_path, encoding="utf-8").read(), flags=re.S)
    out: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    #  Selector lists matter here: site.css declares the sub-question aliases once,
    #  under ":root, [data-theme=dark]", so matching the two selectors
    #  separately would miss them. Later blocks win, which is cascade order.
    for sel, block in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        parts = [p.strip() for p in sel.split(",")]
        themes = []
        if ":root" in parts:
            themes.append("light")
        if '[data-theme="dark"]' in parts:
            themes.append("dark")
        if not themes:
            continue
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block):
            for t in themes:
                out[t][name] = value.strip()
    #  The dark theme overrides a subset of the light theme and inherits the rest.
    for k, v in out["light"].items():
        out["dark"].setdefault(k, v)
    return out


def resolve(value: str, tokens: dict[str, str], env: dict[str, str],
            depth: int = 0) -> str:
    if depth > 12:
        raise RecursionError(f"var() loop at {value!r}")
    m = re.fullmatch(r"var\((--[\w-]+)\)", value.strip())
    if not m:
        return value.strip()
    name = m.group(1)
    if name in env:
        return resolve(env[name], tokens, env, depth + 1)
    if name in tokens:
        return resolve(tokens[name], tokens, env, depth + 1)
    raise KeyError(f"undefined custom property {name}")


def to_rgb(colour: str) -> tuple[int, int, int]:
    h = colour.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"cannot rasterise colour {colour!r}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------- #
# style sheet inside the svg                                                   #
# --------------------------------------------------------------------------- #

def parse_style(text: str) -> dict[str, dict[str, str]]:
    """{'text': {...}, '.cls': {...}} keyed by the last simple selector."""
    rules: dict[str, dict[str, str]] = {}
    for sel, block in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        decls = dict(
            (k.strip(), v.strip())
            for k, v in (d.split(":", 1) for d in block.split(";") if ":" in d))
        for one in sel.split(","):
            key = one.strip().split()[-1] if one.strip() else ""
            if key:
                rules.setdefault(key, {}).update(decls)
    return rules


# --------------------------------------------------------------------------- #
# path parsing                                                                 #
# --------------------------------------------------------------------------- #

TOKEN = re.compile(r"([MmLlHhVvZz])|(-?\d*\.?\d+)")


def parse_path(d: str) -> list[list[tuple[float, float]]]:
    """Return a list of polylines. Only the commands the generator emits."""
    toks = [(c, n) for c, n in TOKEN.findall(d)]
    subs, cur = [], []
    x = y = 0.0
    i, cmd = 0, None
    nums: list[float] = []

    def flush():
        nonlocal cur
        if len(cur) > 1:
            subs.append(cur)
        cur = []

    while i < len(toks):
        c, n = toks[i]
        if c:
            cmd = c
            i += 1
            if cmd in "Zz":
                if cur:
                    cur.append(cur[0])
                flush()
            continue
        nums = []
        need = {"M": 2, "m": 2, "L": 2, "l": 2, "H": 1, "h": 1, "V": 1, "v": 1}[cmd]
        while len(nums) < need:
            nums.append(float(toks[i][1]))
            i += 1
        if cmd == "M":
            flush()
            x, y = nums
            cur = [(x, y)]
            cmd = "L"
        elif cmd == "m":
            flush()
            x, y = x + nums[0], y + nums[1]
            cur = [(x, y)]
            cmd = "l"
        elif cmd == "L":
            x, y = nums
            cur.append((x, y))
        elif cmd == "l":
            x, y = x + nums[0], y + nums[1]
            cur.append((x, y))
        elif cmd == "H":
            x = nums[0]
            cur.append((x, y))
        elif cmd == "h":
            x += nums[0]
            cur.append((x, y))
        elif cmd == "V":
            y = nums[0]
            cur.append((x, y))
        elif cmd == "v":
            y += nums[0]
            cur.append((x, y))
    flush()
    return subs


def dash(points, pattern):
    """Split a polyline into dashes. Good enough to read on a contact sheet."""
    on, off = pattern
    out, carry, drawing = [], 0.0, True
    seg = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dist = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while t < dist:
            span = (on if drawing else off) - carry
            step = min(span, dist - t)
            p0 = (x0 + (x1 - x0) * (t / dist), y0 + (y1 - y0) * (t / dist))
            t += step
            p1 = (x0 + (x1 - x0) * (t / dist), y0 + (y1 - y0) * (t / dist))
            if drawing:
                seg.append((p0, p1))
            carry += step
            if carry >= (on if drawing else off) - 1e-9:
                carry = 0.0
                drawing = not drawing
    out.extend(seg)
    return out


# --------------------------------------------------------------------------- #
# renderer                                                                     #
# --------------------------------------------------------------------------- #

class Renderer:
    def __init__(self, svg_path: str, tokens: dict[str, str], scale: float = 1.0):
        self.tokens = tokens
        self.scale = scale
        self.root = ET.parse(svg_path).getroot()
        vb = [float(v) for v in self.root.get("viewBox").split()]
        self.w, self.h = vb[2], vb[3]
        style_el = self.root.find(SVG_NS + "style")
        self.rules = parse_style(style_el.text if style_el is not None else "")
        self.img = Image.new("RGB", (int(self.w * scale), int(self.h * scale)),
                             to_rgb(resolve("var(--bg)", tokens, {})))
        self.d = ImageDraw.Draw(self.img)

    # ---- style ---------------------------------------------------------- #
    def declarations(self, el, inherited: dict[str, str]) -> dict[str, str]:
        out = dict(inherited)
        out.update(self.rules.get(el.tag.replace(SVG_NS, ""), {}))
        for cls in (el.get("class") or "").split():
            out.update(self.rules.get("." + cls, {}))
        for attr in ("fill", "stroke", "stroke-width", "font-size", "text-anchor"):
            if el.get(attr):
                out[attr] = el.get(attr)
        return out

    def env_from(self, el, env: dict[str, str]) -> dict[str, str]:
        out = dict(env)
        for cls in (el.get("class") or "").split():
            for k, v in self.rules.get("." + cls, {}).items():
                if k.startswith("--"):
                    out[k] = v
        return out

    def paint(self, decl, key, env):
        v = decl.get(key, "none")
        if v in ("none", "", "inherit"):
            return None
        if v.startswith("url("):
            return "pattern"
        return to_rgb(resolve(v, self.tokens, env))

    # ---- geometry ------------------------------------------------------- #
    def T(self, pt, tf):
        x, y = pt
        for kind, a, b in reversed(tf):
            if kind == "t":
                x, y = x + a, y + b
            elif kind == "s":
                x, y = x * a, y * b
            else:
                r = math.radians(a)
                x, y = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
        return x * self.scale, y * self.scale

    def factor(self, tf) -> float:
        """How much a length is scaled by, for stroke widths and radii."""
        k = 1.0
        for kind, a, b in tf:
            if kind == "s":
                k *= (abs(a) + abs(b)) / 2
        return k

    @staticmethod
    def parse_transform(s: str):
        """The transforms the generator emits, and a failure for any it does not.

        scale used to be dropped here in silence, and dropping a scale does not
        produce a broken picture: it produces a plausible one at the wrong size.
        Every model icon is placed with translate/scale/translate, so all eight
        of them were drawn on the grayscale review sheet at two to three times
        their real size, overlapping the labels beside them. The sheet exists so
        that a human can look at the diagrams, and it was showing them something
        the site does not draw.

        So scale is supported, and anything else raises rather than being
        skipped. The docstring at the top of this file already claimed
        unsupported transforms were asserted against; now they are.
        """
        s = s or ""
        out = []
        for kind, args in re.findall(r"([a-zA-Z]+)\(([^)]*)\)", s):
            n = [float(v) for v in re.split(r"[ ,]+", args.strip()) if v]
            if kind == "translate":
                out.append(("t", n[0], n[1] if len(n) > 1 else 0.0))
            elif kind == "scale":
                out.append(("s", n[0], n[1] if len(n) > 1 else n[0]))
            elif kind == "rotate":
                out.append(("r", n[0], 0.0))
            else:
                raise SystemExit(
                    f"svgrender: transform {kind}() is not supported. This "
                    f"renderer draws only what tools/diagrams.py emits; either "
                    f"stop emitting it or add it here.")
        return out

    # ---- draw ------------------------------------------------------------ #
    def run(self):
        self.walk(self.root, [], {}, {})
        return self.img

    def walk(self, el, tf, inherited, env):
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("title", "desc", "style", "defs"):
            return
        tf = tf + self.parse_transform(el.get("transform"))
        env = self.env_from(el, env)
        decl = self.declarations(el, inherited)
        if tag == "g" or tag == "svg":
            for ch in el:
                self.walk(ch, tf, decl, env)
            return
        getattr(self, "draw_" + tag, self.draw_unknown)(el, tf, decl, env)
        for ch in el:
            self.walk(ch, tf, decl, env)

    def draw_unknown(self, el, tf, decl, env):
        raise NotImplementedError(f"element {el.tag} is not in the supported subset")

    def draw_rect(self, el, tf, decl, env):
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        w, h = float(el.get("width")), float(el.get("height"))
        rx = float(el.get("rx", 0))
        p0, p1 = self.T((x, y), tf), self.T((x + w, y + h), tf)
        box = [min(p0[0], p1[0]), min(p0[1], p1[1]),
               max(p0[0], p1[0]), max(p0[1], p1[1])]
        fill = self.paint(decl, "fill", env)
        stroke = self.paint(decl, "stroke", env)
        k = self.factor(tf)
        sw = max(1, round(float(decl.get("stroke-width", 1)) * k * self.scale))
        dash_spec = decl.get("stroke-dasharray")
        pattern = fill == "pattern"
        if pattern:
            fill = None
        #  A dashed outline is the shape vocabulary's "partly filled" and the
        #  dot fill is one of the three empty states, so both have to survive
        #  into the grayscale sheet. Drawing them approximately would defeat
        #  the only check gate 3 can actually make.
        self.d.rounded_rectangle(box, radius=rx * k * self.scale, fill=fill,
                                 outline=None if dash_spec else stroke,
                                 width=0 if dash_spec else (sw if stroke else 0))
        if pattern:
            self.stipple(box, resolve("var(--empty-absent-fill)", self.tokens, env))
        if dash_spec and stroke:
            on, off = [float(v) * self.scale
                       for v in re.split(r"[ ,]+", dash_spec.strip())[:2]]
            ring = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]),
                    (box[0], box[3]), (box[0], box[1])]
            for a, b in dash(ring, (on, off)):
                self.d.line([a, b], fill=stroke, width=sw)

    def stipple(self, box, colour):
        c = to_rgb(colour)
        step = 5 * self.scale
        r = max(1, 1.2 * self.scale)
        y = box[1] + step
        while y < box[3] - 1:
            x = box[0] + step
            while x < box[2] - 1:
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=c)
                x += step
            y += step

    def draw_circle(self, el, tf, decl, env):
        cx, cy, r = (float(el.get(k, 0)) for k in ("cx", "cy", "r"))
        p = self.T((cx, cy), tf)
        k = self.factor(tf)
        rr = r * k * self.scale
        self.d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr],
                       fill=self.paint(decl, "fill", env),
                       outline=self.paint(decl, "stroke", env),
                       width=max(1, round(float(decl.get("stroke-width", 1))
                                          * k * self.scale)))

    def draw_path(self, el, tf, decl, env):
        fill = self.paint(decl, "fill", env)
        stroke = self.paint(decl, "stroke", env)
        k = self.factor(tf)
        sw = max(1, round(float(decl.get("stroke-width", 1)) * k * self.scale))
        dash_spec = decl.get("stroke-dasharray")
        for pts in parse_path(el.get("d")):
            sp = [self.T(p, tf) for p in pts]
            if fill and fill != "pattern":
                self.d.polygon(sp, fill=fill)
            if stroke:
                if dash_spec:
                    on, off = [float(v) * self.scale
                               for v in re.split(r"[ ,]+", dash_spec.strip())[:2]]
                    for a, b in dash(sp, (on, off)):
                        self.d.line([a, b], fill=stroke, width=sw)
                else:
                    self.d.line(sp, fill=stroke, width=sw, joint="curve")
            if el.get("marker-end") and stroke:
                self.arrowhead(sp[-2], sp[-1], stroke)

    def arrowhead(self, a, b, colour):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        L = 8 * self.scale
        pts = [b,
               (b[0] - L * math.cos(ang - 0.42), b[1] - L * math.sin(ang - 0.42)),
               (b[0] - L * math.cos(ang + 0.42), b[1] - L * math.sin(ang + 0.42))]
        self.d.polygon(pts, fill=colour)

    def draw_text(self, el, tf, decl, env):
        x, y = float(el.get("x", 0)), float(el.get("y", 0))
        size = round(float(str(decl.get("font-size", "16")).rstrip("px"))
                     * self.scale)
        mono = "mono" in str(decl.get("font-family", ""))
        bold = float(str(decl.get("font-weight", "400")).replace("normal", "400")) >= 600
        f = font(mono, max(6, size), bold)
        s = el.text or ""
        anchor = decl.get("text-anchor", "start")
        px, py = self.T((x, y), tf)
        w = self.d.textlength(s, font=f)
        if anchor == "middle":
            px -= w / 2
        elif anchor == "end":
            px -= w
        self.d.text((px, py), s, font=f, fill=self.paint(decl, "fill", env),
                    anchor="ls")


def render(svg_path: str, tokens: dict[str, str], scale: float = 1.0) -> Image.Image:
    return Renderer(svg_path, tokens, scale).run()


def render_grayscale(svg_path: str, tokens: dict[str, str],
                     scale: float = 1.0) -> Image.Image:
    return render(svg_path, tokens, scale).convert("L")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("svg")
    ap.add_argument("out")
    ap.add_argument("--theme", default="light")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--gray", action="store_true")
    a = ap.parse_args()
    site_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tk = read_tokens(os.path.join(site_root, "assets", "site.css"))[a.theme]
    im = render(a.svg, tk, a.scale)
    (im.convert("L") if a.gray else im).save(a.out)
    print(f"wrote {a.out}  {im.size[0]}x{im.size[1]}")
