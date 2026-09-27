"""Write the animated method + motion-model figure (inline SVG) into index.html between the
METHOD markers.

Layout follows slide 1 of DyRAD_figures.pptx (method overview) in the units of the paper's
Fig. 2 rendered at 1113 px wide; the motion-model callout follows slide 3. Radar panels and the
two point clouds are crops of that figure, with the coloured overlays (seeds, track points,
boxes, arrows) removed so they can be drawn and animated here. Overlay positions were measured
from the same crop and live in tools/method_overlays.json.
Run: python tools/build_method.py
"""
import json
import pathlib
import random
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG = "static/images/method/"
META = json.loads((ROOT / "tools/method_overlays.json").read_text())

TEAL, TEAL_F = "#2f7f93", "#cfe8ef"
PURP, PURP_F = "#6a2a8c", "#e6d8f0"
CRIM, CRIM_F = "#8f1d3a", "#f4c3cd"
GRN, GRN_F = "#3c8a32", "#d3ecca"
GREY, RED = "#7a7a7a", "#cc1f2f"


def box(x, y, w, h, stroke, fill, title, hh=26, cls=""):
    lines = title.split("\n")
    ty = y + (hh / 2) - (len(lines) - 1) * 8 + 5
    t = "".join(f'<text x="{x + w / 2}" y="{ty + i * 16}" text-anchor="middle" class="hd">{ln}</text>' for i, ln in enumerate(lines))
    return (f'<g class="{cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" stroke="{stroke}" stroke-width="1.6"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{hh}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>{t}')


def arrow(d, cls, red=False):
    col = RED if red else GREY
    dash = ' stroke-dasharray="7 5"' if red else ""
    mk = "mt-ahr" if red else "mt-ahg"
    return f'<path class="{cls}" d="{d}" fill="none" stroke="{col}" stroke-width="1.7"{dash} marker-end="url(#{mk})"/>'


def seeds():
    rnd = random.Random(3)
    out = []
    for r in META["init"]["red"]:
        if r["w"] < 4:
            continue
        n = int(r["w"] * r["h"] / 2.2)
        for _ in range(n):
            out.append(f'<circle cx="{r["x"] + rnd.random() * r["w"]:.1f}" cy="{r["y"] + rnd.random() * r["h"]:.1f}" r="1.1"/>')
    return "".join(out)


def blues(key):
    pts = META[key]["blue"]
    if key == "scene":  # one track point was split in two by the arrow tip
        pts = [p for p in pts if p["a"] > 150] + [{"cx": 549.15, "cy": 149.4}]
    r = 1.7 if key == "init" else 2.8
    return "".join(f'<circle class="kn" style="--i:{i}" cx="{p["cx"]}" cy="{p["cy"]}" r="{r}"/>' for i, p in enumerate(sorted(pts, key=lambda p: -p["cy"])))


def objects():
    # two annotated objects in the learned scene: box, reflectors, green velocity arrow
    reds = META["scene"]["redpts"]
    out = []
    for i, d in enumerate(sorted(META["scene"]["dark"], key=lambda d: d["cy"])):
        rp = [p for p in reds if d["x"] - 2 <= p[0] <= d["x"] + d["w"] + 2 and d["y"] - 2 <= p[1] <= d["y"] + d["h"] + 2]
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.4" fill="#e3122f"/>' for x, y in rp)
        cx = d["x"] + d["w"] / 2
        out.append(f'<g class="obj obj{i}"><rect x="{d["x"] + 1.5}" y="{d["y"] + 1.5}" width="{d["w"] - 3}" height="{d["h"] - 3}" fill="none" stroke="#1b2130" stroke-width="2.6"/>'
                   f'{dots}<line x1="{cx}" y1="{d["y"] - 1}" x2="{cx}" y2="{d["y"] - 16}" stroke="#16813a" stroke-width="2.6" marker-end="url(#mt-ahv)"/></g>')
    return "".join(out)


def motion_callout():
    # slide 3 geometry, in the 792 x 540 px space of the paper's Fig. 3 crop
    K = [(78, 180), (168, 210), (265, 188), (485, 207), (618, 172), (711, 186)]
    poly = " ".join(f"{x},{y}" for x, y in K)
    knots = "".join(f'<circle cx="{x}" cy="{y}" r="{11 if i in (0, 5) else 9}" fill="#2a74e0"/>' for i, (x, y) in enumerate(K))
    rings = "".join(f'<circle class="ring" cx="{x}" cy="{y}" r="15" fill="none" stroke="#111" stroke-width="4" stroke-dasharray="7 6"/>' for x, y in K[1:5])
    labels = [("c", "j,k−1", 128, 170), ("c", "j,k", 232, 148), ("c", "j,k+1", 462, 168), ("c", "j,k+2", 586, 136)]
    lab = "".join(f'<text x="{x}" y="{y}" class="mlab"><tspan font-style="italic">{a}</tspan><tspan dy="7" font-size="20" font-style="italic">{b}</tspan></text>' for a, b, x, y in labels)
    refl = [(-44, -24), (-12, -16), (6, 14), (-40, 18), (30, 26), (-22, 6)]
    rdots = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#e3122f"/>' for x, y in refl)
    leg_y = 330
    legend = f'''
      <rect x="12" y="{leg_y - 22}" width="768" height="210" rx="10" fill="#f0f1f3"/>
      <circle cx="46" cy="{leg_y + 18}" r="7" fill="#e3122f"/><text x="72" y="{leg_y + 26}" class="mleg">Reflector <tspan font-style="italic">x</tspan><tspan dy="6" font-size="16" font-style="italic">i</tspan><tspan dy="-6">(t)</tspan></text>
      <line x1="30" y1="{leg_y + 64}" x2="62" y2="{leg_y + 64}" stroke="#7a3fb6" stroke-width="3" marker-end="url(#mt-ahm)" marker-start="url(#mt-ahm)"/><text x="72" y="{leg_y + 72}" class="mleg">Offset from object origin <tspan font-style="italic">μ</tspan><tspan dy="6" font-size="16" font-style="italic">i</tspan></text>
      <rect x="32" y="{leg_y + 100}" width="28" height="18" fill="none" stroke="#1b2130" stroke-width="3"/><text x="72" y="{leg_y + 116}" class="mleg">Bounding box (annotation)</text>
      <circle cx="46" cy="{leg_y + 154}" r="8" fill="#2a74e0"/><text x="72" y="{leg_y + 162}" class="mleg">Track points (learned)</text>
      <line x1="420" y1="{leg_y + 18}" x2="458" y2="{leg_y + 18}" stroke="#8a8a8a" stroke-width="4"/><circle cx="439" cy="{leg_y + 18}" r="6" fill="#8a8a8a"/><text x="472" y="{leg_y + 26}" class="mleg">Track <tspan font-style="italic">p</tspan><tspan dy="6" font-size="16" font-style="italic">j</tspan><tspan dy="-6">(t)</tspan></text>
      <line x1="420" y1="{leg_y + 64}" x2="458" y2="{leg_y + 64}" stroke="#2f9a3c" stroke-width="5" marker-end="url(#mt-ahv)"/><text x="472" y="{leg_y + 72}" class="mleg">Velocity <tspan font-weight="700">v</tspan><tspan dy="6" font-size="16" font-style="italic">j</tspan><tspan dy="-6">(t) (LS slope)</tspan></text>
      <circle cx="439" cy="{leg_y + 110}" r="12" fill="none" stroke="#111" stroke-width="4" stroke-dasharray="7 6"/><text x="472" y="{leg_y + 118}" class="mleg">Points contributing to <tspan font-weight="700">v</tspan><tspan dy="6" font-size="16" font-style="italic">j</tspan><tspan dy="-6">(t)</tspan></text>
      <text x="420" y="{leg_y + 162}" class="mleg" font-weight="600">x<tspan dy="6" font-size="16">i</tspan><tspan dy="-6">(t) = p</tspan><tspan dy="6" font-size="16">j</tspan><tspan dy="-6">(t) + R</tspan><tspan dy="6" font-size="16">j</tspan><tspan dy="-6">(t) μ</tspan><tspan dy="6" font-size="16">i</tspan></text>'''
    return f'''
  <g class="mcall" aria-hidden="true">
    <path class="mlink" d="M537,240 L655,200" stroke="#1b2130" stroke-width="1.2" stroke-dasharray="3 3" fill="none"/>
    <rect x="655" y="44" width="450" height="312" rx="8" fill="#fff" stroke="#9a9a9a" stroke-width="1.2" filter="url(#mt-sh)"/>
    <g transform="translate(662 58) scale(.555)">
      <text x="396" y="20" text-anchor="middle" class="mtitle">Motion model of object <tspan font-style="italic">j</tspan> at time <tspan font-style="italic">t</tspan> ∈ [<tspan font-style="italic">t</tspan><tspan dy="7" font-size="20" font-style="italic">k</tspan><tspan dy="-7">, </tspan><tspan font-style="italic">t</tspan><tspan dy="7" font-size="20" font-style="italic">k+1</tspan><tspan dy="-7">]</tspan></text>
      <polyline points="{poly}" fill="none" stroke="#8a8a8a" stroke-width="5"/>
      {rings}{knots}{lab}
      <g id="mt-body">
        <rect x="-66" y="-40" width="132" height="80" fill="none" stroke="#1b2130" stroke-width="3.5"/>
        {rdots}
        <line id="mt-mu" x1="0" y1="0" x2="-40" y2="18" stroke="#7a3fb6" stroke-width="3" marker-end="url(#mt-ahm)"/>
      </g>
      <line id="mt-vel" x1="0" y1="0" x2="0" y2="0" stroke="#2f9a3c" stroke-width="6" marker-end="url(#mt-ahv)"/>
      <circle id="mt-p" r="10" fill="#8a8a8a"/>
      {legend}
    </g>
  </g>'''


def svg():
    mk = lambda i, c, s=5: (f'<marker id="{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="{s}" markerHeight="{s}" orient="auto-start-reverse">'
                            f'<path d="M0 0L10 5L0 10z" fill="{c}"/></marker>')
    return f'''<svg class="mt-svg" viewBox="0 0 1113 367" role="img" aria-labelledby="mt-title">
  <title id="mt-title">DyRAD overview. Inputs: recorded RAD tensors, sensor poses, object bounding boxes and the radar processing chain. Initialization seeds point reflectors and object tracks and fixes the sensor PSF. Optimization fits reflectors and tracks through the differentiable RAD renderer, with each object moving rigidly along its learned track. Inference renders RAD tensors at new times and poses.</title>
  <defs>{mk("mt-ahg", GREY)}{mk("mt-ahr", RED)}{mk("mt-ahv", "#16813a", 3.2)}{mk("mt-ahm", "#7a3fb6", 3.5)}
    <clipPath id="mt-sweep"><circle class="sweep" cx="342" cy="226" r="190"/></clipPath>
    <clipPath id="mt-wipe"><rect class="wipe" x="870" y="236" width="230" height="120"/></clipPath>
    <clipPath id="mt-psfclip"><rect class="psfwipe" x="280" y="284" width="124" height="54"/></clipPath>
    <filter id="mt-sh" x="-5%" y="-5%" width="110%" height="115%"><feDropShadow dx="0" dy="3" stdDeviation="5" flood-opacity=".18"/></filter>
  </defs>

  <!-- 1 · input -->
  <g class="st-in">
    {box(10, 48, 232, 156, TEAL, TEAL_F, "")}<text x="126" y="66" text-anchor="middle" class="hd">Radar Tensors {{<tspan font-style="italic">Y</tspan><tspan dy="4" class="sb">t</tspan><tspan dy="-4">, </tspan><tspan font-style="italic">P</tspan><tspan dy="4" class="sb">t</tspan><tspan dy="-4" dx="1.5">}}</tspan><tspan dy="-6" dx=".5" class="sb">T</tspan><tspan dy="10" dx="-5" class="sb">t=1</tspan></text></g>
    <image href="{IMG}tensors.jpg" x="14" y="78" width="224" height="124"/>
    {box(10, 210, 232, 28, TEAL, TEAL_F, "Object Bounding Boxes", hh=28)}</g>
    {box(10, 268, 232, 72, TEAL, TEAL_F, "Radar Processing Chain")}
      <text x="22" y="314" class="it">Doppler / DDMA → Range FFT</text><text x="22" y="332" class="it">→ Azimuth beamforming</text></g>
  </g>

  <!-- 2 · scene initialization -->
  <g class="st-init">
    {arrow("M242,140 H274", "fl a-in")}{arrow("M242,224 H274", "fl a-in")}{arrow("M242,304 H274", "fl a-in")}
    {box(276, 48, 132, 180, PURP, PURP_F, "Scene\nInitialization", hh=42)}</g>
    <image class="cloud" href="{IMG}init_bg.jpg" x="279" y="94" width="126" height="132" clip-path="url(#mt-sweep)"/>
    <g class="seeds" fill="#e3122f">{seeds()}</g>
    <g class="knots-i" fill="#2a74e0">{blues("init")}</g>
    {box(276, 240, 130, 100, PURP, PURP_F, "Fixed Sensor\nModel", hh=42)}</g>
    <image class="psf" href="{IMG}psf.png" x="280" y="284" width="124" height="54" clip-path="url(#mt-psfclip)"/>
    {arrow("M408,158 H436", "fl a-init")}
  </g>

  <!-- 3 · optimization -->
  <g class="st-opt">
    {box(438, 48, 198, 292, CRIM, CRIM_F, "Learned Scene", hh=28)}</g>
    <image class="scene" href="{IMG}scene_bg.jpg" x="441" y="80" width="192" height="257"/>
    <g class="knots-s" fill="#2a74e0">{blues("scene")}</g>
    {objects()}
    <rect x="700" y="238" width="146" height="44" rx="5" fill="#f0aeb9" stroke="#e38d9c" stroke-width="1"/>
    <text x="773" y="266" text-anchor="middle" class="hd" font-size="15">RAD Renderer</text>
    {arrow("M636,252 H698", "fl a-opt")}{arrow("M341,340 V356 H773 V284", "fl a-opt")}{arrow("M773,238 V206", "fl a-opt")}
    {box(670, 48, 232, 156, CRIM, CRIM_F, "")}<text x="786" y="66" text-anchor="middle" class="hd">Radar Predictions {{<tspan font-style="italic">Ŷ</tspan><tspan dy="4" class="sb">t</tspan><tspan dy="-4">, </tspan><tspan font-style="italic">P</tspan><tspan dy="4" class="sb">t</tspan><tspan dy="-4" dx="1.5">}}</tspan><tspan dy="-6" dx=".5" class="sb">T</tspan><tspan dy="10" dx="-5" class="sb">t=1</tspan></text></g>
    <image href="{IMG}pred.jpg" x="674" y="78" width="224" height="124"/>
    <g class="loss"><rect x="452" y="8" width="184" height="32" rx="5" fill="#f5c2cb" stroke="#e39aa7"/>
      <text x="544" y="29" text-anchor="middle" class="hd" font-size="14.5"><tspan font-style="italic">ℒ</tspan> = <tspan font-style="italic">ℒ</tspan><tspan dy="4" class="sb">rec</tspan><tspan dy="-4"> + </tspan><tspan font-style="italic">λ</tspan><tspan dy="4" class="sb">int</tspan><tspan dy="-4" font-style="italic"> ℒ</tspan><tspan dy="4" class="sb">int</tspan></text></g>
    {arrow("M124,48 V24 H450", "gr", red=True)}{arrow("M638,24 H786 V46", "gr", red=True)}{arrow("M795,206 V236", "gr", red=True)}{arrow("M698,266 H638", "gr", red=True)}
  </g>

  <!-- 4 · novel views -->
  <g class="st-nv">
    {arrow("M846,260 H864", "fl a-nv")}
    {box(866, 210, 237, 148, GRN, GRN_F, "", hh=24)}<text x="984" y="227" text-anchor="middle" class="hd">Novel view <tspan font-style="italic">Ŷ</tspan><tspan dy="4" class="sb">t*</tspan><tspan dy="-4">, </tspan><tspan font-style="italic">P</tspan><tspan dy="4" class="sb">t*</tspan></text></g>
    <image class="novel" href="{IMG}novel.jpg" x="870" y="238" width="230" height="118" clip-path="url(#mt-wipe)"/>
  </g>

  <g class="legendbox"><rect x="930" y="42" width="173" height="58" rx="8" fill="#fff" stroke="#bdbdbd" stroke-width="1.4"/>
    <text x="944" y="66" class="lgd" fill="#7a7a7a">Data flow</text><line x1="1046" y1="62" x2="1090" y2="62" stroke="{GREY}" stroke-width="2"/>
    <text x="944" y="88" class="lgd" fill="{RED}">Gradient flow</text><line x1="1046" y1="84" x2="1090" y2="84" stroke="{RED}" stroke-width="2" stroke-dasharray="6 4"/></g>

  {motion_callout()}
</svg>'''


if __name__ == "__main__":
    html = (ROOT / "index.html").read_text()
    assert "<!--METHOD-SVG-->" in html, "markers missing"
    html = re.sub(r"(<!--METHOD-SVG-->).*?(<!--/METHOD-SVG-->)", lambda m: m.group(1) + svg() + m.group(2), html, flags=re.S)
    (ROOT / "index.html").write_text(html)
    print("method written")
