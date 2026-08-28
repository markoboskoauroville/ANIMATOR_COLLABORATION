#!/usr/bin/env python3
"""Scan every PDF the production owns and write archive.json.

    python3 tools/archive_scan.py

The PDFs are NOT copied into this repository. They already live in the public
BRAIN_BRAKE repo, 646 MB of them, and copying would double that for nothing. The
archive links straight at raw.githubusercontent, so a PDF appears in the archive
the moment it is pushed to the film repo.

Run this when a new PDF is added, then rebuild the site.
"""
import os, json, glob, subprocess, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = os.path.join(os.path.dirname(ROOT), 'BRAIN_BRAKE')

RAW = 'https://raw.githubusercontent.com/markoboskoauroville/%s/main/%s'


def kind(name):
    n = name.lower()
    if 'read_through' in n:
        return ('Read through', 1)
    if n.startswith('the brain brake'):
        return ('The film document', 2)
    if 'script' in n:
        return ('Scripts', 3)
    if any(k in n for k in ('brief', 'guide', 'breakdown', 'act naturally', 'character sheet',
                            'knjiga likova', 'animatorski')):
        return ('Briefs and guides', 4)
    if 'print_pack' in n:
        return ('Print packs', 0)
    return ('Reference', 5)


def gitdate(repo, rel):
    try:
        r = subprocess.run(['git', '-C', repo, 'log', '-1', '--format=%ad', '--date=short', '--', rel],
                           capture_output=True, text=True, timeout=25)
        return r.stdout.strip()
    except Exception:
        return ''


items = []
for repo_path, repo_name, pat in [
        (FILM, 'BRAIN_BRAKE', 'assets/pdf/*.pdf'),
        (ROOT, 'ANIMATOR_COLLABORATION', 'DOCS/*.pdf'),
        (ROOT, 'ANIMATOR_COLLABORATION', '*.pdf')]:
    if not os.path.isdir(repo_path):
        print('  skipped, not on this machine:', repo_path)
        continue
    for p in sorted(glob.glob(os.path.join(repo_path, pat))):
        rel = os.path.relpath(p, repo_path)
        name = os.path.basename(p)
        k, order = kind(name)
        items.append({
            'name': name,
            'repo': repo_name,
            'url': RAW % (repo_name, urllib.parse.quote(rel)),
            'mb': round(os.path.getsize(p) / 1024 / 1024, 1),
            'date': gitdate(repo_path, rel),
            'group': k,
            'order': order,
        })

# newest first inside each group, by name, which carries the version
items.sort(key=lambda i: (i['order'], i['name'].lower()))
out = {'updated': subprocess.run(['date', '+%Y-%m-%d'], capture_output=True, text=True).stdout.strip(),
       'items': items}
json.dump(out, open(os.path.join(ROOT, 'archive.json'), 'w'), indent=2, ensure_ascii=False)

from collections import Counter
c = Counter(i['group'] for i in items)
print('archive.json: %d PDFs, %.0f MB total' % (len(items), sum(i['mb'] for i in items)))
for g, n in c.most_common():
    print('   %-22s %d' % (g, n))
