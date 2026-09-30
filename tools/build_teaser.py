"""Write the animated teaser (inline SVG) into index.html between the TEASER markers.

Geometry is in slide units (the 16:9 slide is 1000 wide), transcribed from slide 2 of
DyRAD_figures.pptx; radar panels are crops of that slide's own graphic (image4.svg).
Run: python tools/build_teaser.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG = "static/images/teaser/"

# frame x of each panel on slide 2; the left column sits further left than on the slide so the
# shifted ego car's ghost clears it, and the panel arrows move with their panel
SLIDE_X = {"gt": 30, "edit": 357, "shift": 30, "hires": 357}

PANELS = [  # key, title, colour token, frame x, frame y
    ("gt", "Ground Truth", "--t-gt", 4, 100),
    ("edit", "Repositioned Object", "--t-edit", 357, 100),
    ("shift", "Lateral Sensor Shift", "--t-nv", 4, 262),
    ("hires", "High Res Sensor", "--t-cfg", 357, 262),
]


EMU = 12192  # EMU per slide unit (the 16:9 slide is 12192000 EMU = 1000 units wide)
# arrows drawn on the RA panels themselves (slide 2 connectors 76, 77, 81): (off x, off y, ext cx, ext cy) in EMU,
# all flipV, so each runs from the bottom-left to the top-right of its box with the head at the top-right end
PANEL_ARROWS = {
    "shift": ("#60C5DE", [(1471571, 4605557, 160665, 33645), (1402781, 4288823, 110816, 31699)]),
    "edit": ("#F3AAB5", [(5510249, 2443160, 145921, 191946)]),
}


def panel_arrows(key, dx=0):
    if key not in PANEL_ARROWS:
        return ""
    col, arrs = PANEL_ARROWS[key]
    lines = "".join(
        f'<line x1="{ox / EMU + dx:.1f}" y1="{(oy + cy) / EMU:.1f}" x2="{(ox + cx) / EMU + dx:.1f}" y2="{oy / EMU:.1f}" '
        f'stroke="{col}" stroke-width="1.56" marker-end="url(#tz-pa-{key})"/>' for ox, oy, cx, cy in arrs)
    return (f'\n    <marker id="tz-pa-{key}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" '
            f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{col}"/></marker>'
            f'\n    <g class="parr">{lines}</g>')


def panel(key, title, tok, x, y):
    # image placement and type sizes from slide 2: the graphic spans 181 x 115 units at (x+17, y+23),
    # titles are 14 pt bold and axis labels 9 pt Helvetica (1 pt = 1.04 units, panel groups scale ~1.06)
    k = 1.06
    ix, iy, iw, ih, gap, dw = x + 17.7, y + 23.8, 146.9 * k, 107.3 * k, 3.6 * k, 18.9 * k
    return f'''
  <g class="panel p-{key}" style="--c:var({tok})">
    <rect x="{x}" y="{y}" width="214" height="154" rx="6" fill="#fff" stroke="var(--c)" stroke-width="1.8"/>
    <text x="{x + 6}" y="{y + 17}" class="ptitle" fill="var(--c)">{title}</text>
    <image href="{IMG}ra_{key}.jpg" x="{ix:.1f}" y="{iy:.1f}" width="{iw:.1f}" height="{ih:.1f}" preserveAspectRatio="none"/>
    <image href="{IMG}d_{key}.jpg" x="{ix + iw + gap:.1f}" y="{iy:.1f}" width="{dw:.1f}" height="{ih:.1f}" preserveAspectRatio="none"/>
    <text class="ax" transform="translate({x + 12} {iy + ih / 2:.1f}) rotate(-90)" text-anchor="middle">Range [m]</text>
    <text class="ax" x="{ix + iw / 2:.1f}" y="{iy + ih + 11:.1f}" text-anchor="middle">Azimuth°</text>
    <text class="ax" x="{ix + iw + gap + dw / 2:.1f}" y="{iy + ih + 11:.1f}" text-anchor="middle">Doppler</text>{panel_arrows(key, x - SLIDE_X[key])}
  </g>'''


ROAD_CLASSES = {  # slide 2 names -> animation roles (see the stage rules in index.html)
    "Group 26": "carB", "Group 31": "carA", "Group 28": "ego", "Oval 39": "radar",
    "Group 32": "ghostA", "Straight Arrow Connector 25": "arrA",
    "Group 29": "ghostE", "Oval 30": "ghostE", "Straight Arrow Connector 27": "arrE",
    "Triangle 33": "glow",
    **{f"Straight Arrow Connector {i}": "ray" for i in range(34, 39)},
}


def road():
    """The road sketch exactly as drawn on slide 2 (tools/teaser_road.svgfrag, made by
    tools/pptx_group_to_svg.py), with each element tagged by its role in the animation."""
    frag = (ROOT / "tools/teaser_road.svgfrag").read_text()
    frag = re.sub(r'<g data-name="([^"]+)">', lambda m: f'<g class="{ROAD_CLASSES.get(m.group(1), "rd")}" data-name="{m.group(1)}">', frag)
    return f'<g class="road">{frag}</g>'


def plot():
    X0, X1, Y0, S = 628, 896, 380, 63.75
    def px(h):
        return X0 + h * (X1 - X0)
    def py(v):
        return Y0 - (v - 23) * S
    grid = []
    for h in (0, .2, .4, .6, .8, 1.0):
        grid.append(f'<line x1="{px(h):.1f}" y1="{py(27.35):.1f}" x2="{px(h):.1f}" y2="{Y0 + 8}" class="grid"/>'
                    f'<text class="tick" x="{px(h):.1f}" y="{Y0 + 22}" text-anchor="middle">{h:.1f}</text>')
    for v in (23, 24, 25, 26, 27):
        grid.append(f'<line x1="{X0 - 6}" y1="{py(v):.1f}" x2="{X1}" y2="{py(v):.1f}" class="grid"/>'
                    f'<text class="tick" x="{X0 - 10}" y="{py(v) + 4:.1f}" text-anchor="end">{v}</text>')
    # (method, hit rate, PSNR) from paper Tables 1 and 2 (RADIal RAD PSNR, detection hit rate)
    pts = [("rs", .036, 23.56, .064, 23.92), ("rf", .269, 23.13, .181, 24.43), ("dy", .907, 25.88, .917, 26.53)]
    marks = []
    for i, (k, h0, v0, h1, v1) in enumerate(pts):
        r = 9 if k == "dy" else 7
        marks.append(f'<circle class="pt pt-{k}" style="--d:{i * .35:.2f}s" cx="{px(h0):.1f}" cy="{py(v0):.1f}" r="{r}" fill="var(--k)" stroke="var(--k2)" stroke-width="1.5"/>'
                     f'<circle class="pt pt-{k}" style="--d:{i * .35 + .15:.2f}s" cx="{px(h1):.1f}" cy="{py(v1):.1f}" r="{r}" fill="#fff" stroke="var(--k2)" stroke-width="{3 if k == "dy" else 2}"/>')
    lg = 138
    legend = f'''
    <g class="legend">
      <rect x="{X0 + 4}" y="{lg - 14}" width="150" height="112" fill="#fff" fill-opacity=".9"/>
      <circle cx="{X0 + 16}" cy="{lg}" r="7" fill="#d0335b" stroke="#a8123a" stroke-width="1.5"/><text x="{X0 + 30}" y="{lg + 4}" class="lg" fill="#b8173f" font-weight="700">DyRAD (ours)</text>
      <circle cx="{X0 + 16}" cy="{lg + 19}" r="6" fill="#cf8ee6"/><text x="{X0 + 30}" y="{lg + 23}" class="lg" fill="#9a45c0">RadarSplat</text>
      <circle cx="{X0 + 16}" cy="{lg + 38}" r="6" fill="#8fcbe3"/><text x="{X0 + 30}" y="{lg + 42}" class="lg" fill="#2f86ad">RadarFields</text>
      <circle cx="{X0 + 16}" cy="{lg + 64}" r="6" fill="#666"/><text x="{X0 + 30}" y="{lg + 68}" class="lg" fill="#555">on-path</text>
      <circle cx="{X0 + 16}" cy="{lg + 83}" r="5.5" fill="#fff" stroke="#666" stroke-width="2"/><text x="{X0 + 30}" y="{lg + 87}" class="lg" fill="#555">off-path, +2 m</text>
    </g>'''
    return f'''
  <g class="plot">
    <rect x="{X0 - 8}" y="{py(27.35):.1f}" width="{X1 - X0 + 8}" height="{Y0 + 8 - py(27.35):.1f}" fill="#fff" stroke="#8a8a8a" stroke-width="1"/>
    {''.join(grid)}
    <text class="axl" x="{(X0 + X1) / 2}" y="{Y0 + 40}" text-anchor="middle">Detection (Hit Rate) →</text>
    <text class="axl" transform="translate({X0 - 36} {(py(27.35) + Y0) / 2:.1f}) rotate(-90)" text-anchor="middle">RAD PSNR [dB] →</text>
    {legend}
    <g style="--k:#cf8ee6;--k2:#b56bd6">{marks[0]}</g>
    <g style="--k:#8fcbe3;--k2:#5aaed0">{marks[1]}</g>
    <g style="--k:#d0335b;--k2:#a8123a">{marks[2]}</g>
  </g>'''


def svg():
    arrow = lambda i, c: (f'<marker id="tz-ah-{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" '
                          f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{c}"/></marker>')
    return f'''<svg class="tz-svg" viewBox="-6 92 926 336" role="img" aria-labelledby="tz-title">
  <title id="tz-title">DyRAD re-simulation: from a measured radar frame, DyRAD renders a laterally shifted sensor, a repositioned object and a higher-resolution sensor, and scores higher RAD PSNR and detection hit rate than RadarSplat and RadarFields.</title>
  <defs></defs>
  {road()}
  {''.join(panel(*p) for p in PANELS)}
  {plot()}
</svg>'''


if __name__ == "__main__":
    html = (ROOT / "index.html").read_text()
    new = re.sub(r"(<!--TEASER-SVG-->).*?(<!--/TEASER-SVG-->)", lambda m: m.group(1) + svg() + m.group(2), html, flags=re.S)
    assert new != html or "<!--TEASER-SVG-->" in html, "markers missing"
    (ROOT / "index.html").write_text(new)
    print("teaser written")
