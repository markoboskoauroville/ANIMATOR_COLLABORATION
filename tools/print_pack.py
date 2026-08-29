#!/usr/bin/env python3
"""Turn the whole animator site into one PDF laid out for paper.

NOT COMMITTED. `PRINT_PACK.pdf` is in .gitignore. It is generated from catalog.json,
so committing it stores tens of megabytes to reproduce something a single command
rebuilds. On 28.8.2026 it reached 147 MB and GitHub rejected the push outright at
its 100 MB hard limit, which blocked unrelated work until the commit was rewritten.
Build it when you want it, hand it over, do not check it in.

    python3 tools/print_pack.py

Reads catalog.json, the same single source the website is built from, so the paper
and the screen can never disagree. Nothing here is typed by hand.

A4 landscape, because every frame in this film is 16:9 and a portrait page wastes
half the sheet on a picture this shape.
"""
import hashlib, json, os, glob, tempfile, textwrap
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas as rlcanvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(ROOT, 'catalog.json')))
E = CAT['entries']
W, H = landscape(A4)
M = 34                                    # margin

PAPER = (0.976, 0.945, 0.878)             # the film's cream, measured off an approved frame
INK = (0.10, 0.09, 0.08)
DIM = (0.42, 0.40, 0.36)
BRASS = (0.62, 0.44, 0.16)

for name, path in [('B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
                   ('R', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                   ('M', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]:
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))

c = rlcanvas.Canvas(os.path.join(ROOT, 'PRINT_PACK.pdf'), pagesize=(W, H))
PAGE = [0]


def bg():
    c.setFillColorRGB(*PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def foot(label=''):
    PAGE[0] += 1
    c.setFont('M', 7)
    c.setFillColorRGB(*DIM)
    c.drawString(M, 17, label)
    c.drawRightString(W - M, 17, str(PAGE[0]))


def newpage(label=''):
    foot(label)
    c.showPage()
    bg()


def wrap(text, font, size, width):
    """Greedy wrap measured in real glyph widths, not character counts."""
    out = []
    for para in str(text).split('\n'):
        words, line = para.split(), ''
        for w in words:
            t = (line + ' ' + w).strip()
            if pdfmetrics.stringWidth(t, font, size) <= width:
                line = t
            else:
                if line:
                    out.append(line)
                line = w
        out.append(line)
    return out


def para(x, y, text, width, size=8.6, lead=11.4, font='R', colour=INK):
    c.setFont(font, size)
    c.setFillColorRGB(*colour)
    for ln in wrap(text, font, size, width):
        c.drawString(x, y, ln)
        y -= lead
    return y


def heading(y, text, sub=''):
    c.setFont('B', 15)
    c.setFillColorRGB(*INK)
    c.drawString(M, y, text)
    if sub:
        c.setFont('M', 7.5)
        c.setFillColorRGB(*DIM)
        c.drawString(M + pdfmetrics.stringWidth(text, 'B', 15) + 12, y + 1, sub)
    c.setStrokeColorRGB(*BRASS)
    c.setLineWidth(1.1)
    c.line(M, y - 7, W - M, y - 7)
    return y - 24


_SMALL = os.path.join(tempfile.gettempdir(), 'printpack_small')
os.makedirs(_SMALL, exist_ok=True)


def small(path, maxdim=1500, q=80):
    """Downscale before embedding, and cache it.

    A plate is printed about 250mm wide at most. Embedding a 2752px image there is
    roughly 280 dpi, which is fine, but forty of them at full weight took the pack
    to 147 MB and GitHub rejected the push outright at its 100 MB hard limit. The
    read-through hit the same wall on 28.8.2026 and was fixed the same way.
    """
    try:
        st = os.stat(path)
    except OSError:
        return path
    key = hashlib.md5(('%s|%d|%d|%d' % (path, st.st_size, int(st.st_mtime), maxdim)
                       ).encode()).hexdigest()[:16]
    out = os.path.join(_SMALL, key + '.jpg')
    if not os.path.exists(out):
        try:
            im = Image.open(path).convert('RGB')
            if max(im.size) > maxdim:
                im.thumbnail((maxdim, maxdim), Image.LANCZOS)
            im.save(out, quality=q, optimize=True)
        except Exception:
            return path
    return out


def place(path, x, y, boxw, boxh):
    """Fit an image inside a box, keeping its shape, and draw a hairline round it."""
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return 0, 0
    iw, ih = Image.open(p).size
    p = small(p)
    s = min(boxw / iw, boxh / ih)
    w, h = iw * s, ih * s
    c.drawImage(ImageReader(p), x, y - h, width=w, height=h,
                preserveAspectRatio=True, mask='auto')
    c.setStrokeColorRGB(0.74, 0.70, 0.62)
    c.setLineWidth(0.5)
    c.rect(x, y - h, w, h, fill=0, stroke=1)
    return w, h


def of(kind, **kw):
    out = [e for e in E if e.get('kind') == kind]
    for k, v in kw.items():
        out = [e for e in out if str(e.get(k, '')) == str(v)]
    return out


def resolve(e):
    for pat in e.get('prefer', []):
        hits = sorted(glob.glob(os.path.join(ROOT, pat)))
        if hits:
            return os.path.relpath(hits[-1], ROOT)
    return e['file']


# ----------------------------------------------------------------- cover
bg()
c.setFont('B', 40)
c.setFillColorRGB(*INK)
c.drawCentredString(W / 2, H - 150, CAT.get('film', 'THE BRAIN BRAKE').upper())
c.setFont('R', 12)
c.setFillColorRGB(*DIM)
c.drawCentredString(W / 2, H - 175, CAT.get('subtitle', ''))
c.setFont('M', 10)
c.setFillColorRGB(*BRASS)
c.drawCentredString(W / 2, H - 205, '%s  ·  PRINT PACK  ·  %s'
                    % (CAT.get('version', ''), CAT.get('updated', '')))
c.setFont('M', 7.5)
c.setFillColorRGB(*DIM)
c.drawCentredString(W / 2, 84, 'built from catalog.json, the same source the website is built from')
c.drawCentredString(W / 2, 70, 'markoboskoauroville.github.io/ANIMATOR_COLLABORATION')
newpage()

# ----------------------------------------------------------------- the rules
y = heading(H - M - 6, 'How the artwork ships')
rules = [
    ('Edge to edge, no panel border',
     'The frame is a separate layer so it can move, animate or come off. It is delivered as a matte: '
     'solid paper margin and drawn line, transparent window.'),
    ('2731 x 1536, true 16:9', 'The tool returns 2752 wide. Everything is cropped before it ships.'),
    ('Key light is camera right, always', 'The shadow sits on the left of every face.'),
    ('Anything that moves on its own is a layer',
     'Sweat, the border, anything that drips, blinks or travels. It arrives as three files: plate, '
     'layer, composite.'),
    ('Nothing is in the film until Marko says so', 'The status under each picture says where it stands.'),
]
for t, d in rules:
    c.setFont('B', 9.5)
    c.setFillColorRGB(*INK)
    c.drawString(M, y, t)
    y = para(M + 12, y - 13, d, W - 2 * M - 12) - 9

# frame rate
y = heading(y - 6, 'The frame rate is the second language')
for e in of('rate'):
    c.setFont('B', 17)
    c.setFillColorRGB(*BRASS)
    c.drawString(M, y - 3, str(e.get('fps', '')))
    c.setFont('M', 6.5)
    c.setFillColorRGB(*DIM)
    c.drawString(M, y - 13, 'FRAMES / SEC')
    c.setFont('B', 9)
    c.setFillColorRGB(*INK)
    c.drawString(M + 74, y, e.get('title', ''))
    y = para(M + 74, y - 12, e.get('note', ''), W - M - 74 - M) - 10
newpage('how the artwork ships')

# ----------------------------------------------------------------- sheets & frame
for e in of('sheet') + of('overlay'):
    if e.get('status') == 'superseded':
        continue
    y = heading(H - M - 6, e.get('title', 'Sheet'),
                os.path.basename(resolve(e)))
    iw, ih = place(resolve(e), M, y, W - 2 * M, H - 210)
    y2 = y - ih - 16
    para(M, y2, e.get('note', ''), W - 2 * M)
    newpage(e.get('title', ''))

# ----------------------------------------------------------------- shots
shots = []
for e in of('keyframe'):
    if e.get('shot') not in shots:
        shots.append(e.get('shot'))
for sh in shots:
    ks = [e for e in of('keyframe') if str(e.get('shot')) == str(sh)]
    y = heading(H - M - 6, 'Shot %s' % sh, '%d key frame%s' % (len(ks), '' if len(ks) == 1 else 's'))
    n = max(1, len(ks))
    colw = (W - 2 * M - 14 * (n - 1)) / n
    boxh = 250 if n > 1 else H - 200      # a lone key frame gets the whole sheet
    top = y
    for i, e in enumerate(ks):
        x = M + i * (colw + 14)
        iw, ih = place(e['file'], x, top, colw, boxh)
        yy = top - ih - 13
        c.setFont('M', 7.5)
        c.setFillColorRGB(*BRASS)
        c.drawString(x, yy, os.path.basename(e['file']))
        c.setFont('M', 6.5)
        c.setFillColorRGB(*DIM)
        c.drawString(x, yy - 10, (e.get('status', '') or '').upper())
        para(x, yy - 24, e.get('note', ''), colw, size=7.4, lead=9.4)
    newpage('shot %s' % sh)

# ----------------------------------------------------------------- glossary
sy = of('symbol')
per = 4
for p in range(0, len(sy), per):
    y = heading(H - M - 6, 'Glossary of symbols',
                'page %d of %d' % (p // per + 1, (len(sy) + per - 1) // per))
    chunk = sy[p:p + per]
    # constant column width, set by `per` and not by how many landed on this page,
    # or the last page stretches one plate across the whole sheet
    colw = (W - 2 * M - 16 * (per - 1)) / per
    if len(chunk) < per:                  # a short last page centres rather than hugging the left
        pass
    for i, e in enumerate(chunk):
        x = M + i * (colw + 16)
        iw, ih = place(resolve(e), x, y, colw, 190)
        yy = y - ih - 14
        c.setFont('B', 8.4)
        c.setFillColorRGB(*INK)
        for ln in wrap(e.get('title', ''), 'B', 8.4, colw):
            c.drawString(x, yy, ln)
            yy -= 10.5
        para(x, yy - 3, e.get('note', ''), colw, size=7.2, lead=9.2)
    newpage('glossary of symbols')

foot('end')
c.save()
print('written PRINT_PACK.pdf, %d pages' % PAGE[0])
