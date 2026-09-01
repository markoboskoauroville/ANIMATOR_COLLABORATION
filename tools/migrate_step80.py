#!/usr/bin/env python3
"""STEP 80, the one time move: every committed full resolution PNG goes to
Drive, verified byte for byte, and only then leaves the repository.

    python3 tools/migrate_step80.py --plan      say what would move, move nothing
    python3 tools/migrate_step80.py --upload    upload and verify, remove nothing
    python3 tools/migrate_step80.py --cut       git rm what --upload verified

Three phases on purpose. Upload and verify EVERYTHING first, look at the
result, and only then delete, in one commit, exactly the files whose byte
count came back from Drive equal. A file that failed to verify is left
tracked and said out loud. Twenty graded stills were destroyed on 31.8.2026
by an operation that looked like it worked; nothing here is allowed to look
like it worked.

WHAT DOES NOT MOVE, and why:

  mid/ and tiny/          generated small versions, they ARE the site
  *_bg *_fg *_comp etc    layer files: the breakdown pages link them directly
                          and read their sizes off the disk at build time
  prefer glob winners     an entry's `prefer` resolves to the newest matching
                          file on disk; taking the winner away silently swaps
                          the picture for a placeholder

The upload runs as Baba through the `gdrive` rclone remote, same as the v7
daemon and for the same reason: the STEP 78 service account has no storage
quota. Results land in tools/_step80_results.json so --cut never trusts
memory, only what was written down at verify time.
"""
import glob as globmod
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, 'tools', '_step80_results.json')
REMOTE, DROOT = 'gdrive', 'BRAIN_BRAKE_FULL_RES'
LAYER = re.compile(r'_(bg|background|fg|foreground|comp)\b', re.I)
SIPS = '/usr/bin/sips'


def run(*a, timeout=1800):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)


def tracked_pngs():
    out = run('git', '-C', ROOT, 'ls-files', '*.png').stdout.split()
    return [f for f in out if not f.startswith(('mid/', 'tiny/'))]


def prefer_winners(cat):
    keep = set()
    for e in cat['entries']:
        for pat in e.get('prefer', []) or []:
            hits = sorted(globmod.glob(os.path.join(ROOT, pat)))
            if hits:
                keep.add(os.path.relpath(hits[-1], ROOT))
    return keep


def classify():
    cat = json.load(open(os.path.join(ROOT, 'catalog.json')))
    byfile = {e.get('file'): e for e in cat['entries']}
    winners = prefer_winners(cat)
    move, layers, kept = [], [], []
    for f in tracked_pngs():
        if LAYER.search(os.path.basename(f)):
            layers.append(f)
        elif f in winners:
            kept.append(f)
        else:
            move.append(f)
    return cat, byfile, move, layers, kept


def drive_ls(folder):
    r = run('rclone', 'lsjson', '%s:%s' % (REMOTE, folder), '--timeout', '60s')
    if r.returncode != 0:
        if 'directory not found' in (r.stderr or '').lower():
            return []
        return None
    try:
        return json.loads(r.stdout or '[]')
    except ValueError:
        return None


def sips_get(path, key):
    r = run(SIPS, '-g', key, path, timeout=120)
    m = re.search(r'%s:\s*(\S+)' % re.escape(key), r.stdout or '')
    return m.group(1) if m else ''


def make_small(src, stem):
    alpha = sips_get(src, 'hasAlpha') == 'yes'
    try:
        width = int(sips_get(src, 'pixelWidth') or 0)
    except ValueError:
        width = 0
    ext = '.png' if alpha else '.jpg'
    for folder, target in (('mid', 1000), ('tiny', 300)):
        out = os.path.join(ROOT, folder, stem + ext)
        if os.path.exists(out):
            continue                       # never regrade what exists
        a = [SIPS] + (['-s', 'format', 'png'] if alpha else
                      ['-s', 'format', 'jpeg', '-s', 'formatOptions', '85'])
        if width > target:
            a += ['--resampleWidth', str(target)]
        a += [src, '--out', out]
        r = run(*a, timeout=300)
        if r.returncode != 0 or not os.path.exists(out):
            return False
    return True


def upload():
    cat, byfile, move, layers, kept = classify()
    done = {}
    if os.path.exists(RESULTS):
        done = json.load(open(RESULTS))
    listing_cache = {}
    ok = fail = 0
    for i, f in enumerate(move, 1):
        if f in done and done[f].get('verified'):
            ok += 1
            continue
        local = os.path.getsize(os.path.join(ROOT, f))
        sub = f.split('/')[0]
        folder = '%s/%s' % (DROOT, sub)
        name = os.path.basename(f)
        r = run('rclone', 'copyto', os.path.join(ROOT, f),
                '%s:%s/%s' % (REMOTE, folder, name), '--timeout', '300s')
        if r.returncode != 0:
            print('  UPLOAD FAILED %s: %s' % (f, (r.stderr or '').strip()[-120:]))
            fail += 1
            continue
        listing_cache.pop(folder, None)
        lst = drive_ls(folder)
        if lst is None:
            print('  CANNOT READ BACK %s, not verified' % f)
            fail += 1
            continue
        hit = next((e for e in lst if e.get('Name') == name), None)
        if not hit or int(hit.get('Size', -1)) != local:
            print('  BYTE MISMATCH %s: local %d, Drive %s'
                  % (f, local, hit and hit.get('Size')))
            fail += 1
            continue
        link = 'https://drive.google.com/file/d/%s/view' % hit.get('ID', '')
        stem = os.path.splitext(name)[0].replace(' ', '_')
        if not make_small(os.path.join(ROOT, f), stem):
            print('  SMALL VERSIONS FAILED %s, keeping it' % f)
            fail += 1
            continue
        done[f] = {'verified': True, 'bytes': local, 'link': link}
        json.dump(done, open(RESULTS, 'w'), indent=1)
        ok += 1
        print('  %3d/%d  %s  %d bytes verified' % (i, len(move), f, local))
    # the catalogue, once, at the end
    changed = 0
    for f, r in done.items():
        e = byfile.get(f)
        if e is not None and r.get('verified'):
            e['full'], e['full_bytes'] = r['link'], r['bytes']
            changed += 1
    with open(os.path.join(ROOT, 'catalog.json'), 'w') as fh:
        json.dump(cat, fh, indent=1)
        fh.write('\n')
    # and drive_links.json for EVERY verified file, entry or no entry, the
    # same contract the daemon honours: the link must be in the repository
    # before any --cut may remove the file it points at
    dlp = os.path.join(ROOT, 'drive_links.json')
    dl = {}
    if os.path.exists(dlp):
        try:
            dl = json.load(open(dlp))
        except ValueError:
            dl = {}
    linked = 0
    for f, r in done.items():
        if r.get('verified'):
            dl[os.path.basename(f)] = {'url': r['link'], 'bytes': r['bytes']}
            linked += 1
    with open(dlp, 'w') as fh:
        json.dump(dl, fh, indent=1, sort_keys=True)
        fh.write('\n')
    print('verified %d, failed %d, catalogue entries linked %d, drive_links entries %d'
          % (ok, fail, changed, linked))
    print('kept local: %d layer files, %d prefer winners' % (len(layers), len(kept)))


def cut():
    done = json.load(open(RESULTS))
    victims = [f for f, r in done.items()
               if r.get('verified') and os.path.exists(os.path.join(ROOT, f))]
    if not victims:
        print('nothing verified to remove')
        return
    total = sum(done[f]['bytes'] for f in victims)
    r = run('git', '-C', ROOT, 'rm', '-q', '--', *victims)
    if r.returncode != 0:
        print('git rm refused: %s' % r.stderr.strip()[:200])
        return
    print('removed %d PNGs, %.1f MB, in the index. Commit them yourself,' % (
        len(victims), total / 1048576.0))
    print('with the build run in between, so the removal and the rebuilt site')
    print('land together and the tree is never pushed half done.')


if __name__ == '__main__':
    if '--plan' in sys.argv:
        cat, byfile, move, layers, kept = classify()
        tot = sum(os.path.getsize(os.path.join(ROOT, f)) for f in move)
        print('would move %d PNGs, %.1f MB' % (len(move), tot / 1048576.0))
        print('%d have catalogue entries and will get full links'
              % sum(1 for f in move if f in byfile))
        print('kept local: %d layer files, %d prefer winners' % (len(layers), len(kept)))
        for f in layers[:10]:
            print('  layer, stays: %s' % f)
        for f in kept[:10]:
            print('  prefer winner, stays: %s' % f)
    elif '--upload' in sys.argv:
        upload()
    elif '--cut' in sys.argv:
        cut()
    else:
        print(__doc__)
