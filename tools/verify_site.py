#!/usr/bin/env python3
"""Check that the site is not quietly broken, and write down what was checked.

    python3 tools/verify_site.py              # cached, seconds
    python3 tools/verify_site.py --full       # ignore the cache, re-test everything
    python3 tools/verify_site.py --no-log     # check without appending to the log

WHY THIS EXISTS

Baba, 2.9.2026: clean the house, order the house, keep the house in good shape,
bug free, bulletproof. This project should never fall apart with errors.

Every failure this catches has actually happened here, and every one of them was
invisible on the page:

    fourteen hrefs pointing at originals the daemon had already deleted, while
    the thumbnails beside them rendered perfectly
    the whole drive_links dictionary written into an href as a Python repr
    a tray portrait whose ../ climbed out of the repository entirely
    a card page frozen at a build from before a fix, still being served
    a page cached on a phone five versions behind, which looks broken rather
    than stale

None of those produce an error anywhere. That is the point: a site fails silently
and only a check that runs every time will find it.

THE CACHE, WHICH IS NOT AN OPTIMISATION

A check that takes ten minutes stops being run, and a check that is not run is
worth nothing. So remote links are cached by url and expected size, and a run
after a small change tests what changed and confirms the rest from last time.
Use --full before anything that matters, and the log records which kind it was.
"""
import os, sys, json, re, subprocess, hashlib, time, datetime
import concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'tools', '.verify_cache.json')
LOG = os.path.join(ROOT, 'tools', 'verify_log.md')
LIVE = 'https://markoboskoauroville.github.io/ANIMATOR_COLLABORATION/'
PAGES_CEILING = 1024.0                      # MB. Pages fails SILENTLY above this
CACHE_DAYS = 7
FULL = '--full' in sys.argv
NOLOG = '--no-log' in sys.argv

fails, notes = [], []


def fail(check, detail):
    fails.append((check, detail))


def note(s):
    notes.append(s)


def load(p, default):
    try:
        return json.load(open(os.path.join(ROOT, p)))
    except Exception:
        return default


cache = {} if FULL else load('tools/.verify_cache.json', {})
now = time.time()


def head(url, expect_bytes=None):
    """Fetch with NO credential, which is what Kristijan has. Cached."""
    key = '%s|%s' % (url, expect_bytes)
    hit = cache.get(key)
    if hit and (now - hit.get('at', 0)) < CACHE_DAYS * 86400 and hit.get('ok'):
        return True, 'cached'
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-L', '--max-time', '60',
                        '-w', '%{http_code} %{size_download}', url],
                       capture_output=True, text=True).stdout.split()
    code = r[0] if r else '000'
    size = int(r[1]) if len(r) > 1 else 0
    ok = code == '200' and (expect_bytes is None or size == expect_bytes)
    cache[key] = {'at': now, 'ok': ok, 'code': code, 'size': size}
    return ok, '%s %d' % (code, size)


# --------------------------------------------------------------- the checks
cat = load('catalog.json', {})
entries = cat.get('entries', [])
originals = load('originals.json', {})
drive = load('drive_links.json', {})

pages = []
for r, _, fs in os.walk(ROOT):
    if '.git' in r:
        continue
    for fn in fs:
        if fn.endswith('.html'):
            pages.append(os.path.join(r, fn))

# 1  every href and src resolves
targets = {}
for p in pages:
    txt = open(p, encoding='utf-8', errors='ignore').read()
    rel = os.path.relpath(p, ROOT)
    for m in re.finditer(r'(?:href|src)="([^"]*)"', txt):
        u = m.group(1)
        if u == '':
            fail('empty href', rel)
            continue
        if u.startswith('{') or "': {" in u or 'bytes\':' in u:
            fail('a dict where a url belongs', '%s -> %s' % (rel, u[:60]))
            continue
        if u.startswith(('#', 'mailto:', 'data:', 'javascript:')):
            continue
        if u.startswith('http'):
            targets.setdefault(u, set()).add(rel)
        else:
            local = os.path.normpath(os.path.join(os.path.dirname(p), u.split('#')[0]))
            if not os.path.exists(local):
                fail('local path missing', '%s -> %s' % (rel, u))
            elif not local.startswith(ROOT):
                fail('path climbs out of the repository', '%s -> %s' % (rel, u))

with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for (u, pgs), (ok, why) in zip(targets.items(), ex.map(lambda u: head(u), targets)):
        if not ok and not why.startswith('429'):
            fail('remote link', '%s  %s  from %s' % (u[:70], why, sorted(pgs)[0]))

# 2  every catalogue entry has its tiny and its mid
for e in entries:
    f = e.get('file')
    if not f or e.get('kind') != 'keyframe':
        continue
    b = os.path.basename(f).rsplit('.', 1)[0].replace(' ', '_')
    for size in ('tiny', 'mid'):
        if not os.path.exists(os.path.join(ROOT, size, b + '.jpg')):
            fail('missing %s' % size, b)

# 3  nothing superseded is on the front page
front = os.path.join(ROOT, 'index.html')
if os.path.exists(front):
    txt = open(front, encoding='utf-8', errors='ignore').read()
    sup = {os.path.basename(e['file']).rsplit('.', 1)[0].replace(' ', '_')
           for e in entries if e.get('status') == 'superseded' and e.get('file')}
    for b in sup:
        if 'tiny/%s.jpg' % b in txt:
            fail('superseded frame on the front page', b)

# 4  the live version matches the catalogue
want = cat.get('site_version')
r = subprocess.run(['curl', '-s', '--max-time', '30', LIVE + '?cb=%d' % now],
                   capture_output=True, text=True).stdout
m = re.search(r'class=sitev[^>]*>v(\d+)', r)
if not m:
    fail('live version', 'could not read a version from the live page')
elif int(m.group(1)) != want:
    fail('live version', 'catalog says v%s, live serves v%s. The push has not '
                         'published yet, or it failed.' % (want, m.group(1)))
else:
    note('live version v%s matches catalog.json' % want)

# 5  published weight against the ceiling Pages fails silently above
total = 0
for r_, _, fs in os.walk(ROOT):
    if '.git' in r_:
        continue
    for fn in fs:
        try:
            total += os.path.getsize(os.path.join(r_, fn))
        except OSError:
            pass
mb = total / 1048576.0
note('published weight %.1f MB of the %.0f MB Pages ceiling, %.0f%%'
     % (mb, PAGES_CEILING, 100 * mb / PAGES_CEILING))
if mb > PAGES_CEILING * 0.8:
    fail('published weight', '%.1f MB is over 80%% of the ceiling' % mb)

# 6  every original fetches and is byte exact
def one_original(item):
    n, v = item
    ok, why = head(v['url'], v.get('bytes'))
    return n, ok, why


with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for n, ok, why in ex.map(one_original, sorted(originals.items())):
        if not ok:
            fail('original', '%s  %s' % (n, why))
note('%d originals in originals.json, %.1f MB'
     % (len(originals), sum(v.get('bytes', 0) for v in originals.values()) / 1048576.0))
if drive:
    note('%d rows still in drive_links.json, kept as a fallback' % len(drive))

empty = [n for n, v in list(originals.items()) + list(drive.items())
         if isinstance(v, dict) and not v.get('url')]
if empty:
    note('%d rows waiting for an upload, STEP 86: %s' % (len(empty), ', '.join(empty[:6])))

# ------------------------------------------------------------------ report
json.dump(cache, open(CACHE, 'w'))
kind = 'full' if FULL else 'cached'
stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

print('verify_site, %s run, %d pages, %d remote targets' % (kind, len(pages), len(targets)))
for n in notes:
    print('  .. %s' % n)
if fails:
    print('  FAILED %d' % len(fails))
    for c, d in fails:
        print('     %-34s %s' % (c, d))
else:
    print('  everything passed')

if not NOLOG:
    with open(LOG, 'a') as f:
        f.write('\n## %s — v%s — %s run\n\n' % (stamp, want, kind))
        f.write('%d pages, %d remote targets, %d originals.\n\n'
                % (len(pages), len(targets), len(originals)))
        for n in notes:
            f.write('- %s\n' % n)
        if fails:
            f.write('\n**FAILED, %d:**\n\n' % len(fails))
            for c, d in fails:
                f.write('- **%s** — %s\n' % (c, d))
        else:
            f.write('- **everything passed**\n')

sys.exit(1 if fails else 0)
