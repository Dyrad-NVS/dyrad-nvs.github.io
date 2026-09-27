"""Convert one group of a PowerPoint slide into an SVG fragment, in slide units (slide width = 1000).

Handles what the DyRAD figure slides use: nested groups (off/ext/chOff/chExt, rot, flips), custGeom
paths (moveTo/lnTo/cubicBezTo/close), the preset shapes trapezoid, ellipse, roundRect, rect,
triangle, line and straightConnector1, solid and linear-gradient fills with the usual colour
modifiers, and outlines with dashes and triangle arrowheads. 3D bevels and glows are dropped.
Each top-level child of the group is wrapped in <g data-name="...">, so an animation can address it.

    python tools/pptx_group_to_svg.py src/figures/DyRAD_figures.pptx 2 "Group 22" > tools/teaser_road.svgfrag
"""
import colorsys
import math
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
U = 12192.0  # EMU per output unit


def mat_mul(m, n):
    return [[sum(m[i][k] * n[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def T(x, y):
    return [[1, 0, x], [0, 1, y], [0, 0, 1]]


def S(sx, sy):
    return [[sx, 0, 0], [0, sy, 0], [0, 0, 1]]


def R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def about(cx, cy, m):
    return mat_mul(T(cx, cy), mat_mul(m, T(-cx, -cy)))


def placement(xfrm):
    """Matrix placing a w x h local box at off, with the xfrm's flips and rotation about its centre."""
    off, ext = xfrm.find(A + "off"), xfrm.find(A + "ext")
    x, y = int(off.get("x")), int(off.get("y"))
    w, h = int(ext.get("cx")), int(ext.get("cy"))
    cx, cy = x + w / 2, y + h / 2
    m = T(x, y)
    fx = -1 if xfrm.get("flipH") == "1" else 1
    fy = -1 if xfrm.get("flipV") == "1" else 1
    if fx < 0 or fy < 0:
        m = mat_mul(about(cx, cy, S(fx, fy)), m)
    rot = int(xfrm.get("rot", "0")) / 60000.0
    if rot:
        m = mat_mul(about(cx, cy, R(rot)), m)
    return m, w, h


class Theme:
    def __init__(self, xml):
        self.c = {}
        for k in ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"):
            m = re.search(rf"<a:{k}>.*?(?:val|lastClr)=\"([0-9A-Fa-f]{{6}})\"", xml, re.S)
            if k in ("dk1", "lt1"):
                m = re.search(rf"<a:{k}>.*?lastClr=\"([0-9A-Fa-f]{{6}})\"", xml, re.S)
            self.c[k] = m.group(1)
        self.c.update(bg1=self.c["lt1"], tx1=self.c["dk1"], bg2=self.c["lt2"], tx2=self.c["dk2"])


def colour(el, theme):
    """(hex, opacity) of an srgbClr/schemeClr element, with lumMod/lumOff/shade/satMod/alpha applied."""
    if el is None:
        return None, 1.0
    base = el.get("val") if el.tag == A + "srgbClr" else theme.c.get(el.get("val"), "000000")
    r, g, b = (int(base[i:i + 2], 16) / 255 for i in (0, 2, 4))
    alpha = 1.0
    for mod in el:
        v = int(mod.get("val")) / 100000
        t = mod.tag.replace(A, "")
        if t == "alpha":
            alpha = v
        elif t in ("lumMod", "lumOff", "satMod"):
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            if t == "lumMod":
                l *= v
            elif t == "lumOff":
                l += v
            else:
                s *= v
            r, g, b = colorsys.hls_to_rgb(h, min(max(l, 0), 1), min(max(s, 0), 1))
        elif t == "shade":
            r, g, b = r * v, g * v, b * v
        elif t == "tint":
            r, g, b = (1 - (1 - c) * v for c in (r, g, b))
    return "#%02x%02x%02x" % tuple(int(round(min(max(c, 0), 1) * 255)) for c in (r, g, b)), alpha


def first_colour(parent):
    for t in ("srgbClr", "schemeClr"):
        e = parent.find(A + t)
        if e is not None:
            return e
    return None


def geom_path(sp_pr, w, h):
    """Path data in the shape's local box (EMU)."""
    cust = sp_pr.find(A + "custGeom")
    if cust is not None:
        d = []
        for path in cust.iter(A + "path"):
            pw, ph = float(path.get("w", w) or w), float(path.get("h", h) or h)
            sx, sy = w / pw if pw else 1, h / ph if ph else 1
            for cmd in path:
                pts = [(float(p.get("x")) * sx, float(p.get("y")) * sy) for p in cmd.iter(A + "pt")]
                tag = cmd.tag.replace(A, "")
                if tag == "moveTo":
                    d.append(("M", pts))
                elif tag == "lnTo":
                    d.append(("L", pts))
                elif tag == "cubicBezTo":
                    d.append(("C", pts))
                elif tag == "close":
                    d.append(("Z", []))
        return d, True
    prst = sp_pr.find(A + "prstGeom")
    kind = prst.get("prst") if prst is not None else "rect"
    adj = {g.get("name"): int(g.get("fmla").split()[1]) for g in prst.iter(A + "gd")} if prst is not None else {}
    ss = min(w, h)
    if kind == "trapezoid":
        x2 = ss * adj.get("adj", 25000) / 100000
        return [("M", [(0, h)]), ("L", [(x2, 0)]), ("L", [(w - x2, 0)]), ("L", [(w, h)]), ("Z", [])], True
    if kind == "triangle":
        xa = w * adj.get("adj", 50000) / 100000
        return [("M", [(0, h)]), ("L", [(xa, 0)]), ("L", [(w, h)]), ("Z", [])], True
    if kind in ("line", "straightConnector1"):
        return [("M", [(0, 0)]), ("L", [(w, h)])], False
    if kind == "ellipse":
        return ("ELLIPSE", w, h), True
    r = ss * adj.get("adj", 16667) / 100000 if kind == "roundRect" else 0
    return ("RECT", w, h, r), True


def fmt(v):
    return f"{v / U:.2f}".rstrip("0").rstrip(".")


def apply(m, x, y):
    return m[0][0] * x + m[0][1] * y + m[0][2], m[1][0] * x + m[1][1] * y + m[1][2]


def path_to_d(geom, m):
    if isinstance(geom, tuple):  # ellipse or rect: approximate with a transformed path
        if geom[0] == "ELLIPSE":
            _, w, h = geom
            k = .5522847
            cx, cy, rx, ry = w / 2, h / 2, w / 2, h / 2
            segs = [("M", [(cx + rx, cy)]),
                    ("C", [(cx + rx, cy + k * ry), (cx + k * rx, cy + ry), (cx, cy + ry)]),
                    ("C", [(cx - k * rx, cy + ry), (cx - rx, cy + k * ry), (cx - rx, cy)]),
                    ("C", [(cx - rx, cy - k * ry), (cx - k * rx, cy - ry), (cx, cy - ry)]),
                    ("C", [(cx + k * rx, cy - ry), (cx + rx, cy - k * ry), (cx + rx, cy)]), ("Z", [])]
        else:
            _, w, h, r = geom
            k = .5522847 * r
            segs = [("M", [(r, 0)]), ("L", [(w - r, 0)]), ("C", [(w - r + k, 0), (w, r - k), (w, r)]),
                    ("L", [(w, h - r)]), ("C", [(w, h - r + k), (w - r + k, h), (w - r, h)]),
                    ("L", [(r, h)]), ("C", [(r - k, h), (0, h - r + k), (0, h - r)]),
                    ("L", [(0, r)]), ("C", [(0, r - k), (r - k, 0), (r, 0)]), ("Z", [])]
        geom = segs
    out = []
    for c, pts in geom:
        out.append(c + " ".join(f"{fmt(X)},{fmt(Y)}" for X, Y in (apply(m, x, y) for x, y in pts)))
    return " ".join(out)


DASH = {"dash": "4 3", "sysDash": "3 1", "sysDot": "1 1", "dot": "1 2", "lgDash": "8 3", "dashDot": "4 3 1 3"}


class Conv:
    def __init__(self, theme):
        self.theme, self.defs, self.n = theme, [], 0

    def marker(self, col):
        self.n += 1
        mid = f"pp-ah{self.n}"
        self.defs.append(f'<marker id="{mid}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" '
                         f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{col}"/></marker>')
        return mid

    def gradient(self, gf, m, w, h):
        self.n += 1
        gid = f"pp-gr{self.n}"
        ang = int(gf.find(A + "lin").get("ang", "0")) / 60000 if gf.find(A + "lin") is not None else 0
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        cx, cy = w / 2, h / 2
        half = abs(dx) * w / 2 + abs(dy) * h / 2
        x1, y1 = apply(m, cx - dx * half, cy - dy * half)
        x2, y2 = apply(m, cx + dx * half, cy + dy * half)
        stops = []
        for gs in gf.iter(A + "gs"):
            c, a = colour(first_colour(gs), self.theme)
            stops.append(f'<stop offset="{int(gs.get("pos")) / 1000:.1f}%" stop-color="{c}" stop-opacity="{a:.3f}"/>')
        self.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{fmt(x1)}" y1="{fmt(y1)}" '
                         f'x2="{fmt(x2)}" y2="{fmt(y2)}">{"".join(stops)}</linearGradient>')
        return f"url(#{gid})"

    def shape(self, el, parent_m):
        sp_pr = el.find(P + "spPr")
        xfrm = sp_pr.find(A + "xfrm")
        pm, w, h = placement(xfrm)
        m = mat_mul(parent_m, pm)
        geom, closed = geom_path(sp_pr, w, h)
        d = path_to_d(geom, m)
        style = el.find(P + "style")
        # fill
        fill, fop = "none", 1.0
        if closed:
            sf, gf = sp_pr.find(A + "solidFill"), sp_pr.find(A + "gradFill")
            if sf is not None:
                fill, fop = colour(first_colour(sf), self.theme)
            elif gf is not None:
                fill = self.gradient(gf, m, w, h)
            elif sp_pr.find(A + "noFill") is None and style is not None:
                fill, fop = colour(first_colour(style.find(A + "fillRef")), self.theme)
        # outline
        ln = sp_pr.find(A + "ln")
        stroke, sop, sw, dash, mk = "none", 1.0, 0, None, ""
        if ln is not None and ln.find(A + "noFill") is None:
            sc = ln.find(A + "solidFill")
            if sc is not None:
                stroke, sop = colour(first_colour(sc), self.theme)
            elif style is not None:
                stroke, sop = colour(first_colour(style.find(A + "lnRef")), self.theme)
            sw = int(ln.get("w", "12700")) / U * self._scale(m)
            pd = ln.find(A + "prstDash")
            if pd is not None and pd.get("val") in DASH:
                dash = " ".join(f"{float(v) * sw:.2f}" for v in DASH[pd.get("val")].split())
            for end, attr in (("tailEnd", "marker-end"), ("headEnd", "marker-start")):
                e = ln.find(A + end)
                if e is not None and e.get("type", "none") != "none":
                    mk += f' {attr}="url(#{self.marker(stroke)})"'
        elif ln is None and style is not None and not closed:
            stroke, sop = colour(first_colour(style.find(A + "lnRef")), self.theme)
            sw = 12700 / U * self._scale(m)
        attrs = f'd="{d}" fill="{fill}"'
        if fill != "none" and fop < 1:
            attrs += f' fill-opacity="{fop:.3f}"'
        if stroke != "none":
            attrs += f' stroke="{stroke}" stroke-width="{sw:.2f}"'
            if sop < 1:
                attrs += f' stroke-opacity="{sop:.3f}"'
            if dash:
                attrs += f' stroke-dasharray="{dash}"'
            attrs += ' stroke-linejoin="round"'
        return f"<path {attrs}{mk}/>"

    @staticmethod
    def _scale(m):
        return math.sqrt(abs(m[0][0] * m[1][1] - m[0][1] * m[1][0]))

    def group(self, el, parent_m):
        gx = el.find(P + "grpSpPr").find(A + "xfrm")
        pm, _, _ = placement(gx)
        ch_off, ch_ext, ext = gx.find(A + "chOff"), gx.find(A + "chExt"), gx.find(A + "ext")
        sx = int(ext.get("cx")) / int(ch_ext.get("cx"))
        sy = int(ext.get("cy")) / int(ch_ext.get("cy"))
        # placement() maps the local box; the children live in chOff..chOff+chExt
        m = mat_mul(parent_m, mat_mul(pm, mat_mul(S(sx, sy), T(-int(ch_off.get("x")), -int(ch_off.get("y"))))))
        return m

    def children(self, el, m, top=False):
        out = []
        for ch in el:
            tag = ch.tag.replace(P, "")
            name = ch.find(".//p:cNvPr", NS)
            nm = name.get("name") if name is not None else ""
            if tag == "grpSp":
                body = "".join(self.children(ch, self.group(ch, m)))
            elif tag in ("sp", "cxnSp"):
                body = self.shape(ch, m)
            else:
                continue
            out.append(f'<g data-name="{nm}">{body}</g>' if top or tag == "grpSp" else body)
        return out


def convert(pptx, slide, group_name):
    z = zipfile.ZipFile(pptx)
    theme = Theme(z.read("ppt/theme/theme1.xml").decode())
    root = ET.fromstring(z.read(f"ppt/slides/slide{slide}.xml"))
    grp = next(g for g in root.iter(P + "grpSp") if g.find(".//p:cNvPr", NS).get("name") == group_name)
    c = Conv(theme)
    # geometry stays in EMU through the matrices; fmt() divides by U on output
    body = "".join(c.children(grp, c.group(grp, [[1, 0, 0], [0, 1, 0], [0, 0, 1]]), top=True))
    return f'<defs>{"".join(c.defs)}</defs>{body}'


if __name__ == "__main__":
    print(convert(sys.argv[1], int(sys.argv[2]), sys.argv[3]))
