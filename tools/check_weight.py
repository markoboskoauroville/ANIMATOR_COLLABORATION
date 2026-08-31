#!/usr/bin/env python3
"""Refuse to be satisfied by a page that pulls a heavy image.

    python3 tools/check_weight.py

Measures what a browser would actually download per page. Folder names prove
nothing: flow/ and examples/ hold pre-shrunk copies and are fine, while a stray
original anywhere is not. So this counts bytes.
"""
import re, os, glob, sys

LIMIT_IMAGE = 400 * 1024      # any single image over this is a mistake
LIMIT_PAGE = 3 * 1024 * 1024  # any page over this is too heavy for a phone

rows, bad = [], []
for f in sorted(glob.glob('*.html') + glob.glob('BB_C_*/*.html') + glob.glob('card/*.html')):
    d = os.path.dirname(f)
    total = 0
    for s in re.findall(r'<img[^>]+src="([^"]+)"', open(f).read()):
        p = os.path.normpath(os.path.join(d, s))
        if not os.path.exists(p):
            continue
        n = os.path.getsize(p)
        total += n
        if n > LIMIT_IMAGE:
            bad.append((f, s, n))
    rows.append((f, total))

heavy = [(f, t) for f, t in rows if t > LIMIT_PAGE]
for f, s, n in bad:
    print('  OVERSIZED  %-34s %-40s %.2f MB' % (f, s[:40], n / 1048576))
for f, t in heavy:
    print('  HEAVY PAGE %-34s %.2f MB' % (f, t / 1048576))

tot = sum(t for _, t in rows)
print('%d pages, %.1f MB of images in total, heaviest %.2f MB'
      % (len(rows), tot / 1048576, max(t for _, t in rows) / 1048576))
if bad or heavy:
    sys.exit('WEIGHT CHECK FAILED')
print('weight check passed')
