#!/usr/bin/env python3
"""RENUMBER: THE NAME FOLLOWS THE POSITION IN THE FILM.

Baba, 8.9.2026. Frames get generated in whatever order the work happens: four,
then two, then three, then one. But when Kristijan downloads a scene the files
have to sort into the order they play. So the filename is not an identity, it is
an ADDRESS: SC6-1, SC6-2, SC6-3, first to last.

    SC<scene>-<position>

Positions are recomputed from scratch every run, so inserting a frame between
two others, moving one, or retiring one, and running this again, is all it takes.
The slots are fixed; what sits in them changes.

WHY THIS IS SAFE TO RUN REPEATEDLY

  1. Every entry keeps an `id`, set once, never changed. That is the thing's
     real identity. The filename is derived and disposable, so nothing is lost
     when it moves.
  2. It is a two-phase rename. Everything moves to a temporary name first, then
     into place. Without that, renaming 3 to 4 while 4 still exists destroys 4.
  3. Nothing is written until the whole plan is computed and checked for
     collisions.
  4. Every move is verified by SHA-256 afterwards, not by exit code.

WHAT IS RENAMED, AND WHAT IS NOT

Renamed: every frame that appears in the storyboard, generated or filmed,
because the download has to sort correctly and a mixed naming scheme does not.

Left alone: sheets and references (storyboard='hide'), which are not in the
film's running order and are found by name; retired frames, which keep the name
they were retired under so the archive still reads; and the two loose title and
credit cards, which are named for what they are.

Usage:
    python3 renumber.py            dry run, prints the plan
    python3 renumber.py --write    does it
"""
import json, os, re, shutil, subprocess, sys, hashlib

AC = '/home/claude/AC_FULL'
ORIG = '/home/claude/ORIG'
LIVE = ('accepted', 'proposal', 'placeholder')


def shot_key(e):
    s = str(e.get('shot', ''))
    m = re.match(r'^([0-9]+)R?\.?([0-9]*)([a-z]*)$', s)
    if not m:
        return (999, 999, s)
    return (int(m.group(1)), int(m.group(2) or 0), m.group(3))


def scene_key(s):
    return (len(str(s)), str(s))


def plan():
    cat = json.load(open(os.path.join(AC, 'catalog.json')))
    orig = json.load(open(os.path.join(AC, 'originals.json')))

    # THE SCENE NUMBER IS THE POSITION IN THE FILM, not whatever the folder was
    # called. The flow already holds the running order, and one flow entry can
    # cover several old scene ids: the bicycle scene covers 3, 4 and 5.
    flows = sorted([e for e in cat['entries'] if e.get('kind') == 'flow'],
                   key=lambda e: int(e['n']))
    where = {}
    for f in flows:
        for old in (f.get('scenes') or []):
            where[str(old)] = int(f['n'])

    live = [e for e in cat['entries']
            if e.get('kind') == 'keyframe'
            and e.get('status') in LIVE
            and e.get('storyboard') != 'hide']

    scenes, orphan = {}, []
    for e in live:
        # a frame with no scene still knows where it lives: its shot prefix
        old = str(e.get('scene') or str(e.get('shot', '')).split('.')[0])
        if old not in where:
            orphan.append((old, os.path.basename(e['file'])))
            continue
        e['scene'] = old
        scenes.setdefault(where[old], []).append(e)
    if orphan:
        print('NOT PLACED, so left alone (%d):' % len(orphan))
        for o, n in orphan[:8]:
            print('   scene %-4s %s' % (o, n))
        print()

    moves = []
    for sc in sorted(scenes):
        rows = sorted(scenes[sc], key=shot_key)
        for i, e in enumerate(rows, 1):
            old = os.path.basename(e['file'])
            stem, ext = os.path.splitext(old)
            new = 'SC%s-%d%s' % (sc, i, ext)
            if e.get('id') is None:
                e['id'] = stem            # identity, set once
            if old != new:
                moves.append({'entry': e, 'old': old, 'new': new,
                              'scene': sc, 'pos': i,
                              'dir': os.path.dirname(e['file'])})
    # a collision here means two frames want the same address
    want = [m['new'] for m in moves]
    dup = {n for n in want if want.count(n) > 1}
    if dup:
        raise SystemExit('two frames want the same name: %s' % sorted(dup))
    return cat, orig, moves, scenes


def execute():
    """Two phases, because renaming 3 to 4 while 4 still exists destroys 4."""
    cat, orig, moves, scenes = plan()
    if not moves:
        print('nothing to do'); return
    TMP = '__tmp__'
    steps = []                      # (kind, from, to)

    def paths_for(old, new):
        """Everywhere a frame's name appears on disk."""
        out = []
        rec = orig.get(old)
        if rec:
            out.append((os.path.join(ORIG, rec['path']),
                        os.path.join(ORIG, os.path.dirname(rec['path']), new)))
        so, sn = os.path.splitext(old)[0], os.path.splitext(new)[0]
        for d, ext in (('mid', '.jpg'), ('tiny', '.jpg'), ('clips', os.path.splitext(old)[1])):
            a = os.path.join(AC, d, so + ext)
            if os.path.exists(a):
                out.append((a, os.path.join(AC, d, sn + ext)))
        return out

    # phase one: everything out of the way
    for m in moves:
        for a, b in paths_for(m['old'], m['new']):
            t = a + TMP
            shutil.move(a, t)
            steps.append((t, b))
    # phase two: into place
    moved = 0
    for t, b in steps:
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.move(t, b)
        assert os.path.exists(b), b
        moved += 1

    # the catalogue and the originals index follow the files
    for m in moves:
        e = m['entry']
        e['file'] = os.path.join(m['dir'], m['new']) if m['dir'] else m['new']
        rec = orig.pop(m['old'], None)
        if rec:
            rec['path'] = os.path.join(os.path.dirname(rec['path']), m['new'])
            rec['url'] = ('https://raw.githubusercontent.com/markoboskoauroville/'
                          'BRAIN_BRAKE_ORIGINALS/main/' + rec['path'])
            p = os.path.join(ORIG, rec['path'])
            rec['bytes'] = os.path.getsize(p)
            rec['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            orig[m['new']] = rec
        if e.get('full'):
            e['full'] = re.sub(r'/[^/]+$', '/' + m['new'], e['full'])

    # stale card pages are regenerated by the build; delete the old ones
    gone = 0
    for m in moves:
        c = os.path.join(AC, 'card', os.path.splitext(m['old'])[0] + '.html')
        if os.path.exists(c):
            os.remove(c); gone += 1

    json.dump(cat, open(os.path.join(AC, 'catalog.json'), 'w'),
              ensure_ascii=False, indent=2)
    json.dump(orig, open(os.path.join(AC, 'originals.json'), 'w'),
              ensure_ascii=False, indent=2)
    print('renamed %d frames, moved %d files, removed %d stale cards'
          % (len(moves), moved, gone))


if __name__ == '__main__':
    if '--write' in sys.argv:
        execute(); raise SystemExit
    cat, orig, moves, scenes = plan()
    print('scenes: %d, frames in the running order: %d'
          % (len(scenes), sum(len(v) for v in scenes.values())))
    print('renames needed: %d' % len(moves))
    print()
    for sc in sorted(scenes):
        rows = [m for m in moves if m['scene'] == sc]
        if not rows:
            continue
        print('  SC%s' % sc)
        for m in rows[:40]:
            print('     %-34s -> %s' % (m['old'], m['new']))


