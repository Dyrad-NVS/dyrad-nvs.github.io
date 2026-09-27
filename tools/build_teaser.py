"""Write the animated teaser (inline SVG) into index.html between the TEASER markers.

Geometry is in slide units (the 16:9 slide is 1000 wide), transcribed from slide 2 of
DyRAD_figures.pptx; radar panels are crops of that slide's own graphic (image4.svg).
Run: python tools/build_teaser.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG = "static/images/teaser/"

PANELS = [  # key, title, colour token, frame x, frame y
    ("gt", "Ground Truth", "--t-gt", 30, 100),
    ("edit", "Repositioned Object", "--t-edit", 357, 100),
    ("shift", "Lateral Sensor Shift", "--t-nv", 30, 262),
    ("hires", "High Res Sensor", "--t-cfg", 357, 262),
]


def panel(key, title, tok, x, y):
    ix, iy, iw, ih, dw = x + 20, y + 23, 152, 111, 19
    return f'''
  <g class="panel p-{key}" style="--c:var({tok})">
    <rect x="{x}" y="{y}" width="214" height="154" rx="6" fill="#fff" stroke="var(--c)" stroke-width="1.8"/>
    <text x="{x + 8}" y="{y + 15}" class="ptitle" fill="var(--c)">{title}</text>
    <image href="{IMG}ra_{key}.jpg" x="{ix}" y="{iy}" width="{iw}" height="{ih}" preserveAspectRatio="none"/>
    <image href="{IMG}d_{key}.jpg" x="{ix + iw + 3}" y="{iy}" width="{dw}" height="{ih}" preserveAspectRatio="none"/>
    <text class="ax" transform="translate({x + 14} {iy + ih / 2}) rotate(-90)" text-anchor="middle">Range [m]</text>
    <text class="ax" x="{ix + iw / 2}" y="{iy + ih + 11}" text-anchor="middle">Azimuth°</text>
    <text class="ax" x="{ix + iw + 3 + dw / 2}" y="{iy + ih + 11}" text-anchor="middle">Doppler</text>
  </g>'''


def car(cls, x, y, w, h, fill, ghost=False, stroke=None):
    if ghost:
        body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{w * .22:.1f}" fill="#fff" fill-opacity=".85" '
                f'stroke="{stroke}" stroke-width="1.6" stroke-dasharray="4 3"/>')
        win = f'fill="{stroke}" fill-opacity=".35"'
    else:
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{w * .22:.1f}" fill="{fill}"/>'
        win = 'fill="#fff" fill-opacity=".45"'
    return (f'<g class="{cls}">{body}'
            f'<rect x="{x + w * .16:.1f}" y="{y + h * .2:.1f}" width="{w * .68:.1f}" height="{h * .22:.1f}" rx="2" {win}/>'
            f'<rect x="{x + w * .16:.1f}" y="{y + h * .8:.1f}" width="{w * .68:.1f}" height="{h * .09:.1f}" rx="1.5" {win}/></g>')


def road():
    ox, oy = 329, 352  # radar on the ego car's nose
    base = [-24, -12, 0, 12, 24]
    extra = [-30, -18, -6, 6, 18, 30]
    def ray(dx, cls):
        return (f'<line class="{cls}" x1="{ox}" y1="{oy}" x2="{ox + dx}" y2="{oy - 42}" stroke="#2e8b3a" '
                f'stroke-width="1.3" marker-end="url(#tz-ah-g)"/>')
    rays = "".join(ray(d, "ray") for d in base) + "".join(ray(d, "ray ray-x") for d in extra)
    return f'''
  <g class="road">
    <polygon points="270,120 332,120 354,418 248,418" fill="#dcdcdc"/>
    <line x1="301" y1="120" x2="301" y2="418" stroke="#fff" stroke-width="3" stroke-dasharray="11 9"/>
    <polygon class="glow" points="{ox},{oy} 296,262 362,262" fill="url(#tz-glow)"/>
    {car("carB", 318, 140, 21, 33, "#b8304f")}
    {car("carA", 314, 226, 30, 47, "#b8304f")}
    <g class="ghostA">{car("", 269, 168, 24, 38, None, True, "#d0506e")}</g>
    <line class="arrA" x1="316" y1="236" x2="292" y2="206" stroke="#d0506e" stroke-width="1.8" marker-end="url(#tz-ah-p)"/>
    {car("ego", 312, 350, 34, 54, "#3a3a3a")}
    <g class="ghostE">{car("", 258, 350, 34, 54, None, True, "#3d8fa6")}<circle cx="275" cy="349" r="3" fill="#3d8fa6"/></g>
    <line class="arrE" x1="311" y1="382" x2="294" y2="377" stroke="#3d8fa6" stroke-width="1.8" marker-end="url(#tz-ah-t)"/>
    {rays}
    <circle cx="{ox}" cy="{oy}" r="3" fill="#2e8b3a"/>
  </g>'''


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
    return f'''<svg class="tz-svg" viewBox="20 92 900 336" role="img" aria-labelledby="tz-title">
  <title id="tz-title">DyRAD re-simulation: from a measured radar frame, DyRAD renders a laterally shifted sensor, a repositioned object and a higher-resolution sensor, and scores higher RAD PSNR and detection hit rate than RadarSplat and RadarFields.</title>
  <defs>{arrow("p", "#d0506e")}{arrow("t", "#3d8fa6")}{arrow("g", "#2e8b3a")}
    <linearGradient id="tz-glow" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff6b0" stop-opacity=".9"/><stop offset="1" stop-color="#fff6b0" stop-opacity="0"/></linearGradient>
  </defs>
  {''.join(panel(*p) for p in PANELS)}
  {road()}
  {plot()}
</svg>'''


if __name__ == "__main__":
    html = (ROOT / "index.html").read_text()
    new = re.sub(r"(<!--TEASER-SVG-->).*?(<!--/TEASER-SVG-->)", lambda m: m.group(1) + svg() + m.group(2), html, flags=re.S)
    assert new != html or "<!--TEASER-SVG-->" in html, "markers missing"
    (ROOT / "index.html").write_text(new)
    print("teaser written")
