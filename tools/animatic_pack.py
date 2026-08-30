#!/usr/bin/env python3
"""Lay every frame out in film order, numbered, ready to drop into Resolve.

    python3 tools/animatic_pack.py

Writes ANIMATIC/, which is NOT committed. The frames already live in this
repository once; copying them in would add nearly 200 MB to reproduce something
one command rebuilds. Same reason PRINT_PACK.pdf is ignored.

Resolve sorts an imported folder by filename, so the numbering is the edit order.
Drop the folder on a timeline, set each clip to the length of its beat, and the
animatic is built. Replace a frame later and rerun this; the numbering follows
the catalogue.
"""
import json, os, shutil, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(ROOT, 'catalog.json')))
OUT = os.path.join(ROOT, 'ANIMATIC')


def shot_key(s):
    return [(int(m.group(1) or 0), m.group(2)) for m in
            [re.match(r'(\d*)([a-z]*)', p) for p in str(s).split('.')]]


def sortkey(e):
    m = re.search(r'BUILD-(\d+)', e['file'])
    return (shot_key(e['shot']), 1 if m else 0, int(m.group(1)) if m else 0, e['file'])


kf = [e for e in CAT['entries']
      if e.get('kind') == 'keyframe' and e.get('status') != 'superseded']
kf.sort(key=sortkey)

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
rows = []
for i, e in enumerate(kf, 1):
    src = os.path.join(ROOT, e['file'])
    ext = os.path.splitext(src)[1]
    name = '%03d_%s%s' % (i, os.path.basename(src).rsplit('.', 1)[0].replace(' ', '_'), ext)
    shutil.copy2(src, os.path.join(OUT, name))
    note = (e.get('note', '') or '').split('.')[0]
    rows.append('%-42s shot %-6s %s' % (name, e['shot'], note[:70]))

open(os.path.join(OUT, 'ORDER.txt'), 'w').write(
    'THE BRAIN BRAKE, animatic frames in film order\n'
    'Rebuilt by tools/animatic_pack.py from catalog.json. Do not edit by hand.\n\n'
    'Import this folder into Resolve. It sorts by filename, so the numbering is the\n'
    'edit order. Frames are 16:9 at 2731 or 2752 wide. The panel border is a separate\n'
    'layer and is not baked into these.\n\n' + '\n'.join(rows) + '\n')
print('%d frames in ANIMATIC/' % len(kf))
