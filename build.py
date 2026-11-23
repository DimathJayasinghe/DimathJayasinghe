"""Generates the profile README SVGs (modern terminal theme), in light and dark variants.

Fonts (IBM Plex Sans, JetBrains Mono — both SIL OFL) are subsetted and embedded so every
viewer sees the same type. Requires: fonttools, brotli.
"""
import base64, glob, io, math, os
from fontTools.ttLib import TTFont
from fontTools import subset
import logging; logging.getLogger("fontTools").setLevel(logging.ERROR)

FONT_FILES = {
    "sans400": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Regular.ttf",
    "sans500": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-Medium.ttf",
    "sans600": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSans-SemiBold.ttf",
    "mono400": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
    "mono500": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf",
}
FONTS = {k: TTFont(v) for k, v in FONT_FILES.items()}
FAMILY = {"sans": "PS, 'IBM Plex Sans', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
          "mono": "JM, 'JetBrains Mono', ui-monospace, Consolas, Menlo, monospace"}

def width(text, fk, size):
    f = FONTS[fk]; cmap = f.getBestCmap(); hm = f["hmtx"]; upm = f["head"].unitsPerEm
    return sum(hm[cmap.get(ord(c), cmap[32])][0] for c in text) / upm * size

THEMES = {
    "dark": dict(win="#10161D", bar="#161B22", border="#30363D", node="#161B22", text="#E6EDF3",
                 muted="#8B949E", faint="#6E7681", edge="#30363D", tint=0.10,
                 blue="#4C8DFF", purple="#A371F7", green="#3FB950", orange="#F0883E",
                 pink="#F778BA", cyan="#39C5CF", yellow="#E3B341", red="#F85149"),
    "light": dict(win="#FFFFFF", bar="#F6F8FA", border="#D0D7DE", node="#F6F8FA", text="#1F2328",
                  muted="#59636E", faint="#8C959F", edge="#D0D7DE", tint=0.08,
                  blue="#0969DA", purple="#8250DF", green="#1A7F37", orange="#BC4C00",
                  pink="#BF3989", cyan="#1B7C83", yellow="#9A6700", red="#CF222E"),
}

def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Doc:
    def __init__(self, theme):
        self.C = THEMES[theme]; self.used = {}; self.parts = []; self.uid = 0
    def __iadd__(self, s): self.parts.append(s); return self
    def id(self, p="g"): self.uid += 1; return f"{p}{self.uid}"
    def text(self, x, y, t, size=15, fill=None, font="sans", weight=400, anchor="start", extra=""):
        fk = f"{font}{weight}"
        self.used.setdefault(fk, set()).update(t)
        fill = fill or self.C["text"]
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FAMILY[font]}" font-size="{size}" '
                f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" xml:space="preserve" {extra}>{esc(t)}</text>')
    def fontcss(self):
        css = ""
        for fk, chars in self.used.items():
            opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern"]
            opts.name_IDs = []; opts.notdef_outline = True
            f = TTFont(FONT_FILES[fk]); sub = subset.Subsetter(opts)
            sub.populate(text="".join(sorted(chars)) + " "); sub.subset(f)
            buf = io.BytesIO(); f.flavor = "woff2"; f.save(buf)
            fam = "PS" if fk.startswith("sans") else "JM"
            css += (f"@font-face{{font-family:{fam};font-weight:{fk[-3:]};"
                    f"src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}")
        return css
    def svg(self, w, h):
        style = ("<style>" + self.fontcss() + """
@keyframes dash{to{stroke-dashoffset:-20}}
@keyframes pulse{0%{r:4;opacity:.7}100%{r:11;opacity:0}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
.flow{stroke-dasharray:4 6;animation:dash 1.1s linear infinite}
.pulse{animation:pulse 1.8s ease-out infinite}
.cur{animation:blink 1.1s steps(1) infinite}
@media (prefers-reduced-motion:reduce){.flow,.pulse,.cur,.spin{animation:none}}
</style>""")
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                f'{style}{"".join(self.parts)}</svg>')

def save(name, build):
    for theme in THEMES:
        d = Doc(theme); w, h = build(d)
        os.makedirs(f"assets/{theme}", exist_ok=True)
        open(f"assets/{theme}/{name}.svg", "w").write(d.svg(w, h))

# ---------------- shared components ----------------
def window(d, w, h, title):
    C = d.C
    d += f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{C["win"]}" stroke="{C["border"]}"/>'
    d += f'<path d="M1 40 V14 a13 13 0 0 1 13 -13 H{w-14} a13 13 0 0 1 13 13 V40Z" fill="{C["bar"]}"/>'
    d += f'<line x1="1" y1="40.5" x2="{w-1}" y2="40.5" stroke="{C["border"]}"/>'
    for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        d += f'<circle cx="{22+i*18}" cy="20.5" r="5.5" fill="{c}"/>'
    d += d.text(w/2, 25, title, 12, C["muted"], "mono", 400, "middle")

def prompt(d, x, y, cmd):
    C = d.C
    d += d.text(x, y, "~", 13, C["blue"], "mono", 500)
    d += d.text(x + width("~ ", "mono500", 13), y, "$", 13, C["faint"], "mono", 400)
    d += d.text(x + width("~ $ ", "mono400", 13), y, cmd, 13, C["text"], "mono", 400)

def pill(d, x, y, label, color, size=12, h=24, font="sans", weight=500, dot=True, anchor="start", fill_tint=True):
    C = d.C
    tw = width(label, f"{font}{weight}", size)
    w = tw + (30 if dot else 20)
    if anchor == "middle": x -= w/2
    d += (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" '
          f'fill="{color if fill_tint else C["node"]}" fill-opacity="{C["tint"] if fill_tint else 1}" stroke="{color}" stroke-opacity="0.45"/>')
    tx = x + 10
    if dot:
        d += f'<circle cx="{x+12:.1f}" cy="{y+h/2}" r="3.5" fill="{color}"/>'; tx = x + 21
    d += d.text(tx, y + h/2 + size*0.36, label, size, C["text"], font, weight)
    return w

def wrap(text, fk, size, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if width(t, fk, size) > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    return lines + [cur]

def node(d, x, y, w, h, title, sub, color):
    C = d.C
    d += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{C["node"]}"/>'
    d += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" fill-opacity="{C["tint"]}" stroke="{color}" stroke-opacity="0.55"/>'
    cy = y + h/2
    if sub:
        d += d.text(x + w/2, cy - 2, title, 13, C["text"], "sans", 600, "middle")
        d += d.text(x + w/2, cy + 14, sub, 11, C["muted"], "mono", 400, "middle")
    elif title:
        d += d.text(x + w/2, cy + 4.5, title, 13, C["text"], "sans", 600, "middle")

def group(d, x, y, w, h, label):
    C = d.C
    d += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="none" stroke="{C["faint"]}" stroke-opacity="0.6" stroke-dasharray="4 4"/>'
    lw = width(label, "mono400", 11) + 12
    d += f'<rect x="{x+14}" y="{y-8}" width="{lw:.1f}" height="16" fill="{C["win"]}"/>'
    d += d.text(x + 20, y + 4, label, 11, C["muted"], "mono", 400)

def edge(d, p1, p2, color, dur=2.2, delay=0.0, back=None):
    """Curved connector with flowing dashes and travelling packets (back = colour of return packet)."""
    C = d.C
    (x1, y1), (x2, y2) = p1, p2
    if abs(x2 - x1) >= abs(y2 - y1):
        mx = (x1 + x2) / 2; path = f"M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}"
        rpath = f"M{x2},{y2} C{mx},{y2} {mx},{y1} {x1},{y1}"
    else:
        my = (y1 + y2) / 2; path = f"M{x1},{y1} C{x1},{my} {x2},{my} {x2},{y2}"
        rpath = f"M{x2},{y2} C{x2},{my} {x1},{my} {x1},{y1}"
    d += f'<path d="{path}" fill="none" stroke="{C["edge"]}" stroke-width="1.5"/>'
    d += f'<path d="{path}" fill="none" stroke="{color}" stroke-opacity="0.55" stroke-width="1.5" class="flow"/>'
    for pth, col, dl in ((path, color, delay),) + (((rpath, back, delay + dur/2),) if back else ()):
        d += (f'<g><circle r="7" fill="{col}" opacity="0.18"/><circle r="3.4" fill="{col}"/>'
              f'<animateMotion path="{pth}" dur="{dur}s" begin="{dl:.2f}s" repeatCount="indefinite" '
              f'keyTimes="0;1" keySplines="0.45 0 0.55 1" calcMode="spline"/></g>')

# ---------------- HERO ----------------
def hero(d):
    C = d.C; W, H = 1000, 420
    window(d, W, H, "dimath@ucsc — ~ — zsh")
    x = 40
    prompt(d, x, 84, "whoami")
    d += d.text(x - 2, 142, "Dimath Jayasinghe", 46, C["text"], "sans", 600, extra='letter-spacing="-0.8"')
    gid = d.id()
    d += (f'<defs><linearGradient id="{gid}" x1="0" x2="1"><stop offset="0" stop-color="{C["blue"]}"/>'
          f'<stop offset="0.55" stop-color="{C["purple"]}"/><stop offset="1" stop-color="{C["pink"]}"/></linearGradient></defs>')
    d += d.text(x, 180, "Backend & Systems Engineer", 22, f"url(#{gid})", "sans", 600)
    for i, l in enumerate(["I build network servers, real-time systems and the",
                           "backends behind full-stack products."]):
        d += d.text(x, 218 + i*23, l, 15, C["muted"], "sans", 400)
    rows = [("focus", "networking · concurrency · system design"),
            ("stack", "C · C++ · Rust · TypeScript · PostgreSQL"),
            ("edu", "CS undergrad @ UCSC, University of Colombo"),
            ("based", "Sri Lanka · UTC+5:30")]
    for i, (k, v) in enumerate(rows):
        y = 284 + i*22
        d += d.text(x, y, k, 13, C["blue"], "mono", 500) + d.text(x + 64, y, v, 13, C["text"], "mono", 400)
    sy = 392
    label = "Looking for a software engineering internship"
    pw = width(label, "sans500", 13) + 36
    d += f'<rect x="{x}" y="{sy-18}" width="{pw:.1f}" height="28" rx="14" fill="{C["green"]}" fill-opacity="{C["tint"]}" stroke="{C["green"]}" stroke-opacity="0.45"/>'
    d += f'<circle class="pulse" cx="{x+15}" cy="{sy-4}" r="4" fill="{C["green"]}"/><circle cx="{x+15}" cy="{sy-4}" r="4" fill="{C["green"]}"/>'
    d += d.text(x + 27, sy + 0.5, label, 13, C["text"], "sans", 500)

    # topology graphic: core node, orbiting stack, packets both ways
    cx, cy = 790, 228
    d += f'<g class="spin" style="transform-origin:{cx}px {cy}px;transform-box:view-box;animation:spin 60s linear infinite">'
    d += f'<circle cx="{cx}" cy="{cy}" r="124" fill="none" stroke="{C["faint"]}" stroke-opacity="0.45" stroke-dasharray="2 7"/></g>'
    d += f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="{C["faint"]}" stroke-opacity="0.25"/>'
    sats = [("C++", C["blue"], -150), ("Rust", C["orange"], -90), ("TypeScript", C["cyan"], -30),
            ("PostgreSQL", C["purple"], 30), ("Linux", C["yellow"], 90), ("Docker", C["pink"], 150)]
    R = 124
    pos = [(round(cx + R*math.cos(math.radians(a))), round(cy + R*math.sin(math.radians(a)))) for _, _, a in sats]
    for i, ((lab, col, _), p) in enumerate(zip(sats, pos)):
        edge(d, (cx, cy), p, col, dur=2.6 + (i % 3)*0.4, delay=i*0.35, back=col)
    for (lab, col, _), (sx, sy2) in zip(sats, pos):
        pill(d, sx, sy2 - 13, lab, col, 12, 26, anchor="middle", fill_tint=False)
    g2 = d.id()
    d += (f'<defs><linearGradient id="{g2}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["blue"]}"/>'
          f'<stop offset="1" stop-color="{C["purple"]}"/></linearGradient></defs>')
    d += f'<rect x="{cx-38}" y="{cy-38}" width="76" height="76" rx="20" fill="url(#{g2})"/>'
    d += d.text(cx, cy + 10, "DJ", 28, "#FFFFFF", "sans", 600, "middle")
    return W, H

# ---------------- SECTION HEADERS ----------------
def section(num, title, note, colorkey):
    def b(d):
        C = d.C; W, H = 1000, 56
        d += d.text(0, 36, num, 13, C[colorkey], "mono", 500)
        tx = width(num, "mono500", 13) + 14
        d += d.text(tx, 37, title, 24, C["text"], "sans", 600)
        nx = tx + width(title, "sans600", 24) + 16
        d += d.text(nx, 36, note, 15, C["muted"], "sans", 400)
        lx = nx + width(note, "sans400", 15) + 20
        d += f'<line x1="{lx:.1f}" y1="31.5" x2="{W}" y2="31.5" stroke="{C["border"]}"/>'
        return W, H
    return b

# ---------------- PROJECT CARD ----------------
def project(slug, name, badge, badgekey, chips, desc, bullets, role, diagram):
    def b(d):
        C = d.C; W, H = 1000, 400
        window(d, W, H, f"~/systems/{slug} — zsh")
        x = 36
        prompt(d, x, 80, "cat README.md")
        d += d.text(x, 124, name, 30, C["text"], "sans", 600, extra='letter-spacing="-0.4"')
        pill(d, x + width(name, "sans600", 30) + 14, 103, badge, C[badgekey], 12, 24)
        cx_ = x
        for label, ck in chips:
            cx_ += pill(d, cx_, 142, label, C[ck], 12, 24, dot=False) + 8
        lines = wrap(desc, "sans400", 15, 380)
        assert len(lines) <= 2, f"{name}: description wraps to {len(lines)} lines"
        for i, l in enumerate(lines):
            d += d.text(x, 200 + i*23, l, 15, C["muted"], "sans", 400)
        by = 200 + len(lines)*23 + 18
        for i, bl in enumerate(bullets):
            yy = by + i*26
            d += f'<circle cx="{x+7}" cy="{yy-5}" r="7" fill="{C["green"]}" fill-opacity="{C["tint"]+0.06}"/>'
            d += f'<path d="M{x+3.5},{yy-5} l2.4,2.4 l4.6,-4.8" fill="none" stroke="{C["green"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            d += d.text(x + 22, yy, bl, 14, C["text"], "sans", 400)
        d += d.text(x, H - 26, role, 12, C["faint"], "mono", 400)
        d += f'<line x1="440.5" y1="64" x2="440.5" y2="{H-24}" stroke="{C["border"]}"/>'
        diagram(d)
        return W, H
    return b

def dg_wsrv(d):
    C = d.C
    for y in (82, 140, 198):
        node(d, 466, y, 84, 36, "client", "", C["blue"])
    node(d, 596, 128, 118, 60, "event loops", "epoll · TLS", C["cyan"])
    node(d, 760, 128, 128, 60, "sans-I/O core", "RFC 6455", C["purple"])
    node(d, 910, 128, 52, 60, "", "", C["pink"])
    d += d.text(936, 155, "pub", 11, C["muted"], "mono", 400, "middle") + d.text(936, 169, "sub", 11, C["muted"], "mono", 400, "middle")
    node(d, 774, 236, 100, 40, "C ABI", "", C["orange"])
    for i, (t, s) in enumerate((("wsrvd", "sidecar"), ("PHP FFI", "embedded"), ("Laravel", "rooms"))):
        node(d, 618 + i*118, 314, 104, 48, t, s, C["yellow"])
    for i, y in enumerate((100, 158, 216)):
        edge(d, (550, y), (596, 158), C["blue"], 1.8, i*0.4, back=C["cyan"])
    edge(d, (714, 158), (760, 158), C["cyan"], 1.4, 0.2)
    edge(d, (888, 158), (910, 158), C["purple"], 1.2, 0.5)
    edge(d, (824, 188), (824, 236), C["purple"], 1.4, 0.3)
    for i in range(3):
        edge(d, (824, 276), (670 + i*118, 314), C["orange"], 1.8, i*0.35)
    pill(d, 466, 256, "Autobahn 517/517", C["green"], 12, 26)
    d += d.text(466, 312, "fuzzed", 11, C["muted"], "mono", 400)
    d += d.text(466, 330, "ASan · UBSan", 11, C["muted"], "mono", 400)
    d += d.text(466, 348, "TSan clean", 11, C["muted"], "mono", 400)

def dg_serendeva(d):
    C = d.C
    group(d, 456, 72, 330, 172, "pnpm · turborepo monorepo")
    node(d, 472, 92, 116, 50, "mobile app", "Expo", C["pink"])
    node(d, 472, 172, 116, 50, "B2B portal", "Next.js", C["blue"])
    node(d, 646, 128, 124, 58, "API", "NestJS", C["purple"])
    node(d, 830, 76, 132, 50, "PostgreSQL", "Prisma", C["cyan"])
    node(d, 830, 150, 132, 50, "Redis", "Upstash", C["red"])
    group(d, 600, 278, 362, 92, "serendeva-ai")
    node(d, 618, 298, 150, 56, "AI worker", "Python", C["orange"])
    node(d, 790, 298, 156, 56, "recommender", "outfits · sizing", C["yellow"])
    edge(d, (588, 117), (646, 157), C["pink"], 2.0, 0, back=C["purple"])
    edge(d, (588, 197), (646, 157), C["blue"], 2.0, 0.6, back=C["purple"])
    edge(d, (770, 150), (830, 101), C["purple"], 1.8, 0.3, back=C["cyan"])
    edge(d, (770, 164), (830, 175), C["purple"], 1.8, 0.9, back=C["red"])
    edge(d, (708, 186), (693, 298), C["purple"], 2.2, 0.5, back=C["orange"])
    edge(d, (768, 326), (790, 326), C["orange"], 1.2, 0.2)
    d += d.text(466, 296, "3D avatars", 11, C["muted"], "mono", 400)
    d += d.text(466, 314, "size mapping", 11, C["muted"], "mono", 400)
    d += d.text(466, 332, "outfit recs", 11, C["muted"], "mono", 400)

def dg_poker(d):
    C = d.C
    for y in (88, 156, 224):
        node(d, 466, y, 92, 44, "phone", "player", C["blue"])
    group(d, 600, 72, 362, 250, "table device")
    node(d, 620, 92, 322, 44, "Flutter table UI", "", C["cyan"])
    node(d, 620, 164, 136, 58, "game server", "LAN", C["purple"])
    node(d, 800, 164, 142, 58, "Rust engine", "rules · side pots", C["orange"])
    node(d, 800, 250, 142, 52, "bots", "easy · normal · hard", C["yellow"])
    for i, y in enumerate((110, 178, 246)):
        edge(d, (558, y), (620, 193), C["blue"], 2.0, i*0.45, back=C["purple"])
    edge(d, (756, 193), (800, 193), C["purple"], 1.4, 0.2, back=C["orange"])
    edge(d, (688, 164), (688, 136), C["purple"], 1.2, 0.4)
    edge(d, (871, 222), (871, 250), C["orange"], 1.2, 0.6, back=C["yellow"])
    pill(d, 466, 340, "no internet needed", C["green"], 12, 26)
    d += d.text(620, 357, "join by room code or QR", 11, C["muted"], "mono", 400)

def dg_lms(d):
    C = d.C
    node(d, 462, 150, 112, 56, "web app", "Next.js · Vercel", C["blue"])
    group(d, 600, 72, 362, 226, "one VPS · docker compose")
    node(d, 614, 150, 78, 56, "nginx", "TLS", C["green"])
    node(d, 728, 94, 104, 54, "API", "Express", C["purple"])
    node(d, 728, 214, 104, 54, "worker", "BullMQ", C["pink"])
    node(d, 862, 94, 88, 54, "Postgres", "16", C["cyan"])
    node(d, 862, 214, 88, 54, "Redis", "queue", C["red"])
    edge(d, (574, 178), (614, 178), C["blue"], 1.4, 0, back=C["green"])
    edge(d, (692, 178), (728, 121), C["green"], 1.6, 0.3, back=C["purple"])
    edge(d, (832, 121), (862, 121), C["purple"], 1.2, 0.5, back=C["cyan"])
    edge(d, (780, 148), (780, 214), C["purple"], 1.6, 0.2)
    edge(d, (832, 241), (862, 241), C["pink"], 1.2, 0.7, back=C["red"])
    xx = 614
    for lab, col in (("Bunny.net", C["orange"]), ("R2", C["yellow"]), ("Zoom", C["blue"]), ("SMS", C["green"])):
        xx += pill(d, xx, 320, lab, col, 12, 26, fill_tint=False) + 10
    d += d.text(462, 337, "external", 11, C["muted"], "mono", 400)
    pill(d, 462, 236, "~1,200 students", C["purple"], 12, 26)

def dg_gradlink(d):
    C = d.C
    roles = (("student", C["blue"]), ("alumni", C["purple"]), ("admin", C["orange"]))
    for i, (r, col) in enumerate(roles):
        node(d, 466 + i*112, 80, 96, 44, r, "", col)
    node(d, 574, 170, 140, 54, "role-based auth", "", C["pink"])
    node(d, 574, 268, 140, 58, "PHP app", "no framework", C["cyan"])
    node(d, 762, 268, 110, 58, "MySQL", "", C["yellow"])
    group(d, 820, 72, 142, 164, "features")
    for i, f in enumerate(("groups", "mentoring", "messaging", "job posts")):
        pill(d, 836, 90 + i*34, f, C["green"], 12, 26, fill_tint=False)
    for i, (_, col) in enumerate(roles):
        edge(d, (514 + i*112, 124), (644, 170), col, 1.8, i*0.4)
    edge(d, (644, 224), (644, 268), C["pink"], 1.4, 0.3)
    edge(d, (714, 297), (762, 297), C["cyan"], 1.6, 0.5, back=C["yellow"])
    edge(d, (714, 282), (820, 200), C["cyan"], 2.2, 0.8)
    pill(d, 466, 346, "team of 4 · UCSC", C["blue"], 12, 26)

# ---------------- STACK ----------------
def stack(d):
    C = d.C; W = 1000
    rows = [("metal", "orange", ["C", "C++", "Rust"]),
            ("languages", "blue", ["TypeScript", "JavaScript", "Python", "Java", "C#", "PHP", "Dart"]),
            ("backend", "purple", ["Node.js", "NestJS", "Express", "Spring", "Flask"]),
            ("data", "cyan", ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Prisma", "BullMQ"]),
            ("infra", "green", ["Docker", "Nginx", "Linux", "Kubernetes", "Cloudflare", "GitHub Actions"]),
            ("frontend", "pink", ["Next.js", "React", "Flutter", "Expo", "Tailwind"])]
    H = 92 + len(rows)*48 + 20
    window(d, W, H, "~/stack — zsh")
    prompt(d, 36, 80, "ls ~/stack")
    for i, (lab, ck, items) in enumerate(rows):
        y = 104 + i*48
        if lab == "metal":
            d += f'<rect x="24" y="{y-8}" width="{W-48}" height="44" rx="10" fill="{C["orange"]}" fill-opacity="{C["tint"]}" stroke="{C["orange"]}" stroke-opacity="0.35"/>'
        d += d.text(40, y + 18, lab, 13, C[ck], "mono", 500)
        x = 170
        for it in items:
            x += pill(d, x, y + 1, it, C[ck], 13, 26, fill_tint=False) + 10
        if lab == "metal":
            d += d.text(W - 44, y + 18, "home", 12, C["orange"], "mono", 500, "end")
    return W, H

# ---------------- FOOTER ----------------
def footer(d):
    C = d.C; W, H = 1000, 96
    window(d, W, H, "~ — zsh")
    prompt(d, 36, 74, "exit")
    msg = "thanks for reading. connection closed, inbox open."
    mx = 36 + width("~ $ exit", "mono400", 13) + 28
    d += d.text(mx, 74, msg, 13, C["muted"], "mono", 400)
    d += f'<rect class="cur" x="{mx + width(msg, "mono400", 13) + 6:.1f}" y="62" width="8" height="16" rx="1" fill="{C["green"]}"/>'
    return W, H

if __name__ == "__main__":
    for f in glob.glob("assets/**/*.svg", recursive=True): os.remove(f)
    save("hero", hero)
    save("sec-systems", section("01", "Systems", "things I designed and built", "blue"))
    save("sec-stack", section("02", "Stack", "metal first", "purple"))
    save("sec-lab", section("03", "Lab", "earlier experiments", "orange"))
    save("sec-stats", section("04", "Stats", "updated by GitHub", "green"))
    save("sec-contact", section("05", "Contact", "say hello", "pink"))
    save("p-wsrv", project("wsrv", "wsrv", "open source", "green",
        [("C++23", "blue"), ("Linux", "yellow"), ("RFC 6455", "purple"), ("Apache-2.0", "green")],
        "WebSocket server written from scratch, no Boost or Asio. One audited core behind a stable C ABI.",
        ["sans-I/O protocol core, epoll event loops", "permessage-deflate, TLS, pub/sub", "PHP bindings via FFI and a sidecar daemon", "Prometheus metrics, fuzzing, sanitizers"],
        "role: author", dg_wsrv))
    save("p-serendeva", project("serendeva", "Serendeva", "private", "purple",
        [("TypeScript", "blue"), ("NestJS", "red"), ("Next.js", "text"), ("Expo", "purple"), ("Python", "yellow")],
        "AI-powered wardrobe and fashion intelligence platform, with a B2B layer for fashion brands.",
        ["NestJS API for the mobile app and B2B portal", "size-accurate 3D avatars", "context-aware outfit recommendations", "cross-vendor size mapping for brands"],
        "role: top contributor · org repo", dg_serendeva))
    save("p-poker", project("poker-credits", "poker-credits", "Microsoft Store", "blue",
        [("Dart", "cyan"), ("Flutter", "blue"), ("Rust", "orange"), ("LAN", "green")],
        "Digital chips, blinds and side pots for in-person Texas Hold'em. Players join from their own phones.",
        ["table device hosts the game server", "fully offline over local Wi-Fi", "Rust engine for rules, pots and bots", "solo mode against 1 to 9 bots"],
        "role: author", dg_poker))
    save("p-lms", project("LMS", "LMS", "deployed", "green",
        [("TypeScript", "blue"), ("Express", "text"), ("PostgreSQL", "cyan"), ("Redis", "red"), ("Docker", "blue")],
        "Learning management system for a tuition institute: five roles, exams, marking, payments and live classes.",
        ["runs on one small VPS, no Kubernetes", "results published live over SSE", "idempotent payment handling", "multi-tenant ready"],
        "role: author", dg_lms))
    save("p-gradlink", project("GRADLINK", "GRADLINK", "team project", "orange",
        [("PHP", "purple"), ("MySQL", "cyan"), ("JavaScript", "yellow")],
        "Alumni and student networking platform for UCSC, built from scratch without frameworks.",
        ["role-based access for 3 user types", "groups, mentoring and messaging", "job and project posts by alumni", "admin approvals and analytics"],
        "role: top contributor", dg_gradlink))
    save("stack", stack)
    save("footer", footer)
    print("built", len(glob.glob("assets/**/*.svg", recursive=True)), "files")
