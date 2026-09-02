#!/usr/bin/env python3
"""THE BRAIN BRAKE, the animator read through. Build the PDF.

    python3 tools/print_readthrough.py

Writes DOCS/BRAIN_BRAKE_READTHROUGH.pdf, one spread per frame: the picture, what
it is, what it means, and HOW IT MOVES.

WHO IT IS FOR

Kristijan, at his desk, away from the site. The web page is the live thing and
always will be. This is what you print, mark up, and put beside a monitor.

WHY IT SAYS WHAT IT MEANS AND NOT ONLY WHAT TO DO

An animator given only instructions will follow them and stop there. An animator
who knows WHY a shot exists will fix things nobody thought to specify. So each
frame carries the reason as well as the move, and the two grammars are stated at
the front, once, because almost every per frame note is an application of them.

Built from catalog.json, so it cannot drift from the site. If a note changes
there, it changes here on the next build.
"""
import json, os, textwrap
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'DOCS', 'BRAIN_BRAKE_READTHROUGH.pdf')
PAGE = landscape(A4)
W, H = PAGE

PAPER = colors.HexColor('#FBF7EF')
INK = colors.HexColor('#26211B')
DIM = colors.HexColor('#7A7267')
GOLD = colors.HexColor('#B07B23')
RULE = colors.HexColor('#D8D0C2')

# HOW EACH SHOT MOVES. Keyed by the frame's file name. Where a frame has no
# entry here it gets the grammar rule for its half of the film, which is not a
# gap: the rule IS the instruction, and saying it again per frame would invite
# somebody to treat the exceptions as normal.
CUES = {
 '0-0-TITLE-v1.png': 'Hold. The title rubs itself onto the paper by frottage, edge first, and is '
    'never typed on. Nothing else moves.',
 '8-0-A-v5.png': 'Slow push straight down the corridor, constant speed, no easing at either end. '
    'The doors pass. DO NOT linger on any one of them: the audience must learn that the bumps mean '
    'something without being told to look. The far door at the vanishing point stays centred.',
 '8-3-MUSCLE-v1.png': 'Push in on the gap. The door is already open a hand\u2019s width, so nothing '
    'opens on camera. We are looking at a decision somebody already made.',
 '8-4-MUSCLE-v1.png': 'Track forward down the hall at walking pace. The next door grows from a mark '
    'to a shape. Cross THROUGH it: the frame darkens as the door fills the lens and the next hall '
    'is already there. No cut.',
 '8-1-A-v3.png': 'Same move, same speed as the muscle hall. Sameness is the point: three rooms that '
    'feel identical make the fourth door land. The bulbs breathe once, slowly, out of sync with each '
    'other.',
 '8-6-HEART-v1.png': 'Same move again, then SLOW as the key door resolves. This is the only place in '
    'the sequence the camera changes its mind, and it is the moment he realises.',
 '18-0-A-v6.png': 'Hold, longer than is comfortable. Then in through the door, not around it. The '
    'key in the clay is the last thing on screen before the room.',
 '19-0-A-v2.png': 'Slow drift in on Coach Brain. He turns to us on his own time. The gold at his '
    'neck is the ONLY colour that has appeared in the film so far, so give it a beat with no other '
    'movement competing.',
 '9-1-VORTEX-v2.png': 'The camera does not move. THE WATER DOES. The strands turn and climb and the '
    'throat holds its position, so the shot rotates without the frame rotating. Keys drift at their '
    'own speeds, never in step.',
 '9-0-VORTEX-v2.png': 'The faint version scales into the full one. Same spiral, same place, same '
    'angle. Grow it, do not redraw it.',
 '9-2-MANAN-1-v2.png': 'He lifts out of the bottom of frame. Clothes and hair trail DOWNWARD, which '
    'is the only thing that tells the audience he is rising and not falling. Get that wrong and the '
    'whole passage reads backwards.',
 '9-2-MANAN-2-v2.png': 'He rotates as he rises, carried rather than swimming. He never once looks at '
    'the keys. That is the shot: he is inside the answer and cannot see it.',
 '9-2-MANAN-3-v1.png': 'He passes the lens and leaves the top of frame. Do not cut. The paper he '
    'leaves behind becomes the white of the house, so the next shot is already underway before this '
    'one ends.',
 '14-8-DEDICATION-v2.png': 'The last card. Ganesha rubs on by frottage, the lettering after him, '
    'then hold in silence with the music. Nothing moves out. The film simply stops.',
}

GRAMMAR = [
 ('BEFORE HE CLOSES HIS EYES, THINGS ARRIVE.',
  'The world manifests out of the paper, part by part, by frottage: a shape rubs through as though '
  'something under the sheet is being taken. Nothing slides in from the side, nothing fades up. If '
  'a thing needs to appear, it is rubbed on. This is the whole grammar of the first half and it '
  'never varies.'),
 ('AFTER HE CLOSES HIS EYES, NOTHING ARRIVES. WE MOVE.',
  'Every transition is a passage through a surface. Through a door, into a throat, past a lens, into '
  'the paper itself. THERE IS NO CUT ANYWHERE AFTER PHASE 5. If a shot seems to need one, the '
  'answer is a surface, not a cut.'),
 ('GOLD MEANS FOUND.',
  'Gold is not the key\u2019s colour, it is what the key means once he has it. So the whole passage '
  'is graphite even though it is made of keys, because he has not found it yet. The first gold is at '
  'Coach Brain\u2019s neck. The last is the key falling out of the sky. There is no third.'),
 ('THE SIGNS ARE NEVER EXPLAINED.',
  'A shape raised in clay tells you what is behind a door. Nobody says so, no camera move points at '
  'it, no music underlines it. By the fourth door the audience is reading them without having been '
  'taught, and that is why the key door works.'),
 ('HE IS REAL. THE INSIDE OF HIM IS DRAWN.',
  'Manan is photographic, in monochrome, everywhere he appears. The house of the body, the vortex '
  'and Coach Brain are pencil. Do not draw him and do not colour him.'),
]


def wrap(c, text, x, y, width, leading=11.5, size=9, colour=INK, font='Helvetica'):
    c.setFont(font, size)
    c.setFillColor(colour)
    chars = int(width / (size * 0.50))
    for line in textwrap.wrap(text, chars):
        c.drawString(x, y, line)
        y -= leading
    return y


def page_frame(c, e, n, total):
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    b = os.path.basename(e['file']).rsplit('.', 1)[0].replace(' ', '_')
    img = os.path.join(ROOT, 'mid', b + '.jpg')
    iw = W * 0.52
    if os.path.exists(img):
        ih = iw * 558 / 1000.0
        c.drawImage(img, 18 * mm, H - 26 * mm - ih, width=iw, height=ih,
                    preserveAspectRatio=True, mask='auto')
        c.setStrokeColor(RULE); c.setLineWidth(0.6)
        c.rect(18 * mm, H - 26 * mm - ih, iw, ih, fill=0, stroke=1)
    x = 18 * mm + iw + 12 * mm
    right = W - 18 * mm - x
    y = H - 28 * mm
    c.setFont('Helvetica-Bold', 7.5); c.setFillColor(GOLD)
    c.drawString(x, y, ('PHASE %s' % e.get('shot', '')).upper())
    y -= 14
    c.setFont('Helvetica-Bold', 15); c.setFillColor(INK)
    c.drawString(x, y, (e.get('title') or b)[:46])
    y -= 10
    c.setFont('Courier', 7.5); c.setFillColor(DIM)
    c.drawString(x, y, os.path.basename(e['file']))
    y -= 18
    c.setStrokeColor(RULE); c.line(x, y, x + right, y); y -= 16
    c.setFont('Helvetica-Bold', 7.5); c.setFillColor(GOLD)
    c.drawString(x, y, 'WHAT IT IS'); y -= 13
    y = wrap(c, (e.get('note') or '').replace('\n', ' '), x, y, right)
    y -= 12
    c.setFont('Helvetica-Bold', 7.5); c.setFillColor(GOLD)
    c.drawString(x, y, 'HOW IT MOVES'); y -= 13
    cue = CUES.get(os.path.basename(e['file']))
    if not cue:
        sc = e.get('scene', 0)
        cue = ('First half grammar: it arrives by frottage, rubbed through the paper, never slid in '
               'and never faded up.' if isinstance(sc, int) and sc <= 5 else
               'Second half grammar: we move, it does not arrive. Enter and leave through a surface. '
               'There is no cut.')
    wrap(c, cue, x, y, right, colour=INK)
    c.setFont('Courier', 7); c.setFillColor(DIM)
    c.drawString(18 * mm, 12 * mm, 'THE BRAIN BRAKE  \u00b7  animator read through')
    c.drawRightString(W - 18 * mm, 12 * mm, '%d / %d' % (n, total))
    c.showPage()


def main():
    cat = json.load(open(os.path.join(ROOT, 'catalog.json')))
    live = [e for e in cat['entries']
            if e.get('kind') == 'keyframe' and e.get('status') not in ('superseded',)
            and e.get('file')]
    def order(e):
        try:
            return [float(p) for p in str(e.get('shot', '0')).split('.')]
        except ValueError:
            return [999.0]
    live.sort(key=order)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    c = canvas.Canvas(OUT, pagesize=PAGE)
    c.setTitle('THE BRAIN BRAKE, the animator read through')

    # cover
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 34); c.setFillColor(INK)
    c.drawString(24 * mm, H - 48 * mm, 'THE BRAIN BRAKE')
    c.setFont('Helvetica', 13); c.setFillColor(DIM)
    c.drawString(24 * mm, H - 58 * mm, 'the animator read through')
    c.setFont('Helvetica', 9)
    c.drawString(24 * mm, H - 72 * mm,
                 'Presented by Manan Periwal  \u00b7  animated by Kristijan Kauri\u0107  '
                 '\u00b7  Breakthrough Junior Challenge 2026')
    y = H - 92 * mm
    y = wrap(c, 'Every frame in the film, in order, with what it is, what it means and how it moves. '
                'Built from the catalogue, so it cannot drift from the live page. The site is always '
                'current; this is the copy you print and mark up.', 24 * mm, y, W - 48 * mm,
             size=10, leading=13)
    y -= 8
    wrap(c, 'markoboskoauroville.github.io/ANIMATOR_COLLABORATION', 24 * mm, y, W - 48 * mm,
         size=9, colour=GOLD, font='Courier-Bold')
    c.showPage()

    # the grammar
    c.setFillColor(PAPER); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 20); c.setFillColor(INK)
    c.drawString(24 * mm, H - 30 * mm, 'FIVE THINGS THAT DECIDE EVERY SHOT')
    y = H - 44 * mm
    for head, body in GRAMMAR:
        c.setFont('Helvetica-Bold', 9.5); c.setFillColor(GOLD)
        c.drawString(24 * mm, y, head); y -= 13
        y = wrap(c, body, 24 * mm, y, W - 48 * mm, size=9, leading=11.5)
        y -= 10
    c.showPage()

    for i, e in enumerate(live, 1):
        page_frame(c, e, i, len(live))
    c.save()
    print('%s' % os.path.relpath(OUT, ROOT))
    print('  %d frames, %d pages, %.1f MB'
          % (len(live), len(live) + 2, os.path.getsize(OUT) / 1048576.0))


if __name__ == '__main__':
    main()
