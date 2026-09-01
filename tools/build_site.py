#!/usr/bin/env python3
"""Build the animator site from catalog.json.

catalog.json is the only truth. Nothing on any page is written by hand, so
nothing can drift from what is actually in the repo.

    python3 tools/build_site.py

Pages: the landing page, one per scene, one breakdown per frame that has
layers, and the documentation page. Every page carries the bar and the gate.
No zips anywhere: Kristijan downloads what he needs, one file at a time.
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(ROOT, 'catalog.json')))
SCENES = CAT['scenes']
VERSION = CAT.get('version', '')
FILM = CAT.get('film', 'THE BRAIN BRAKE')
SITEV = CAT.get('site_version', 0)
SUBTITLE = CAT.get('subtitle', '')
EVENT = CAT.get('event', '')
WORKING = str(CAT.get('working_scene', ''))
ARCHIVE = {}
_ap = os.path.join(ROOT, 'archive.json')
if os.path.exists(_ap):
    ARCHIVE = json.load(open(_ap))


def _readthrough():
    """The read through link in the bar. Always the LATEST version.

    The target comes from catalog.json, never from a filename typed into a page, and
    it is chosen by the HIGHEST VERSION NUMBER in the filename, not by where the entry
    happens to sit in the list and not by its status. Drop v9 in anywhere in the
    catalog and the bar points at it, whether or not anybody remembered to mark v8
    superseded. Numeric, so v12 beats v9 rather than losing to it on a string sort.
    """
    import re as _re
    rts = []
    for e in CAT['entries']:
        if e.get('kind') != 'document' or 'READ_THROUGH' not in e.get('file', ''):
            continue
        m = _re.search(r'_v(\d+)', os.path.basename(e['file']))
        rts.append((int(m.group(1)) if m else -1, e['file']))
    return max(rts)[1] if rts else ''


READTHROUGH = _readthrough()
ENTRIES = CAT['entries']
PASS = 'kristijan'

# 28.8.2026, Baba's ask: the site is open for a few days. Set this back to True to
# put the gate back. The passphrase and the whole gate stay in the code, they are
# simply not inserted into the pages, so turning it back on is one word.
GATED = False
EMAIL = 'marko.bosko@auroville.community'

STATUS = {
    'accepted':     '#3d6b4a',
    'proposal':     '#9C7A31',
    'rejected':     '#a8402f',
    'superseded':   '#8a8170',
    'reference':    '#4a6b7a',
    'note pending': '#a8402f',
}


def human(n):
    for u in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return '%d B' % n if u == 'B' else '%.0f %s' % (n, u)
        n /= 1024.0
    return '%.1f TB' % n


def size_of(rel):
    p = os.path.join(ROOT, rel)
    return os.path.getsize(p) if os.path.exists(p) else 0


def dims(rel):
    try:
        from PIL import Image
        with Image.open(os.path.join(ROOT, rel)) as im:
            return '%d x %d' % im.size
    except Exception:
        return ''


CSS = """
:root{--paper:#f2ebda;--ink:#221f19;--dim:#8a8170;--rule:#cdbfa4;--brass:#9C7A31;--box:#e6dcc4;--slate:#20241f;--body:#4a453b;--card:#fff}
html[data-t=dark]{--paper:#17150f;--ink:#ece4d2;--dim:#8d8574;--rule:#3a352b;--brass:#c9a35a;--box:#221f18;--slate:#0d0c09;--body:#c2bba9;--card:#0d0c09}
html{background:var(--paper)}
img{transition:none}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
 font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
a{color:var(--brass)}
.bar{position:sticky;top:0;z-index:50;background:var(--slate);color:#e6dcc4;
 display:flex;flex-wrap:wrap;align-items:center;gap:2px 18px;padding:11px 22px;
 font:600 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em}
.bar a{color:#c9bfa4;text-decoration:none;padding:4px 0}
.bar a:hover{color:#fff}
.bar a.home{color:#fff;letter-spacing:.14em;margin-right:8px}
.bar a.on{color:#e0b45f;border-bottom:2px solid #e0b45f}
.bar .vb{color:#e0b45f;border:1px solid #4a4436;border-radius:2px;padding:3px 7px;
 font:600 11px/1 ui-monospace,monospace;letter-spacing:.1em;margin-right:6px}
.vdraft{max-width:880px;margin:14px 0 0;padding:11px 16px;background:var(--box);
 border-left:3px solid var(--brass);font:600 13px ui-monospace,monospace;
 letter-spacing:.04em;color:var(--body)}
.vdraft b{color:var(--brass);letter-spacing:.1em}
.bar .sp{flex:1}
.bar a.drive{color:var(--brass);margin-left:14px;white-space:nowrap}
.bar a.rt{color:var(--brass);margin-left:16px;white-space:nowrap}
.bar a.rt:hover{color:#fff}
.bar .th{background:none;border:0;cursor:pointer;color:#c9bfa4;padding:4px 0 4px 16px;
 font:600 12px/1 ui-monospace,monospace;letter-spacing:.08em}
.bar .th:hover{color:#fff}
.bar a.drive:hover{color:#fff}
.wrap{max-width:1500px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:30px;letter-spacing:-.01em;margin:8px 0 6px}
h2{font-size:19px;margin:38px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--rule)}
.lede{max-width:760px;color:var(--body)}
.rules{background:var(--box);border-left:3px solid var(--brass);padding:14px 18px;margin:22px 0;
 max-width:880px;font-size:14.5px}
.scenes{list-style:none;padding:0;margin:24px 0;max-width:880px}
.scenes li{border-top:1px solid var(--rule)}
.scenes a{display:flex;justify-content:space-between;align-items:baseline;gap:14px;
 padding:14px 2px;text-decoration:none;color:var(--ink)}
.scenes a:hover{color:var(--brass)}
.scenes .n{font:600 12px ui-monospace,monospace;color:var(--brass);width:52px;flex:none}
.scenes .t{font-size:19px;flex:1}
.scenes .c{font:12px ui-monospace,monospace;color:var(--dim)}
.row{display:flex;flex-wrap:wrap;margin:0 0 14px}
.cell{width:20%;flex:none}
.cell img{width:100%;display:block}
.meta{padding:6px 8px 12px}
.fid{font:600 12px ui-monospace,monospace;color:var(--brass)}
.ver{font:600 10px ui-monospace,monospace;letter-spacing:.06em;color:var(--dim);
 border:1px solid var(--rule);border-radius:2px;padding:1px 5px;margin-left:6px;
 text-transform:uppercase}
.tag{font:600 10px ui-monospace,monospace;letter-spacing:.08em;color:#fff;
 padding:2px 7px;border-radius:2px;margin-left:6px;text-transform:uppercase}
.note{font-size:13px;line-height:1.5;color:var(--body);margin:5px 0 0}
.bd{display:inline-block;margin-top:7px;font:600 11px ui-monospace,monospace;
 letter-spacing:.06em;text-transform:uppercase}
.pick{display:flex;align-items:center;gap:7px;margin-top:8px;cursor:pointer;
 font:600 10px ui-monospace,monospace;letter-spacing:.07em;color:var(--dim);
 text-transform:uppercase;user-select:none}
.pick input{width:auto;margin:0;accent-color:var(--brass)}
.say{display:none;width:100%;margin:7px 0 2px;padding:8px 9px;
 background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:2px;
 font:13px/1.45 inherit;resize:vertical}
.say:focus{outline:0;border-color:var(--brass)}
.say.on{display:block}
.say.miss{border-color:#a8402f}
.tray{position:fixed;left:0;right:0;bottom:0;z-index:60;background:var(--slate);
 color:#e6dcc4;display:none;align-items:center;gap:16px;padding:13px 22px;
 font:12px ui-monospace,monospace;letter-spacing:.05em;
 box-shadow:0 -2px 14px rgba(0,0,0,.25)}
.tray.on{display:flex}
.tray b{color:#e0b45f}
.tray .sp{flex:1}
.tray a,.tray button{font:600 11px ui-monospace,monospace;letter-spacing:.08em;
 text-transform:uppercase;padding:9px 15px;border:0;border-radius:2px;cursor:pointer;
 text-decoration:none}
.prev{display:none}
.prev.on{position:fixed;inset:0;z-index:100;display:flex;flex-direction:column;
 background:#0e0d0a;margin:0;border-radius:0;overflow:hidden}
.prev.on h3{position:sticky;top:0;flex:0 0 auto}
.prev.on pre{flex:1 1 auto;overflow:auto}
.prev.on .acts{flex:0 0 auto;flex-wrap:wrap}
.prev h3 .gap{flex:1}
.prev h3 .x{font:600 12px ui-monospace,monospace;letter-spacing:.1em;cursor:pointer;
 background:var(--brass);color:#17150f;border:0;border-radius:4px;padding:8px 15px}
.prev h3 .x:hover{background:#f0c876}
.prev_legacy{border-radius:7px;overflow:hidden;background:#0e0d0a;margin:34px 0 96px;display:none;
 box-shadow:0 6px 26px rgba(0,0,0,.28)}
.prev h3{margin:0;padding:9px 14px;background:#1b1a15;border-bottom:1px solid #2b2921;
 font:600 11px ui-monospace,monospace;letter-spacing:.09em;color:#8d8574;
 display:flex;align-items:center;gap:8px}
.prev pre{margin:0;padding:18px 16px;white-space:pre-wrap;word-break:break-word;
 font:13px/1.65 ui-monospace,SFMono-Regular,Menlo,monospace;color:#d9d1bd;
 max-height:46vh;overflow:auto}
.prev pre b{color:#e0b45f;font-weight:600}
.prev pre .cur{background:#e0b45f;color:#0e0d0a}
.prev .acts{display:flex;gap:10px;align-items:center;padding:12px 16px;
 border-top:1px solid #2b2921;background:#141310;flex-wrap:wrap}
.prev .who{display:flex;align-items:center;gap:11px;text-decoration:none;
 padding:5px 12px 5px 5px;border:1px solid #3a352b;border-radius:999px;margin-right:4px}
.prev .who:hover{border-color:var(--brass);background:#1b1a15}
.prev .who img{width:38px;height:38px;border-radius:50%;display:block}
.prev .who .n{font:600 12px ui-monospace,monospace;color:#e6dcc4;letter-spacing:.03em}
.prev .who .e{font:11px ui-monospace,monospace;color:#8d8574}
.prev .who.off{opacity:.35;pointer-events:none}
.prev .sep{flex:1}
.prev .acts button,.prev .acts a{font:600 11px ui-monospace,monospace;letter-spacing:.08em;
 text-transform:uppercase;padding:9px 15px;border-radius:3px;cursor:pointer;
 text-decoration:none;border:1px solid #3a352b;background:none;color:#c9bfa4}
.prev .acts button:hover,.prev .acts a:hover{color:#fff;border-color:#5a5344}
.prev .acts .go{background:var(--brass);color:#17150f;border-color:var(--brass)}
.prev .acts .clr{margin-left:auto;color:#c98a72;border-color:#4a382f}
.prev .acts .clr:hover{color:#fff;background:#3a2620;border-color:#7a4c3c}
.prev .acts .go:hover{color:#17150f}
.prev .acts .go.off{opacity:.35;pointer-events:none}
.tray .go{background:var(--brass);color:#17150f}
.tray .cp{background:none;color:#c9bfa4;border:1px solid #3a352b}
.ask{background:var(--box);border-left:3px solid var(--brass);padding:13px 18px;
 margin:18px 0 24px;max-width:880px;font-size:14px;color:var(--body)}
.log{max-width:880px}
.log .it{border-top:1px solid var(--rule);padding:13px 0}
.log .d{font:11px ui-monospace,monospace;color:var(--dim)}
.it.hasimg{display:flex;gap:16px;align-items:flex-start}
.it .ith{flex:0 0 132px;display:block}
.it .ith img{width:132px;display:block;border:1px solid var(--rule);background:var(--card)}
.it .itx{flex:1;min-width:0}
@media(max-width:640px){.it.hasimg{display:block}.it .ith{margin-bottom:8px}
 .it .ith img{width:100%;max-width:260px}}
.sref{margin:16px 0 8px 44px;padding:16px 18px;background:var(--box);
 border-left:3px solid var(--brass);max-width:1000px}
.sref h4{margin:0 0 4px;font:700 12px ui-monospace,monospace;letter-spacing:.11em;
 text-transform:uppercase;color:var(--brass)}
.sref p{margin:0 0 12px;font-size:13.5px;line-height:1.55;color:var(--body)}
.vids{display:flex;flex-wrap:wrap;gap:12px}
.vid{width:calc(50% - 6px)}
.vid iframe{width:100%;aspect-ratio:16/9;border:1px solid var(--rule);display:block}
.vid span{display:flex;justify-content:space-between;align-items:baseline;gap:10px;
 font:600 10px ui-monospace,monospace;letter-spacing:.06em;
 color:var(--dim);padding-top:5px}
.vid .play{color:var(--brass);text-decoration:none;white-space:nowrap;letter-spacing:.11em}
.vid .play:hover{color:#fff;text-decoration:underline}
@media(max-width:760px){.vid{width:100%}.sref{margin-left:0}}
.flow{margin:22px 0 40px}
.fp{border-top:1px solid var(--rule);padding:22px 0 6px;position:relative}
.fp .hd{display:flex;gap:14px;align-items:baseline;margin-bottom:4px}
.fp .num{flex:0 0 30px;height:30px;border-radius:50%;background:var(--brass);
 color:#17150f;font:700 13px ui-monospace,monospace;display:flex;
 align-items:center;justify-content:center}
.fp h3{margin:0;font:700 14px ui-monospace,monospace;letter-spacing:.09em;
 text-transform:uppercase;color:var(--body)}
.fp .why{margin:2px 0 12px 44px;font-size:14px;line-height:1.55;color:var(--dim);
 max-width:900px}
.board{display:flex;flex-wrap:wrap;gap:8px;margin-left:44px}
.board a{display:block;width:calc(12.5% - 7px)}
.board img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.board a:hover img{border-color:var(--brass)}
.fp .cnt{margin-left:44px;margin-top:9px;font:600 9.5px ui-monospace,monospace;
 letter-spacing:.11em;color:var(--dim)}
.fp .ph{display:inline-block;font:600 9.5px ui-monospace,monospace;letter-spacing:.11em;
 color:#c48a52;border:1px solid #4a382f;border-radius:2px;padding:2px 6px;margin-left:8px}
.fp .lk{display:inline-block;font:600 9.5px ui-monospace,monospace;letter-spacing:.11em;
 color:#17150f;background:var(--brass);border-radius:2px;padding:3px 7px;
 text-decoration:none;margin-left:8px}
@media(max-width:1100px){.board a{width:calc(16.66% - 7px)}}
@media(max-width:760px){.board a{width:calc(25% - 6px)}.fp .why,.board,.fp .cnt{margin-left:0}}
.fp{width:calc(33.333% - 14px);position:relative}
.fp a{display:block;text-decoration:none;color:inherit}
.fp img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.fp .num{position:absolute;top:-9px;left:-9px;width:30px;height:30px;border-radius:50%;
 background:var(--brass);color:#17150f;font:700 13px ui-monospace,monospace;
 display:flex;align-items:center;justify-content:center;z-index:2}
.fp h3{margin:11px 0 5px;font:700 13px ui-monospace,monospace;letter-spacing:.09em;
 text-transform:uppercase;color:var(--body)}
.fp p{margin:0;font-size:13.5px;line-height:1.5;color:var(--dim)}
.fp .ph{display:inline-block;margin-top:7px;font:600 9.5px ui-monospace,monospace;
 letter-spacing:.11em;color:#c48a52;border:1px solid #4a382f;border-radius:2px;padding:2px 6px}
.fp .lk{display:inline-block;margin-top:7px;font:600 9.5px ui-monospace,monospace;
 letter-spacing:.11em;color:#17150f;background:var(--brass);border-radius:2px;padding:3px 7px}
@media(max-width:900px){.fp{width:calc(50% - 10px)}}
@media(max-width:600px){.fp{width:100%}}
.filmfoot{margin:60px 0 10px;padding-top:18px;border-top:1px solid var(--rule);
 text-align:center;font:700 11px ui-monospace,monospace;letter-spacing:.16em;
 color:var(--dim)}
.filmfoot span{display:block;font-weight:600;font-size:9px;letter-spacing:.14em;
 padding-top:6px;color:var(--dim);opacity:.75}
.srcbox{margin:16px 0 6px;padding:13px 16px;background:var(--box);
 border-left:3px solid var(--brass)}
.srcbox .t{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.srcbox .t b{font:700 10.5px ui-monospace,monospace;letter-spacing:.11em;
 text-transform:uppercase;color:var(--body)}
.srcbox p{margin:7px 0 0;font-size:12.5px;line-height:1.55;color:var(--dim)}
.creds{margin:20px 0 8px;max-width:760px}
.creds .hd{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
 margin-bottom:8px}
.creds .hd b{font:700 11px ui-monospace,monospace;letter-spacing:.11em;text-transform:uppercase;
 color:var(--body)}
.creds textarea{width:100%;min-height:330px;background:var(--card);color:var(--body);
 border:1px solid var(--rule);border-radius:3px;padding:14px 16px;
 font:400 12.5px/1.65 ui-monospace,monospace;resize:vertical}
.creds .warn{font:600 9.5px ui-monospace,monospace;letter-spacing:.1em;color:#c48a52;
 padding-top:7px;display:block}
@media(max-width:760px){.creds{margin-left:0}}
.seqstrip{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 8px}
.seqstrip .f{width:calc(14.28% - 9px);min-width:110px}
.seqstrip .f img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.seqstrip .f .n{font:600 8.5px ui-monospace,monospace;letter-spacing:.06em;color:var(--dim);
 padding-top:5px}
.seqstrip .f iframe,.seqstrip .f video{width:100%;aspect-ratio:16/9;border:1px solid var(--rule);display:block;
 background:var(--card);pointer-events:none}
.seqstrip .f .vid{position:relative}
.seqstrip .f .vid{cursor:zoom-in}
.seqstrip .f .n{display:block}
.seqstrip .f .pr{display:inline-block;margin-top:4px}
.seqstrip .f .pr{font:700 7.5px ui-monospace,monospace;letter-spacing:.09em;color:#17150f;
 background:var(--brass);border-radius:2px;padding:2px 5px;text-decoration:none;
 white-space:nowrap}
.seqstrip .f .pr:hover{background:#f0c876}
.seqstrip .f .vid .lbl{position:absolute;left:5px;bottom:5px;background:var(--brass);
 color:#17150f;font:700 7.5px ui-monospace,monospace;letter-spacing:.1em;padding:2px 5px;
 border-radius:2px}
.seqstrip .cut{width:16px;display:flex;align-items:center;justify-content:center;
 font:700 12px ui-monospace,monospace;color:var(--brass)}
@media(max-width:820px){.seqstrip .f{width:calc(33.33% - 8px)}.seqstrip .cut{display:none}}
.asset{display:flex;flex-wrap:wrap;gap:9px;margin:10px 0 26px}
.asset a{width:calc(12.5% - 8px);display:block;text-decoration:none;color:inherit}
.asset img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.asset a:hover img{border-color:var(--brass)}
.asset .c{font:600 8px ui-monospace,monospace;letter-spacing:.03em;color:var(--dim);
 padding-top:3px;word-break:break-all}
.asset .sup img{opacity:.42}
.asset .sup .c{color:#8a7a5e}
@media(max-width:900px){.asset a{width:calc(25% - 7px)}}
@media(max-width:600px){.asset a{width:calc(33.333% - 6px)}}
.flight{margin:0 0 22px;padding:16px 20px;background:var(--box);
 border-left:3px solid var(--brass);max-width:1180px}
.flight b{display:block;font:700 11px ui-monospace,monospace;letter-spacing:.13em;
 text-transform:uppercase;color:var(--body);margin-bottom:8px}
.flight p{margin:0;font-size:13px;line-height:1.65;color:var(--dim)}
.sitev{font:700 10px ui-monospace,monospace;letter-spacing:.14em;color:#17150f;
 background:var(--brass);border-radius:3px;padding:3px 8px;margin-left:10px}
.mast{margin:0 0 26px}
.mast img{width:100%;max-width:760px;display:block;border:1px solid var(--rule);
 background:var(--card);margin:0 auto}
.mast .sub{text-align:center;font:600 10px ui-monospace,monospace;letter-spacing:.18em;
 color:var(--dim);padding-top:10px;text-transform:uppercase}
.rtsheet{max-width:1180px;margin:0 auto}
.tiny{display:flex;flex-wrap:wrap;gap:9px;margin:12px 0 4px}
.tiny a{width:calc(16.666% - 8px);display:block;text-decoration:none;color:inherit}
.tiny img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.tiny a:hover img{border-color:var(--brass)}
.tiny .c{font:600 8.5px ui-monospace,monospace;letter-spacing:.04em;color:var(--dim);padding-top:4px}
.tiny .ln{padding-top:5px}
.tiny .ln .sp{display:block;font:700 7.5px ui-monospace,monospace;letter-spacing:.11em;
 color:var(--brass)}
.tiny .ln .tx{display:block;font-size:11.5px;line-height:1.45;color:var(--body);padding-top:2px}
.tiny .ln .rec{display:block;font:600 7px ui-monospace,monospace;letter-spacing:.09em;
 color:var(--dim);padding-top:3px}
@media(max-width:900px){.tiny a{width:calc(25% - 7px)}}
@media(max-width:600px){.tiny a{width:calc(33.333% - 6px)}}
.cardhead{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
 padding-bottom:8px;border-bottom:1px solid var(--rule);margin-bottom:16px}
.cardhead .code{font:700 15px ui-monospace,monospace;letter-spacing:.1em;color:var(--brass)}
.dl{font:600 10px ui-monospace,monospace;letter-spacing:.12em;color:#17150f;
 background:var(--brass);border-radius:3px;padding:8px 15px;text-decoration:none;white-space:nowrap}
.dl:hover{background:#f0c876}
.cardimg{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.aud{margin:18px 0 6px;padding:14px 16px;background:var(--box);border-left:3px solid var(--brass)}
.aud .t{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:9px}
.aud .t b{font:700 11px ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;
 color:var(--body)}
.aud .t span{font:600 9.5px ui-monospace,monospace;color:var(--dim)}
.aud audio{width:100%;display:block}
.slug{font:700 12px ui-monospace,monospace;letter-spacing:.11em;color:var(--body);margin:20px 0 10px}
.lay{display:flex;flex-wrap:wrap;gap:14px;margin:14px 0}
.lay .l{width:calc(33.333% - 10px)}
.lay .l img{width:100%;display:block;border:1px solid var(--rule)}
.lay .l .n{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding-top:6px}
.lay .l .n span{font:600 9px ui-monospace,monospace;letter-spacing:.1em;color:var(--dim)}
@media(max-width:700px){.lay .l{width:100%}}
.rtph{margin:34px 0 6px;padding-bottom:6px;border-bottom:1px solid var(--rule);
 display:flex;gap:12px;align-items:baseline}
.rtph .n{width:26px;height:26px;border-radius:50%;background:var(--brass);color:#17150f;
 font:700 12px ui-monospace,monospace;display:flex;align-items:center;justify-content:center;flex:0 0 26px}
.rtph h3{margin:0;font:700 13px ui-monospace,monospace;letter-spacing:.1em;
 text-transform:uppercase;color:var(--body)}
.rtph .st{margin-left:auto;font:600 9.5px ui-monospace,monospace;letter-spacing:.1em;color:var(--dim)}
.rtrow{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0 4px}
.rtc{width:calc(25% - 9px)}
.rtc .box{width:100%;aspect-ratio:16/9;border:1px solid var(--rule);background:var(--card);
 display:flex;align-items:center;justify-content:center;overflow:hidden}
.rtc .box img{width:100%;height:100%;object-fit:cover;display:block}
.rtc .box.empty{background:#0b0a08;border-style:dashed}
.rtc .box.empty span{font:600 9px ui-monospace,monospace;letter-spacing:.12em;color:#4a4438}
.rtc .cap{font:600 9.5px ui-monospace,monospace;letter-spacing:.05em;color:var(--dim);padding-top:5px}
.rtc .line{font-size:12.5px;line-height:1.45;color:var(--body);padding-top:3px}
@media(max-width:900px){.rtc{width:calc(50% - 6px)}}
.arc{margin:10px 0 34px}
.arcg{font:600 11px ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;
 color:var(--brass);margin:26px 0 6px;padding-bottom:5px;border-bottom:1px solid var(--rule)}
.arcr{display:flex;gap:14px;align-items:baseline;padding:7px 2px;
 border-bottom:1px solid rgba(140,130,110,.16)}
.arcr a{flex:1;color:var(--body);text-decoration:none;font-size:14px}
.arcr a:hover{color:var(--brass);text-decoration:underline}
.arcr .d{font:600 10px ui-monospace,monospace;color:var(--dim);white-space:nowrap}
.arcr .z{font:600 10px ui-monospace,monospace;color:var(--dim);white-space:nowrap;width:56px;text-align:right}
.rates{margin:18px 0 34px;border-top:1px solid var(--rule)}
.rt{display:flex;gap:18px;align-items:flex-start;padding:15px 0;
 border-bottom:1px solid var(--rule)}
.rt .fps{flex:0 0 118px;font:700 25px ui-monospace,monospace;color:var(--brass);
 line-height:1;letter-spacing:-.02em}
.rt .fps small{display:block;font:600 10px ui-monospace,monospace;letter-spacing:.14em;
 color:var(--dim);margin-top:6px}
.rt .bar{flex:0 0 92px;height:11px;margin-top:6px;background:#211f19;border-radius:2px;
 overflow:hidden}
.rt .bar i{display:block;height:100%;background:var(--brass)}
.rt h4{margin:0 0 5px;font:600 12px ui-monospace,monospace;letter-spacing:.12em;
 text-transform:uppercase;color:var(--body)}
.rt p{margin:0;font-size:14px;line-height:1.55;color:var(--body)}
@media(max-width:700px){.rt .bar{display:none}.rt .fps{flex:0 0 92px;font-size:21px}}
.sym{display:flex;flex-wrap:wrap;gap:26px;margin:18px 0 10px}
.sym .s{width:calc(50% - 13px);display:flex;gap:16px;align-items:flex-start}
.sym .s img{width:150px;flex:0 0 150px;border:1px solid var(--rule);display:block}
.sym .s h4{margin:0 0 5px;font:600 12px ui-monospace,monospace;letter-spacing:.12em;
 text-transform:uppercase;color:var(--brass)}
.sym .s p{margin:0;font-size:14px;line-height:1.5;color:var(--body)}
@media(max-width:760px){.sym .s{width:100%}}
.ex .cell{width:33.333%}
.exi{width:100%;display:block;border:1px solid var(--rule)}
.exi.trans{background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/16px 16px}
@media(max-width:700px){.ex .cell{width:100%}}
.rule1{background:var(--slate);color:#e6dcc4;border-left:3px solid var(--brass);
 padding:13px 18px;margin:16px 0 10px;max-width:880px;font-size:14.5px}
.rule1 b{color:#e0b45f;letter-spacing:.04em}
.tip{font:600 13px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;
 color:var(--brass);margin:0 0 26px;text-transform:uppercase}
.crumb{font:600 11px ui-monospace,monospace;letter-spacing:.12em;color:var(--dim);
 text-transform:uppercase;margin:0 0 4px}
.crumb a{color:var(--brass);text-decoration:none}
.seq{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 30px;align-items:flex-start}
.seq a{width:calc(20% - 8px);text-decoration:none;color:inherit;display:block}
.seq img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.seq .cap{font:600 9.5px ui-monospace,monospace;letter-spacing:.06em;color:var(--dim);
 padding:5px 1px 0;display:flex;justify-content:space-between;gap:6px}
.seq .cap b{color:var(--brass);font-weight:600}
.seq .brk{width:100%;height:0}
@media(max-width:760px){.seq a{width:calc(50% - 5px)}}
.shot .cell a.open{display:block;text-decoration:none;color:inherit}
.shot .cell img{border:1px solid var(--rule)}
.kf{font:600 10px ui-monospace,monospace;letter-spacing:.08em;color:var(--dim);
 text-transform:uppercase;margin-left:6px}
.ovl{max-width:1040px;margin:16px 0 30px}
.ovl img{width:100%;display:block;border:1px solid var(--rule);
 background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/22px 22px}
.ovl .meta{padding:9px 2px 0}
.sheet{max-width:1040px;margin:0 0 26px}
.sheet img{width:100%;display:block;border:1px solid var(--rule);background:var(--card)}
.sheet .meta{padding:9px 2px 0}
.doc{display:flex;gap:20px;border-top:1px solid var(--rule);padding:20px 0;max-width:1000px}
.doc img{width:230px;border:1px solid var(--rule);background:var(--card);flex:none}
.lay{display:flex;gap:18px;align-items:flex-start;border-top:1px solid var(--rule);padding:16px 0}
.lay img{width:260px;border:1px solid var(--rule);
 background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/18px 18px}
.lay .n{font:600 13px ui-monospace,monospace}
.lay .s{font:11px ui-monospace,monospace;color:var(--dim);margin:3px 0 6px}
.gate{position:fixed;inset:0;background:var(--paper);z-index:99;
 display:flex;align-items:center;justify-content:center}
.gate form{text-align:center}
.gate input{font:16px ui-monospace,monospace;padding:10px 14px;border:1px solid var(--rule);
 background:var(--card);color:var(--ink);width:230px}
.gate p{font:12px ui-monospace,monospace;color:var(--dim);letter-spacing:.1em}
.gate .rem{display:flex;align-items:center;justify-content:center;gap:8px;
 margin-top:16px;font:12px ui-monospace,monospace;color:var(--dim);
 letter-spacing:.04em;cursor:pointer;user-select:none}
.gate .rem input{margin:0;width:auto;padding:0;border:0;background:none;accent-color:var(--brass)}
@media(max-width:1100px){.cell{width:33.333%}}
@media(max-width:640px){.cell{width:50%}.wrap{padding:20px 14px 50px}}
"""

GATE = """<div class=gate id=gate><form onsubmit="g(event)">
<p>THE BRAIN BRAKE</p>
<input id=pw autofocus autocomplete=off>
<label class=rem><input type=checkbox id=rem checked> keep me signed in on this device</label>
<p id=ge></p></form></div>
<script>
function g(e){e.preventDefault();
 var v=document.getElementById('pw').value.trim().toLowerCase();
 if(v==='PASSPHRASE'){
   var keep=document.getElementById('rem').checked;
   document.cookie='bbc=1;path=/;samesite=lax'+(keep?';max-age=31536000':'');
   try{keep?localStorage.setItem('bbc','1'):localStorage.removeItem('bbc');}catch(x){}
   o();
 } else {document.getElementById('ge').textContent='NO';
   document.getElementById('pw').value='';document.getElementById('pw').focus();}}
function o(){document.getElementById('gate').style.display='none';
 document.getElementById('app').style.display='block';}
function seen(){ if(document.cookie.indexOf('bbc=1')>-1) return true;
 try{ if(localStorage.getItem('bbc')==='1'){
   document.cookie='bbc=1;path=/;max-age=31536000;samesite=lax'; return true;} }catch(x){}
 return false;}
if(seen()){window.addEventListener('DOMContentLoaded',o);}
</script>""".replace('PASSPHRASE', PASS)


DRIVE = 'https://drive.google.com/drive/folders/1INASz6hT4OUQo4UrpT62rMJaF24Amnuu'


TRAY = """
<div class=prev id=prev>
  <h3>email composer &nbsp;·&nbsp; %s<span class=gap></span><button class=x id=x onclick="shut()" title="close">CLOSE &times;</button></h3>
  <pre id=pv></pre>
  <div class=acts>
    <a class=who id=who href="#" title="open this in your mail app">
      <img src="../mid/marko.png" alt="" loading=lazy>
      <span><span class=n>Marko</span><br><span class=e>EMAILADDR</span></span>
    </a>
    <span class=sep></span>
    <button onclick="cp()" id=cpb>copy the whole message</button>
    <button onclick="cpa()" id=cab>copy just the address</button>
    <button onclick="clr()" id=clb class=clr>clean</button>
  </div>
</div>
<div class=tray id=tray>
  <span id=sum></span>
  <span class=sp></span>
  <a class=go id=go href="#">go to the composer</a>
</div>
<script>
var NL=String.fromCharCode(10);
window.__open=false;
function shut(){ window.__open=false; document.body.style.overflow=''; upd(); }
function clr(){
  // untick everything and empty every box, then close and go back to the top.
  // No confirm: nothing here is destructive, the pictures are untouched, and a
  // confirm dialog on a phone costs more than retyping a sentence.
  [].slice.call(document.querySelectorAll('.pk')).forEach(function(c){ c.checked=false; });
  [].slice.call(document.querySelectorAll('.say')).forEach(function(t){ t.value=''; });
  window.__open=false;
  document.body.style.overflow='';
  upd();
  window.scrollTo(0,0);
}
function open_(){ window.__open=true; document.body.style.overflow='hidden'; upd(); }
function boxes(k){return [].slice.call(document.querySelectorAll('.pk:checked'))
  .filter(function(x){return x.dataset.k===k;});}
function said(f){var t=document.querySelector('.say[data-f="'+f+'"]');
  return t?t.value.trim():'';}
function text(){
  var b=boxes('breakdown').map(function(x){return x.dataset.f;});
  var m=boxes('modification').map(function(x){return x.dataset.f;});
  var out=[];
  if(b.length) out.push('BREAKDOWN into background and foreground:'+NL+'  '+b.join(NL+'  '));
  if(m.length){
    var lines=m.map(function(f){return '  '+f+NL+'    '+(said(f)||'(nothing written)');});
    out.push('MODIFICATION:'+NL+lines.join(NL+NL));
  }
  return out.join(NL+NL);
}
function upd(){
  // show a box only for a ticked frame
  [].slice.call(document.querySelectorAll('.pk[data-k=modification]')).forEach(function(c){
    var t=document.querySelector('.say[data-f="'+c.dataset.f+'"]');
    if(!t) return;
    t.className='say'+(c.checked?' on':'');
    if(!c.checked) t.value='';
  });
  var b=boxes('breakdown'), m=boxes('modification');
  var missing=m.filter(function(x){return !said(x.dataset.f);});
  var parts=[];
  if(b.length) parts.push('<b>'+b.length+'</b> breakdown');
  if(m.length) parts.push('<b>'+m.length+'</b> modification');
  if(missing.length) parts.push('<span style="color:#e08a6f">say what to change on '
    +missing.map(function(x){return x.dataset.f;}).join(', ')+'</span>');
  document.getElementById('sum').innerHTML=parts.join(' &nbsp;·&nbsp; ');
  // the tray exists to get you to the composer. Once the composer is on screen it is
  // a button to somewhere you already are, sitting on top of the buttons you want.
  // the tray is the way in. The composer is a full screen sheet, so only one of
  // the two is ever on screen.
  document.getElementById('tray').className =
    'tray' + (((b.length + m.length) && !window.__open) ? ' on' : '');

  var any=(b.length+m.length)>0;
  var subj=[];
  if(b.length) subj.push('breakdown '+b.map(function(x){return x.dataset.f;}).join(', '));
  if(m.length) subj.push('modification '+m.map(function(x){return x.dataset.f;}).join(', '));
  var subject='%s request: '+subj.join('; ');
  var href='mailto:EMAILADDR?subject='+encodeURIComponent(subject)
    +'&body='+encodeURIComponent(text()+NL+NL+location.href);

  // the preview at the foot of the page, live as he ticks
  var pv=document.getElementById('pv'), pr=document.getElementById('prev');
  if(!any && window.__open) window.__open=false;      // nothing ticked, nothing to send
  if(!any) document.body.style.overflow='';
  pr.className='prev'+((any && window.__open)?' on':'');
  if(any){
    var esc=function(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;');};
    pv.innerHTML='<b>To:</b>      EMAILADDR'+NL+'<b>Subject:</b> '+esc(subject)+NL+NL
      +esc(text())+NL+NL+esc(location.href)+'<span class=cur> </span>';
  }

  var g1=document.getElementById('go');
  if(g1){ g1.href='#'; g1.onclick=function(ev){ ev.preventDefault(); open_(); };
          g1.style.opacity=1; g1.style.pointerEvents='auto'; }
  var w=document.getElementById('who');
  if(w){
    if(missing.length){ w.className='who off'; w.href='#'; }
    else { w.className='who'; w.href=href; }
  }
}
function cpa(){navigator.clipboard.writeText('EMAILADDR').then(function(){
  var x=document.getElementById('cab');x.textContent='copied';
  setTimeout(function(){x.textContent='copy just the address';},1400);});}
function cp(){
  var t=document.getElementById('pv').innerText.replace(/\u00a0/g,' ').trimEnd();
  navigator.clipboard.writeText(t).then(function(){
    ['cpb'].forEach(function(id){var x=document.getElementById(id);
      if(x){x.textContent='copied';setTimeout(function(){
        x.textContent='copy the whole message';},1400);}});
  });}
</script>"""


def bar(here, r):
    """An invisible table. Home and documentation left, the scenes in the middle,
    and the last cell is always Google Drive, hard right."""
    # HOME, then the scenes, then everything else. The scenes are what the animator
    # comes here for, so they sit before the documents.
    o = ['<div class=bar><a class=home href="%sindex.html">HOME</a>' % r]
    for n in sorted(SCENES, key=int):
        o.append('<a href="%sBB_C_%s/index.html"%s>SC%s</a>'
                 % (r, n, ' class=on' if here == n else '', n))
    o.append('<span class=sp></span>')
    o.append(('<span class=vb>%s</span>' % VERSION) if VERSION else '')
    o.append('<a href="%sfootage.html"%s>FOOTAGE</a>'
             % (r, ' class=on' if here == 'footage' else ''))
    o.append('<a href="%sassets.html"%s>ASSETS</a>'
             % (r, ' class=on' if here == 'assets' else ''))
    o.append('<a href="%sbrainstorm.html"%s>BRAINSTORM</a>'
             % (r, ' class=on' if here == 'brainstorm' else ''))
    o.append('<a href="%sbreakdown.html"%s>BREAKDOWN</a>'
             % (r, ' class=on' if here == 'breakdown' else ''))
    o.append('<a href="%sdocumentation.html"%s>DOCUMENTATION</a>'
             % (r, ' class=on' if here == 'doc' else ''))
    if ARCHIVE.get('items'):
        o.append('<a href="%sarchive.html"%s>ARH</a>'
                 % (r, ' class=on' if here == 'archive' else ''))
    o.append('<span class=sp></span>')
    o.append('<a class=drive href="%s" target=_blank rel=noopener>GDRIVE &nearr;</a>' % DRIVE)
    o.append('<span class=sitev title="site version">v%d</span>' % SITEV)
    o.append('<button class=th id=th onclick="tt()" title="light or dark">&#9681;</button>')
    o.append('</div>')
    return ''.join(o)


def page(title, body, here=None, depth=0):
    r = '../' * depth
    return ('<!doctype html><html lang=en><head><meta charset=utf-8>'
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            '<title>%s</title>'
            '<link rel=icon href="%sfavicon.svg" type="image/svg+xml">'
            '<link rel=icon href="%sfavicon-32.png" sizes="32x32">'
            '<link rel=icon href="%sfavicon-16.png" sizes="16x16">'
            '<link rel=apple-touch-icon href="%sapple-touch-icon.png">'
            '<meta name=theme-color content="#20241f">'
            '<script>(function(){try{var t=localStorage.getItem("bbt");'
            'if(!t)t=matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light";'
            'document.documentElement.dataset.t=t;}catch(e){}})();'
            'function tt(){var d=document.documentElement,'
            'n=d.dataset.t==="dark"?"light":"dark";d.dataset.t=n;'
            'try{localStorage.setItem("bbt",n);}catch(e){}}</script>'
            '<style>%s</style></head><body>%s'
            # HIDDEN ONLY WHEN THERE IS A GATE TO UNHIDE IT. On 28.8.2026 the gate was
            # switched off and this div stayed display:none, so every page went blank
            # in the middle of production. Nothing else on the site ever un-hides it.
            '<div id=app style="display:%s">%s<div class=wrap>%s'
            # the film's full name sits at the foot of every page, so the subtitle
            # travels with the work wherever a page is opened or printed
            '<p class=filmfoot>%s<br><span>%s &nbsp;&middot;&nbsp; %s</span></p>'
            '</div></div></body></html>'
            % (title, r, r, r, r, CSS, GATE if GATED else '',
               'none' if GATED else 'block', bar(here, r), body,
               FILM, SUBTITLE, EVENT))


import re


def ver(e):
    """1-1-v3.png -> v3 . No version in the name -> nothing."""
    m = re.search(r'[_-](v\d+)(?:[_.]|$)', os.path.basename(e.get('file', '')), re.I)
    return m.group(1).lower() if m else ''


def tag(st):
    return '<span class=tag style="background:%s">%s</span>' % (STATUS.get(st, '#8a8170'), st)


def frames_of(scene):
    return [e for e in ENTRIES if e.get('kind') == 'frame'
            and e.get('frame', '').split('.')[0] == str(scene)]


# the two big read throughs live on Drive now: at 75 MB each they took the
# published site over the GitHub Pages 1 GB limit and the build failed with no
# message at all. Anything that large is a Drive artefact, not a site file.
MOVED_TO_DRIVE = {
    'DOCS/4-BRAIN_BRAKE_READ_THROUGH_v4.pdf':
        'https://drive.google.com/file/d/1cXUQxWPi71RbyXmFIgJZdfqjcqpGyQAp/view',
    'DOCS/8-BRAIN_BRAKE_READ_THROUGH_v8.pdf':
        'https://drive.google.com/file/d/1zsm3VOXz2dshiZol2oA3KB0W3eWEo4Yr/view',
}


# The watch folder daemon uploads every original to Drive and records the link
# in drive_links.json, keyed by file name. It writes that file the moment a
# frame arrives, which is BEFORE the chat session has written a catalogue entry
# for it. Looking the link up here rather than storing it on the entry removes
# the ordering dependency entirely: either side can go first.
DRIVE = {}
_dl = os.path.join(ROOT, 'drive_links.json')
if os.path.exists(_dl):
    try:
        DRIVE = json.load(open(_dl))
    except Exception:
        DRIVE = {}


def full_link(path):
    """Where the full resolution original lives, or the local file if it is
    still in the repository."""
    return DRIVE.get(os.path.basename(path)) or path


def small(path, size='mid'):
    # a transparent png keeps its alpha: it gets a small png, never a jpg
    if path.lower().endswith('.png') and os.path.exists(
            os.path.join(ROOT, 'mid', os.path.basename(path))):
        cand = os.path.join('mid', os.path.basename(path))
        return cand if os.path.exists(os.path.join(ROOT, cand)) else path
    """Never put a full resolution file in an <img>.

    422 MB of originals sit in this repository. The same set is 8 MB as mid and
    0.7 MB as tiny, so a page that reaches for the original is hundreds of times
    heavier than it needs to be, on a phone, on Indian mobile data. The full file
    is reached ONLY by pressing download.

    Falls back to the original if no small version was generated, so a new image
    still shows rather than breaking.
    """
    base = os.path.basename(path).rsplit('.', 1)[0].replace(' ', '_')
    cand = os.path.join(size, base + '.jpg')
    return cand if os.path.exists(os.path.join(ROOT, cand)) else path


def resolve(e):
    """A placeholder that replaces itself.

    An entry may carry `prefer`, a list of globs. The first one that actually
    exists on disk wins and `file` is the fallback. So the moment a real drawn
    Ganesha lands in the repo under a matching name, the site swaps to it on the
    next build and the placeholder wording disappears by itself. Nobody has to
    remember, which is the only kind of reminder that works.

    Returns (path, is_placeholder).
    """
    for pat in e.get('prefer', []):
        hits = sorted(glob.glob(os.path.join(ROOT, pat)))
        if hits:
            return os.path.relpath(hits[-1], ROOT), False
    return e['file'], bool(e.get('prefer'))


BOARD = {}
_bp = os.path.join(ROOT, 'flow', 'board.json')
if os.path.exists(_bp):
    BOARD = json.load(open(_bp))


def style_for(n):
    return [e for e in ENTRIES if e.get('kind') == 'style' and str(e.get('after', '')) == str(n)]


def flow_of():
    return sorted([e for e in ENTRIES if e.get('kind') == 'flow'],
                  key=lambda e: int(e.get('n', 0)))


def rates_of():
    return [e for e in ENTRIES if e.get('kind') == 'rate'
            and e.get('status') != 'superseded']


def symbols_of():
    return [e for e in ENTRIES if e.get('kind') == 'symbol'
            and e.get('status') != 'superseded']


def examples_of(scene=None):
    out = [e for e in ENTRIES if e.get('kind') == 'example'
           and e.get('status') != 'superseded']
    if scene is None:
        return [e for e in out if not e.get('scene')]
    return [e for e in out if str(e.get('scene', '')) == str(scene)]


# the three parts of a layered delivery, in the order they are looked at
PARTS = [('plate', 'PLATE', 'the drawing with the moving thing taken out of it'),
         ('layer', 'LAYER', 'the moving thing alone, transparent everywhere else'),
         ('composite', 'COMPOSITE', 'the two stacked, which is what it must look like')]


def example_block(e, prefix=''):
    """plate, layer, composite, side by side. One source, so the landing page and a
    scene page can never drift apart."""
    o = ['<h2>%s</h2>' % e.get('title', 'Layers')]
    if e.get('note'):
        o.append('<p class=lede>%s</p>' % e['note'])
    o.append('<div class="row ex">')
    for key, label, blurb in PARTS:
        f = e.get(key)
        if not f:
            continue
        cls = 'exi trans' if key == 'layer' else 'exi'
        o.append('<div class=cell><a href="%s%s"><img class="%s" src="%s%s" alt=""></a>'
                 '<div class=meta><span class=fid>%s</span>'
                 '<p class=note>%s</p>'
                 '<p><a href="%s%s" download>Download</a></p></div></div>'
                 % (prefix, f, cls, prefix, f, label, blurb, prefix, f))
    o.append('</div>')
    return ''.join(o)


def keyframes_of(shot):
    """Every key frame inside one shot, in catalog order."""
    return [e for e in ENTRIES if e.get('kind') == 'keyframe'
            and str(e.get('shot', '')) == str(shot)]


def shot_key(sh):
    """Sort 1.1 before 1.2b before 1.3, and 1.10 after 1.9.

    Catalog order is not shot order: an entry rewritten later moves to the end of
    the file, and the scene page would then list its shots out of sequence.
    """
    import re as _r
    parts = str(sh).split('.')
    out = []
    for p in parts:
        m = _r.match(r'(\d*)([a-z]*)', p)
        out.append((int(m.group(1)) if m.group(1) else 0, m.group(2)))
    return out


def shots_of(scene):
    """The shot ids in a scene, in shot order."""
    out = set()
    for e in ENTRIES:
        if e.get('kind') != 'keyframe':
            continue
        sh = str(e.get('shot', ''))
        if sh.split('.')[0] == str(scene):
            out.add(sh)
    return sorted(out, key=shot_key)


def representative(shot):
    """The one key frame that stands for the shot on the scene page.

    Marked with "representative": true in the catalog. Failing that the newest one
    that is not retired, so a shot always has a face even when nobody has chosen.
    """
    ks = keyframes_of(shot)
    if not ks:
        return None
    for e in ks:
        if e.get('representative'):
            return e
    live = [e for e in ks if e.get('status') != 'superseded']
    return (live or ks)[-1]


def shot_page(shot):
    return 'shot-%s.html' % str(shot).replace('.', '-')


def rule_strip(scene):
    """The one rule, at the top, on the scene we are actually working in."""
    if not WORKING or str(scene) != WORKING:
        return ''
    return ('<div class=rule1><b>WE ARE WORKING ON SCENE %s.</b> '
            'Everything happens on this page. Nothing is written on any other scene page.</div>'
            '<p class=tip>scene -&gt; shot -&gt; key frame</p>' % WORKING)


def overlays_of(scene=None):
    """Things that sit on top of a frame rather than being one. The panel border
    is the first: the artwork ships edge to edge and this is the frame, on its own
    layer.

    With no scene, every current overlay, which is what the landing page wants.
    With a scene, only the ones pinned to it by a `scene` key in the catalog, so
    the frame can sit on the scene page the animator is actually working in.

    Retired ones never get a section. They stay reachable in the What changed log
    with their note and their link, because nothing is deleted.
    """
    out = [e for e in ENTRIES if e.get('kind') == 'overlay'
           and e.get('status') != 'superseded']
    if scene is None:
        return out
    return [e for e in out if str(e.get('scene', '')) == str(scene)]


def overlay_block(e, prefix=''):
    """One source for the frame block, so the landing page and the scene page can
    never drift apart."""
    lbl = ('%s %s' % (e.get('title', 'the frame'), ver(e))).strip()
    return ('<h2>The frame</h2>'
            '<div class=ovl><a href="%s%s"><img src="%s%s" alt="" loading=lazy></a>'
            '<div class=meta><span class=fid>%s</span>%s%s'
            '<p class=note>%s</p><p><a href="%s%s" download>Download the PNG</a></p>%s</div></div>'
            % (prefix, e['file'], prefix, small(e['file']), os.path.basename(e['file']),
               ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
               tag(e.get('status', 'reference')), e.get('note', 'note pending'),
               prefix, e['file'], picks(lbl)))


def sheets_of(scene):
    """Character sheets. They sit at the top of a scene page, big, above the frames,
    because they are who everybody in the scene is."""
    return [e for e in ENTRIES if e.get('kind') == 'sheet'
            and e.get('frame', '').split('.')[0] == str(scene)]


def picks(label):
    """The two tick boxes and the box he types in. Every picture on the site gets
    them, a sheet exactly as much as a frame."""
    return ('<label class=pick><input type=checkbox class=pk data-k="breakdown" '
            'data-f="%s" onchange="upd()"> need a breakdown</label>'
            '<label class=pick><input type=checkbox class=pk data-k="modification" '
            'data-f="%s" onchange="upd()"> need a modification</label>'
            '<textarea class=say data-f="%s" oninput="upd()" rows=3 '
            'placeholder="what needs to change?"></textarea>' % (label, label, label))


def layers_of(e):
    base = os.path.splitext(os.path.basename(e['file']))[0]
    d = os.path.dirname(e['file'])
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, d, base + '_*'))):
        low = os.path.basename(p).lower()
        if any(k in low for k in ('_bg', '_background', '_fg', '_foreground', '_comp')):
            out.append(os.path.join(d, os.path.basename(p)))
    return out


for n in sorted(SCENES, key=int):
    fs = frames_of(n)
    sh = sheets_of(n)
    b = ['<h1>Scene %s &nbsp;<span style="color:#8a8170;font-weight:400">%s</span></h1>'
         % (n, SCENES[n])]
    b.append(rule_strip(n))

    # THE FIRST THING ON THE PAGE. The scene as one strip, in order. Everything
    # else on this page is reference for it, so it comes after.
    sh_ids = shots_of(n)
    seq = []
    for sid in sh_ids:
        for e in keyframes_of(sid):
            if e.get('status') != 'superseded':
                seq.append((sid, e))
    if seq:
        b.append('<h2>Storyboard</h2>')
        b.append('<p class=lede>The whole scene in order, %d frames across %d shots, read left to '
                 'right like a silent film. This is the scene. Everything below it is the breakdown: '
                 'the sheets, the frame and the shots opened one at a time. '
                 'Click any frame to open the shot it belongs to.</p>' % (len(seq), len(sh_ids)))
        b.append('<div class=seq>')
        last = None
        for sid, e in seq:
            if last is not None and sid != last:
                b.append('<div class=brk></div>')
            last = sid
            b.append('<a href="%s"><img src="../%s" alt="" loading=lazy>'
                     '<div class=cap><b>%s</b><span>%s</span></div></a>'
                     % (shot_page(sid), small(e['file'], 'tiny'), sid,
                        os.path.basename(e['file']).replace('.png', '').replace('.jpg', '')))
        b.append('</div>')

    b.append('<div class=ask><b>Breakdowns are made on request.</b> A frame is delivered flat '
             'unless you ask for it to be split into background and foreground, because most '
             'frames do not need it and splitting one takes real time. Tick the ones you want '
             'and press the button at the bottom. Marko gets an email and does them.</div>')
    for _i, e in enumerate(sh):
        lbl = ('%s %s' % (e.get('title', 'character sheet'), ver(e))).strip()
        if _i == 0:
            b.append('<h2>Character sheet%s</h2>' % ('s' if len(sh) > 1 else ''))
        b.append('<div class=sheet><a href="../%s"><img src="../%s" alt=""></a>'
                 '<div class=meta><span class=fid>%s</span>%s%s'
                 '<p class=note>%s</p>%s</div></div>'
                 % (e['file'], small(e['file']), e.get('title', 'character sheet'),
                    ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                    tag(e.get('status', 'reference')),
                    e.get('note', 'note pending'), picks(lbl)))
    for e in overlays_of(n):
        b.append(overlay_block(e, '../'))
    for e in examples_of(n):
        b.append(example_block(e, '../'))
    b.append('<h2>Shots</h2>')
    if not sh_ids:
        b.append('<p class=lede>Nothing here yet.</p>')
    else:
        b.append('<p class=lede>%d %s. One picture stands for each shot. '
                 'Click it to open the shot and see every key frame in it, and to ask for a '
                 'breakdown or a change.</p>'
                 % (len(sh_ids), 'shot' if len(sh_ids) == 1 else 'shots'))
        for i in range(0, len(sh_ids), 5):
            b.append('<div class="row shot">')
            for sid in sh_ids[i:i + 5]:
                rep = representative(sid)
                ks = keyframes_of(sid)
                b.append('<div class=cell><a class=open href="%s">'
                         '<img src="../%s" alt="">'
                         '<div class=meta><span class=fid>shot %s</span>'
                         '<span class=kf>%d key frame%s</span>%s'
                         '<p class=note>%s</p>'
                         '<span class=bd>Open the shot &rarr;</span></div></a></div>'
                         % (shot_page(sid), small(rep['file'], 'tiny'), sid, len(ks),
                            '' if len(ks) == 1 else 's',
                            tag(rep.get('status', 'proposal')),
                            rep.get('note', 'note pending')))
            b.append('</div>')

    if fs:
        b.append('<h2>Loose frames</h2>')
        b.append('<p class=lede>Catalogued before the scene, shot and key frame structure '
                 'existed. Kept, not retired.</p>')
        for i in range(0, len(fs), 5):
            b.append('<div class=row>')
            for e in fs[i:i + 5]:
                lay = layers_of(e)
                bd = ('<a class=bd href="%s_breakdown.html">Breakdown &rarr;</a>'
                      % os.path.splitext(os.path.basename(e['file']))[0]) if lay else ''
                fid = e.get('frame', '')
                b.append('<div class=cell><a href="../%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s%s'
                         '<p class=note>%s</p>%s%s'
                         '</div></div>'
                         % (e['file'], small(e['file'], 'tiny'), fid,
                            ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                            tag(e.get('status', 'proposal')),
                            e.get('note', 'note pending'), bd,
                            picks(('%s %s' % (fid, ver(e))).strip())))
            b.append('</div>')
    b.append((TRAY % ('scene %s' % n, 'Scene %s' % n)).replace("EMAILADDR", EMAIL))
    open(os.path.join(ROOT, 'BB_C_%s' % n, 'index.html'), 'w').write(
        page('Scene %s' % n, ''.join(b), here=n, depth=1))

    for sid in shots_of(n):
        ks = keyframes_of(sid)
        rep = representative(sid)
        k = ['<p class=crumb><a href="index.html">scene %s</a> -&gt; shot %s -&gt; key frame</p>' % (n, sid),
             '<h1>Shot %s &nbsp;<span style="color:#8a8170;font-weight:400">%s</span></h1>'
             % (sid, SCENES[n]),
             rule_strip(n),
             '<div class=ask><b>This is where you ask for things.</b> Tick a key frame for a '
             'breakdown into background and foreground, or for a change, say what needs to change, '
             'and press the button at the bottom. Marko gets an email.</div>',
             '<p class=lede>%d key frame%s in this shot. The one marked <b>represents the shot</b> '
             'on the scene page.</p>' % (len(ks), '' if len(ks) == 1 else 's')]
        for i in range(0, len(ks), 5):
            k.append('<div class=row>')
            for e in ks[i:i + 5]:
                lay = layers_of(e)
                bd = ('<a class=bd href="%s_breakdown.html">Breakdown &rarr;</a>'
                      % os.path.splitext(os.path.basename(e['file']))[0]) if lay else ''
                lbl = ('%s %s' % (os.path.basename(e['file']), ver(e))).strip()
                k.append('<div class=cell><a href="../%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s%s%s'
                         '<p class=note>%s</p>%s%s</div></div>'
                         % (e['file'], small(e['file']), os.path.basename(e['file']),
                            ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                            '<span class=kf>represents the shot</span>' if e is rep else '',
                            tag(e.get('status', 'proposal')),
                            e.get('note', 'note pending'), bd, picks(lbl)))
            k.append('</div>')
        k.append('<p style="margin-top:30px"><a href="index.html">&larr; back to scene %s</a></p>' % n)
        k.append((TRAY % ('shot %s' % sid, 'Shot %s' % sid)).replace("EMAILADDR", EMAIL))
        open(os.path.join(ROOT, 'BB_C_%s' % n, shot_page(sid)), 'w').write(
            page('Shot %s' % sid, ''.join(k), here=n, depth=1))

    for e in fs:
        lay = layers_of(e)
        if not lay:
            continue
        base = os.path.splitext(os.path.basename(e['file']))[0]
        rows = ['<h1>%s &nbsp;<span style="color:#8a8170;font-weight:400">breakdown</span></h1>'
                % e.get('frame', base),
                '<div class=rules><b>Background</b> is the world with nobody in it. '
                '<b>Foreground</b> is the character, transparent, with a solid body. '
                '<b>Composite</b> is what it must look like when they are stacked.</div>']
        order = sorted(lay, key=lambda p: ('comp' not in p.lower(), 'bg' not in p.lower(), p))
        for p in order:
            rows.append('<div class=lay><a href="../%s"><img src="../%s" alt="" loading=lazy></a><div>'
                        '<div class=n>%s</div><div class=s>%s &nbsp;·&nbsp; %s</div>'
                        '<a href="../%s" download>Download</a></div></div>'
                        % (p, small(p), os.path.basename(p), dims(p), human(size_of(p)), p))
        rows.append('<p style="margin-top:30px"><a href="index.html">&larr; back to scene %s</a></p>' % n)
        open(os.path.join(ROOT, 'BB_C_%s' % n, base + '_breakdown.html'), 'w').write(
            page('%s breakdown' % e.get('frame', base), ''.join(rows), here=n, depth=1))

docs = [e for e in ENTRIES if e.get('kind') == 'document']
b = ['<h1>Documentation</h1>']
if not docs:
    b.append('<p class=lede>Nothing here yet.</p>')
for e in docs:
    tp = os.path.join('thumbs', os.path.splitext(os.path.basename(e['file']))[0] + '.jpg')
    thumb = ('<a href="%s"><img src="%s" alt=""></a>' % (e['file'], tp)
             if os.path.exists(os.path.join(ROOT, tp)) else '')
    b.append('<div class=doc>%s<div><div class=fid>%s</div>'
             '<div style="font:11px ui-monospace,monospace;color:#8a8170;margin:4px 0 8px">'
             '%s &nbsp;·&nbsp; %s</div><p class=note>%s</p>'
             '<p><a href="%s" download>Download</a></p></div></div>'
             % (thumb, os.path.basename(e['file']), human(size_of(e['file'])),
                e.get('date', ''), e.get('note', 'note pending'), e['file']))
if ARCHIVE.get('items'):
    a = ['<h1>Archive</h1>',
         '<p class=lede>Every PDF this production has ever made, %d of them. Nothing is deleted here, '
         'so superseded versions are kept and still open: an old cut is often the fastest way to see '
         'what changed. Files open from the film repository, they are not copied into this one.</p>'
         % len(ARCHIVE['items']),
         '<div class=arc>']
    last = None
    for it in ARCHIVE['items']:
        if it['group'] != last:
            a.append('<div class=arcg>%s</div>' % it['group'])
            last = it['group']
        a.append('<div class=arcr><a href="%s" target=_blank rel=noopener>%s</a>'
                 '<span class=d>%s</span><span class=z>%s MB</span></div>'
                 % (it['url'], it['name'], it.get('date', ''), it['mb']))
    a.append('</div>')
    open(os.path.join(ROOT, 'archive.html'), 'w').write(
        page('Archive', ''.join(a), here='archive', depth=0))

# ---------------------------------------------------------------- read through
# The whole film as a storyboard, built from catalog.json, so it is current the
# moment anything is filed. Phases with nothing drawn show empty frames, which is
# the point: it shows what is missing as clearly as what exists.
# phase number -> the scene folder its frames live in. The two do not match any
# more: the film was reordered on 31.8.2026 and the folders kept their names, so
# this table is the only place the mapping lives.
# A phase can draw on several scene folders now: the house gathers its exterior,
# its front door, the rooms and the threshold, and the theories gather both
# boards. The folders kept their old numbers, so the catalogue carries the map.
def scenes_of(e):
    v = e.get('scenes') or ([e['scene']] if e.get('scene') else [])
    return [str(x) for x in v]
# The storyboard shows ONE version per shot where a shot has both a generated
# placeholder and a real footage composite. Baba's rule, 30.8.2026: the generated
# boy stands in on the front page because it reads finished at a glance, and the
# real footage lives on the scene and breakdown pages where the work is done.
_kf = [e for e in ENTRIES if e.get('kind') == 'keyframe'
       and e.get('status') != 'superseded'
       and not e.get('storyboard') == 'hide']
_kf.sort(key=lambda e: shot_key(e.get('shot', '0')))
_byscene = {}
for e in _kf:
    _byscene.setdefault(str(e['shot']).split('.')[0], []).append(e)

_fl = flow_of()
_done = sum(len(v) for v in _byscene.values())
# the last shot, laid out as the sequence it is: four drawn frames, a cut, and
# three live ones. The two hands never share a frame, which is the whole point.
CREDITS_TEXT = '''THE BRAIN BRAKE
The Central Governor Theory


PRESENTED BY
Manan Periwal


CINEMATOGRAPHER
Aurovenkatesh


CREW
Jagan
Pushparaj


ANIMATION
Kristijan Kauric
Studio Brojke, Croatia


DIRECTED, EDITED AND SOUND BY
Marko Bosko
Mantra Productions


Breakthrough Junior Challenge
2026'''


CLIP_SOURCE = {
    'clips/key-catch-loop.mp4':
        'https://drive.google.com/drive/folders/1YGb_z7OCrLSUX7JagNpynXbu1fAK2wNu',
    'clips/in-front-of-door-loop.mp4':
        'https://drive.google.com/drive/folders/1ph36NxPciUB5Y4s_IiowDotmjk2ciFZ4',
}


LASTSHOT = [
    ('BB_C_15/15-2-A-v1.png', 'opening'),
    ('BB_C_15/15-3-A-v1.png', 'turns over'),
    ('BB_C_15/15-4-A-v1.png', 'the key alone'),
    (None, 'CUT'),
    (('mp4', 'clips/key-catch-loop.mp4'), 'the catch, moving'),
]


ARRIVAL = [
    ('BB_C_16/live/16-1-MOCKUP-v1.png', 'he is at the door'),
    (('mp4', 'clips/in-front-of-door-loop.mp4'), 'in front of the door'),
    ('BB_C_16/16-1-A-v1.png', 'the door open'),
    ('BB_C_16/16-0-A-v1.png', 'the door shut'),
]


def strip(items, lede, prefix=''):
    out = ['<p class=lede>%s</p>' % lede, '<div class=seqstrip>']
    for f, label in items:
        if f is None:
            out.append('<div class=cut>&rarr;</div>')
            continue
        if isinstance(f, tuple) and f[0] == 'mp4':
            # a native loop. A YouTube embed lays a title card and a watermark
            # over the picture, which is unreadable at thumbnail size, so these
            # are served straight from the repository instead.
            # tapping the loop opens it full screen. The ProRes with alpha is a
            # separate link, because that is what gets composited, not this.
            drive = CLIP_SOURCE.get(f[1], '')
            dl = ('<a class=pr href="%s" target=_blank rel=noopener '
                  'onclick="event.stopPropagation()">PRORES &nearr;</a>' % drive) if drive else ''
            out.append('<div class=f><div class=vid onclick="var v=this.firstElementChild;'
                       '(v.requestFullscreen||v.webkitEnterFullscreen||v.webkitRequestFullscreen)'
                       '.call(v);v.controls=true;">'
                       '<video src="%s%s" autoplay muted loop playsinline preload=metadata '
                       'disablepictureinpicture></video>'
                       '<span class=lbl>LOOP</span></div>'
                       '<div class=n>%s%s</div></div>'
                       % (prefix, f[1], label.upper(), dl))
            continue
        if isinstance(f, tuple) and f[0] == 'yt':
            vid = f[1]
            out.append('<div class=f><div class=vid>'
                       '<iframe src="https://www.youtube-nocookie.com/embed/%s'
                       '?autoplay=1&mute=1&loop=1&playlist=%s&controls=0&modestbranding=1'
                       '&playsinline=1&rel=0&disablekb=1" '
                       'title="%s" frameborder=0 allow="autoplay" tabindex=-1></iframe>'
                       '<span class=lbl>LOOP</span></div><div class=n>%s</div></div>'
                       % (vid, vid, label, label.upper()))
            continue
        if not os.path.exists(os.path.join(ROOT, f)):
            continue
        out.append('<div class=f><a href="%s%s"><img src="%s%s" alt="" loading=lazy></a>'
                   '<div class=n>%s</div></div>'
                   % (prefix, f, prefix, small(f, 'tiny'), label.upper()))
    out.append('</div>')
    return ''.join(out)


def arrival_strip(prefix=''):
    return strip(ARRIVAL,
                 'He arrives out of the white and the door is already giving off light. One '
                 'continuous pull back from here: as the camera draws away he goes inside, and by '
                 'the time we see the whole building the door is shut. He is keyed into the doorway '
                 'and taken out of the composite part way through, so he is never drawn.', prefix)


def lastshot_strip(prefix=''):
    return strip(LASTSHOT,
                 'Coach Brain lets the key go, it falls through an empty frame, and we cut. '
                 'His hand and Manan\u2019s are never on screen together, so nothing is composited '
                 'and the lighting difference between the drawing and the footage does not matter. '
                 'The first three are drawn. The catch is the live clip, looping here as it will cut.', prefix)


_titlecard = 'BB_C_0/0-0-TITLE-v1.png'
_mast = ''
if os.path.exists(os.path.join(ROOT, _titlecard)):
    _mast = ('<div class=mast><a href="card/0-0-TITLE-v1.html">'
             '<img src="%s" alt="%s, %s"></a>'
             '<div class=sub>%s &nbsp;&middot;&nbsp; %s</div></div>'
             % (small(_titlecard), FILM, SUBTITLE, SUBTITLE, EVENT))
_flight = ('<div class=flight><b>How the first half arrives</b><p>%s</p></div>'
           % CAT.get('rubbing_note', '')) if CAT.get('rubbing_note') else ''
_flight += ('<div class=flight><b>How the second half moves</b><p>%s</p></div>'
            % CAT.get('flight_note', '')) if CAT.get('flight_note') else ''
rt = [_mast, '<h1>THE BRAIN BRAKE ANIMATIC</h1>', _flight,
      '<p class=lede>The whole film as a storyboard, in order. <b>%d frames drawn so far.</b> '
      'Empty frames are phases that have not been drawn yet, and they are shown on purpose so the '
      'gaps are as visible as the work. This page is built from the catalogue, so it is current the '
      'moment anything is filed. Everything we have collected for each phase, kept and abandoned, '
      'is on <a href="brainstorm.html">brainstorm</a>.</p>' % _done,
      '<p class=lede><a class=rt href="#">Download the PDF &darr;</a> &nbsp;'
      '<span style="color:var(--dim);font-size:12px">PDF coming, this page is the live one</span></p>',
      '<div class=rtsheet>']
for e in _fl:
    n = str(e.get('n', ''))
    frames = []
    for sc in scenes_of(e):
        frames.extend(_byscene.get(sc, []))
    frames.sort(key=lambda f: shot_key(f.get('shot', '0')))
    live = n in ('2', '4', '5')
    # phases 8 and 11 both draw on scene 6, so its frames are split between them:
    # the corridor and the rooms are the journey, the control room is Coach Brain.
    # every shot number is unique again as of 31.8.2026, so no phase needs to
    # filter another phase's frames out of a shared folder
    # a phase whose frames are all photographs says so: calling footage "drawn"
    # was misleading on the one phase that was shot rather than drawn
    # the label says what the frames actually are. Calling a reference still
    # "drawn" hides that a phase is still waiting for its real material.
    shot = [f for f in frames if '/live/' in f.get('file', '')]
    ref  = [f for f in frames if f.get('status') == 'placeholder']
    drawn = [f for f in frames if f not in shot and f not in ref]
    bits = []
    if drawn: bits.append('%d drawn' % len(drawn))
    if shot:  bits.append('%d shot' % len(shot))
    if ref:   bits.append('%d reference' % len(ref))
    st = ', '.join(bits) if bits else ('LIVE ACTION' if live else 'NOT DRAWN YET')
    rt.append('<div class=rtph><span class=n>%s</span><h3>%s</h3><span class=st>%s</span></div>'
              % (n, e.get('title', ''), st))
    # the last shot is phase 15, so its sequence belongs here in the flow rather
    # than at the foot of the page
    # a frame shown in a strip is not listed again in the grid below it, but the
    # rest of the phase still is. Suppressing the whole grid hid the rooms of the
    # house and printed EMPTY boxes over them.
    in_strip = set()
    if n == '7':
        rt.append(arrival_strip())
        in_strip = {f for f, _ in ARRIVAL if isinstance(f, str)}
    if n == '11':
        # Baba, 31.8.2026: this phase shows the strip and nothing else. The other
        # live stills and drawn attempts are still on their card pages.
        rt.append(lastshot_strip())
        frames = []
    if in_strip:
        frames = [f for f in frames if f['file'] not in in_strip]
    if frames:
        rt.append('<div class=tiny>')
        for f in frames:
            b = os.path.basename(f['file']).rsplit('.', 1)[0].replace(' ', '_')
            ln = ''
            if f.get('line'):
                ln = ('<div class=ln><span class=sp>%s</span>'
                      '<span class=tx>“%s”</span>'
                      '<span class=rec>%s</span></div>'
                      % (f.get('speaker', ''), f['line'], f.get('linestate', '').upper()))
            rt.append('<a href="card/%s.html"><img src="tiny/%s.jpg" alt="" loading=lazy>'
                      '<div class=c>%s</div>%s</a>' % (b, b, b, ln))
        rt.append('</div>')
    elif not (n == '11'):
        rt.append('<div class=tiny>')
        for i in range(6):
            rt.append('<a><div class="box empty" style="aspect-ratio:16/9;border:1px dashed '
                      'var(--rule);background:#0b0a08"></div><div class=c>%s</div></a>'
                      % ('FOOTAGE' if live else 'EMPTY'))
        rt.append('</div>')
rt.append('</div>')
# ---------------------------------------------------------------- assets
# Everything ever made for this film, including what was abandoned. Nothing is
# thrown away: a rejected frame is a decision with a reason attached, and the
# reason is usually worth more than the frame. Images only, because a PDF has no
# small version and would be loaded at full size as if it were a thumbnail.
_as = ['<h1>ASSETS</h1>']
# the key as a 3D model, one mesh with two materials so it can cross from drawn
# to real without a vertex moving
if os.path.exists(os.path.join(ROOT, 'assets3d', 'brain_break_key.obj')):
    _as.append(
        '<div class=srcbox><div class=t><b>The key in 3D, for Blender</b>'
        '<span><a class=dl href="assets3d/brain_break_key_blender.py" download>SCRIPT</a>&nbsp;'
        '<a class=dl href="assets3d/brain_break_key.obj" download>OBJ</a>&nbsp;'
        '<a class=dl href="assets3d/brain_break_key_source.py" download>SOURCE</a></span></div>'
        '<img src="%s" alt="" style="width:100%%;max-width:900px;display:block;margin:12px 0 8px;'
        'border:1px solid var(--rule)">'
        '<p>The real key modelled from the photographs: 110 mm long, 26 mm head, clover hole cut '
        'clean through, three ring collar, three teeth. Watertight, 694 vertices, exported in '
        'metres so it lands at the right scale.</p>'
        '<p><b>Put both files in one folder, open Blender, Scripting tab, open the script, press '
        'Run.</b> You get one mesh with two materials on it: slot 0 <b>KEY_REAL</b>, polished '
        'brass, and slot 1 <b>KEY_DRAWN</b>, flat cream with no specular. The mesh never changes, '
        'only the surface, so the key crosses from the drawn world to the real one without a vertex '
        'moving. Keyframe the material index across the fall.</p>'
        '<p style="color:var(--dim)">The origin is at the centre of volume, so it tumbles about '
        'itself in a rigid body sim rather than swinging around a corner. The third file is the '
        'source that generated the mesh: every dimension is a named constant at the top if you want '
        'to change proportions.</p></div>'
        % small('reference/OBJECT_SHEET_KEY-v2.png'))

# the film's own lettering as an installable font, built from a specimen sheet
# drawn in the same hand. See MANTRA_MANIFEST/modules/font-from-drawing.md.
if os.path.exists(os.path.join(ROOT, 'font', 'brain_break.ttf')):
    _as.append(
        '<div class=srcbox><div class=t><b>Brain Brake, the film\u2019s own font</b>'
        '<span><a class=dl href="font/brain_break.ttf" download>TTF</a>&nbsp;'
        '<a class=dl href="font/brain_break.otf" download>OTF</a></span></div>'
        '<img src="%s" alt="" style="width:100%%;max-width:900px;display:block;margin:12px 0 8px;'
        'border:1px solid var(--rule)">'
        '<p>The hand lettering of the film, traced from a specimen sheet and built into a font so '
        'a line can be typed instead of drawn. 41 glyphs: A to Z, 0 to 9, and full stop, comma, '
        'colon, apostrophe and hyphen. Double click to install on macOS or Windows; it appears as '
        '<b>Brain Brake</b>.</p>'
        '<p style="color:var(--dim)">No kerning, so tight pairs like AV or TA may want manual '
        'tracking. Every letter is identical each time it repeats, which real handwriting is not: '
        'for a title that has to look truly hand drawn, draw it rather than set it.</p></div>'
        % small('DOCS/FONT_SPECIMEN.png'))
_as += [
       '<p class=lede>Every image ever made for this film, live and retired. Nothing here is '
       'deleted. A frame that was rejected carries the reason it was rejected, which is usually '
       'worth more than the frame. Click any of them for the full note and a download. Faded ones '
       'are superseded.</p>']
_groups = [
    ('In the film', lambda e: e.get('kind') == 'keyframe' and e.get('status') != 'superseded'),
    ('Superseded and rejected', lambda e: e.get('status') == 'superseded'),
    ('Sheets and references', lambda e: e.get('kind') in ('sheet', 'overlay', 'symbol', 'example',
                                                          'rate', 'style', 'document')
        and e.get('status') != 'superseded'),
]
for _title, _pred in _groups:
    _items = [e for e in ENTRIES if _pred(e) and e.get('file')
              and os.path.splitext(e['file'])[1].lower() in ('.png', '.jpg', '.jpeg')
              and os.path.exists(os.path.join(ROOT, e['file']))]
    if not _items:
        continue
    _items.sort(key=lambda e: e['file'])
    _as.append('<h2>%s <span style="color:var(--dim);font-weight:400">%d</span></h2>'
               % (_title, len(_items)))
    _as.append('<div class=asset>')
    for e in _items:
        b = os.path.basename(e['file']).rsplit('.', 1)[0].replace(' ', '_')
        cls = ' class=sup' if e.get('status') == 'superseded' else ''
        card = os.path.join(ROOT, 'card', b + '.html')
        href = ('card/%s.html' % b) if os.path.exists(card) else e['file']
        _as.append('<a href="%s"%s><img src="%s" alt="" loading=lazy>'
                   '<div class=c>%s</div></a>' % (href, cls, small(e['file'], 'tiny'), b))
    _as.append('</div>')
open(os.path.join(ROOT, 'assets.html'), 'w').write(
    page('Assets', ''.join(_as), here='assets', depth=0))

# ---------------------------------------------------------------- footage
# One page listing every export, what is in it and which phase it belongs to.
# The site has many levels now and this is the way out of the forest.
_fo = ['<h1>FOOTAGE</h1>',
       '<p class=lede>Every piece of live material, where it lives and what it is for. '
       'Everything here is ProRes 4444 with an alpha channel unless it says otherwise, and it all '
       'lives on Google Drive rather than in this repository. Download from Drive and composite '
       'from that, never from the stills on this site: those are previews.</p>']
for _f in (CAT.get('footage') or []):
    _fo.append('<div class=srcbox><div class=t><b>%s</b>'
               '<a class=dl href="%s" target=_blank rel=noopener>OPEN ON DRIVE &nearr;</a></div>'
               '<p><b>%s</b>%s</p><p>%s</p><p style="color:var(--dim)">%s</p></div>'
               % (_f['name'], _f['url'],
                  ('Phase %s, %s. ' % (_f['phase'], _f['phase_title'])) if _f.get('phase')
                  else (_f.get('phase_title', '') + '. '),
                  _f.get('codec', ''), _f.get('what', ''), _f.get('use', '')))
open(os.path.join(ROOT, 'footage.html'), 'w').write(
    page('Footage', ''.join(_fo), here='footage', depth=0))

open(os.path.join(ROOT, 'index.html'), 'w').write(
    page('%s, %s' % (FILM.title(), SUBTITLE), ''.join(rt), here='home', depth=0))

# ------------------------------------------------------------- the card pages
# One page per frame. A medium image, never the full one, the code on the left
# and a download on the right, the layers if there are any, and what the frame
# is doing. The full file is only ever reached by pressing download.
os.makedirs(os.path.join(ROOT, 'card'), exist_ok=True)
_order = [e for e in _kf]
for _i, e in enumerate(_order):
    b = os.path.basename(e['file']).rsplit('.', 1)[0].replace(' ', '_')
    # STEP 80. A frame whose original lives on Drive carries `full` and
    # `full_bytes` on its catalogue entry: the watch folder daemon writes both
    # when it uploads. The button goes to Drive and the size comes from the
    # catalogue, because there is no local file left to weigh. A frame with no
    # `full` behaves exactly as before, and a missing local file no longer
    # crashes the build, it just says 0.0 MB until someone looks.
    # Three places the original might be, in order of trust. The entry itself,
    # which the daemon fills in once a catalogue entry exists. Then
    # drive_links.json, which the daemon writes the moment a frame arrives,
    # before anybody has written an entry for it. Then the local file, for
    # everything not yet migrated.
    _dv = DRIVE.get(os.path.basename(e['file']))
    if e.get('full'):
        _href = e['full']
        mb = e.get('full_bytes', 0) / 1048576.0
    elif _dv:
        _href = _dv if isinstance(_dv, str) else _dv.get('url', '')
        mb = (_dv.get('bytes', 0) / 1048576.0) if isinstance(_dv, dict) else 0.0
    else:
        _href = '../' + e['file']
        _p = os.path.join(ROOT, e['file'])
        mb = (os.path.getsize(_p) if os.path.exists(_p) else 0) / 1048576.0
    cd = ['<div class=cardhead><span class=code>%s</span>'
          '<a class=dl href="%s" download>DOWNLOAD FULL SIZE &nbsp;%.1f MB</a></div>'
          % (b.upper(), _href, mb)]
    cd.append('<img class=cardimg src="../mid/%s.jpg" alt="">' % b)
    if e.get('slug'):
        cd.append('<div class=slug>%s</div>' % e['slug'])
    if e.get('what'):
        cd.append('<p class=note>%s</p>' % e['what'])
    if e.get('why'):
        cd.append('<p class=note>%s</p>' % e['why'])
    cd.append('<p class=note style="color:var(--dim)">%s</p>' % e.get('note', ''))

    # the credits text lives here, one level down, not in the flow. See
    # modules/design-language.md: a flow view stays pictures and words.
    if str(e.get('shot', '')).startswith('14.'):
        cd.append(
            '<div class=creds><div class=hd><b>The credits as text</b>'
            '<button class=dl onclick="var t=this.parentNode.nextElementSibling;'
            't.select();document.execCommand(\'copy\');this.textContent=\'COPIED\';">'
            'COPY</button></div>'
            '<textarea readonly spellcheck=false>%s</textarea>'
            '<span class=warn>PLACEHOLDER. ONLY AUROVENKATESH, JAGAN AND PUSHPARAJ ARE CONFIRMED. '
            'EVERYTHING ELSE IS WAITING ON NEHA AND MUST NOT BE USED AS IS.</span></div>'
            % CREDITS_TEXT)

    for src in (e.get('source') or []):
        cd.append('<div class=srcbox><div class=t><b>%s</b>'
                  '<a class=dl href="%s" target=_blank rel=noopener>OPEN ON DRIVE &nearr;</a></div>'
                  '<p>%s</p></div>'
                  % (src.get('name', 'source footage'), src['url'], src.get('note', '')))

    for a in (e.get('audio') or []):
        amb = os.path.getsize(os.path.join(ROOT, a['file'])) / 1048576.0
        cd.append('<div class=aud><div class=t><b>%s</b>'
                  '<span>%.1f s &nbsp;&middot;&nbsp; '
                  '<a class=dl href="../%s" download title="download the wav">&darr; %.1f MB</a>'
                  '</span></div>'
                  '<audio controls preload=none src="../%s"></audio></div>'
                  % (a.get('name', 'reference voice'), a.get('secs', 0), a['file'], amb, a['file']))

    lay = e.get('layers') or []
    if lay:
        cd.append('<h2>The layers</h2>')
        cd.append('<p class=lede>Each one downloads on its own. This is what goes on top of what.</p>')
        cd.append('<div class=lay>')
        for L in lay:
            lb = os.path.basename(L['file']).rsplit('.', 1)[0].replace(' ', '_')
            lmb = os.path.getsize(os.path.join(ROOT, L['file'])) / 1048576.0
            cd.append('<div class=l><img src="../mid/%s.jpg" alt="">'
                      '<div class=n><span>%s</span>'
                      '<a class=dl href="../%s" download>DOWNLOAD %.1f MB</a></div></div>'
                      % (lb, L.get('name', lb).upper(), L['file'], lmb))
        cd.append('</div>')

    nav = []
    if _i > 0:
        pb = os.path.basename(_order[_i-1]['file']).rsplit('.', 1)[0].replace(' ', '_')
        nav.append('<a href="%s.html">&larr; %s</a>' % (pb, pb))
    nav.append('<a href="../index.html">all frames</a>')
    if _i < len(_order) - 1:
        nb = os.path.basename(_order[_i+1]['file']).rsplit('.', 1)[0].replace(' ', '_')
        nav.append('<a href="%s.html">%s &rarr;</a>' % (nb, nb))
    cd.append('<p class=lede style="margin-top:26px">%s</p>' % ' &nbsp;&middot;&nbsp; '.join(nav))
    open(os.path.join(ROOT, 'card', b + '.html'), 'w').write(
        page(b, ''.join(cd), here='home', depth=1))
print('  %d card pages' % len(_order))

open(os.path.join(ROOT, 'documentation.html'), 'w').write(
    page('Documentation', ''.join(b), here='doc', depth=0))

b = ['<h1>THE BRAIN BRAKE</h1>',
     ('<p class=vdraft><b>%s.</b> Scene 1 is being rebuilt from scratch and everything on this site '
      'is part of that draft. The V7 artwork is <b>not gone</b>: it is stored, it is still what the '
      'film is cut from, and any of it can be pulled back and modified rather than drawn again. If an '
      'older picture is better, we go back to it. Nothing here is in the film until Marko says so.</p>'
      % VERSION) if VERSION else '',
     '<p class=lede>A two minute film for the Breakthrough Junior Challenge. A fourteen year old '
     'asks why a runner with nothing left can still find one more sprint. Everything here is for '
     'the animation.</p>',
     '<div class=rules><b>The artwork runs edge to edge and has no panel border.</b> '
     'The frame is yours to add as its own layer, so it can move, animate or come off.<br>'
     'Everything is <b>2731 x 1536</b>, true 16:9. Key light is <b>camera right</b>, always.<br>'
     'Nothing here is in the film until Marko says so. The status under each picture says where it '
     'stands.<br>Video files are on <b>GDrive</b>, top right of every page.</div>',
     '<h2>Scenes</h2><ul class=scenes>']
for e in overlays_of():
    b.insert(2, overlay_block(e, ''))
for e in examples_of():
    b.append(example_block(e, ''))
for n in sorted(SCENES, key=int):
    c = len(frames_of(n))
    b.append('<li><a href="BB_C_%s/index.html"><span class=n>SC%s</span>'
             '<span class=t>%s</span><span class=c>%s</span></a></li>'
             % (n, n, SCENES[n], '%d frames' % c if c else 'nothing yet'))
b.append('</ul><h2>What changed</h2><div class=log>')
for e in sorted(ENTRIES, key=lambda x: x.get('date', ''), reverse=True):
    # an entry does not always have a single 'file': an example has a plate, a
    # layer and a composite. Do not assume the shape of an entry here.
    who = (e.get('frame') or e.get('shot') or e.get('title')
           or (os.path.basename(e['file']) if e.get('file') else e.get('kind', '?')))
    # show the picture, not only the words about it. A symbol row with no crop in
    # it is asking the reader to imagine the thing the row exists to point at.
    f, _ph = resolve(e) if e.get('file') or e.get('prefer') else ('', False)
    if not f:
        f = e.get('composite') or e.get('layer') or e.get('plate') or ''
    thumb = ''
    if f and os.path.splitext(f)[1].lower() in ('.png', '.jpg', '.jpeg', '.webp') \
            and os.path.exists(os.path.join(ROOT, f)):
        thumb = '<a class=ith href="%s"><img src="%s" alt=""></a>' % (f, small(f, 'tiny'))
    b.append('<div class="it%s">%s<div class=itx><span class=fid>%s</span>%s%s'
             '<div class=d>%s</div><p class=note>%s</p></div></div>'
             % (' hasimg' if thumb else '', thumb, who,
                ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                tag(e.get('status', 'proposal')), e.get('date', ''),
                e.get('note', 'note pending')))
b.append('</div>')
ra = rates_of()
if ra:
    b.append('<h2>The frame rate is the second language</h2>')
    b.append('<p class=lede>Nothing in this film runs smooth except one thing. The animation is '
             'stepped, and <b>how heavily it is stepped is what the shot is saying</b>. The rate '
             'rises as the brake comes off, and the audience feels it in the body without being '
             'told. Never smooth between tiers inside a shot: the tiers are steps and the cut is '
             'where they change.</p>')
    b.append('<div class=rates>')
    for e in ra:
        b.append('<div class=rt><div class=fps>%s<small>frames / sec</small></div>'
                 '<div class=bar><i style="width:%s%%"></i></div>'
                 '<div><h4>%s</h4><p>%s</p></div></div>'
                 % (e.get('fps', ''), e.get('pct', '10'), e.get('title', ''), e.get('note', '')))
    b.append('</div>')

sy = symbols_of()
if sy:
    b.append('<h2>Glossary of symbols</h2>')
    b.append('<p class=lede>The film says most of what it means through objects. These are the ones '
             'that carry weight, what each one stands for, and where it appears. A symbol that comes '
             'back is doing work the second time too.</p>')
    b.append('<div class=sym>')
    for e in sy:
        f, ph = resolve(e)
        note = e.get('note', '')
        if ph:
            note += ('<br><span style="color:#c48a52">Placeholder. It swaps itself for the real '
                     'drawing the moment one lands in the repository.</span>')
        b.append('<div class=s><a href="%s"><img src="%s" alt=""></a>'
                 '<div><h4>%s</h4><p>%s</p></div></div>'
                 % (f, small(f), e.get('title', ''), note))
    b.append('</div>')

if overlays_of():
    b.append((TRAY % ('the frame', 'The frame')).replace("EMAILADDR", EMAIL).replace('../marko.png', 'marko.png'))
# everything above became the BREAKDOWN page. The homepage is now the flow.
open(os.path.join(ROOT, 'breakdown.html'), 'w').write(
    page('Breakdown', ''.join(b), here='breakdown', depth=0))

fl = flow_of()
h = ['<h1>THE BRAIN BRAKE</h1>',
     ('<p class=vdraft><b>%s.</b> The film in twelve phases, in order. Under each one is '
      'everything we have that belongs to it, drawn and shot, kept and abandoned. It is a '
      'brainstorming board, not a selection: nothing here is chosen yet. Only phase 1 is '
      'locked.</p>' % VERSION) if VERSION else '',
     '<p class=lede>A two minute film for the Breakthrough Junior Challenge. A fourteen year old '
     'asks why a runner with nothing left can still find one more sprint.</p>',
     '<div class=flow>']
for e in fl:
    key = os.path.splitext(os.path.basename(e['file']))[0]
    pics = BOARD.get(key, [])
    badge = ('<a class=lk href="BB_C_%s/index.html">LOCKED &nbsp;OPEN SCENE %s &rarr;</a>'
             % (e['scene'], e['scene'])) if e.get('status') == 'LOCKED' \
        else '<span class=ph>NOT DRAWN YET</span>'
    h.append('<div class=fp><div class=hd><span class=num>%s</span><h3>%s</h3>%s</div>'
             '<p class=why>%s</p>' % (e.get('n', ''), e.get('title', ''), badge, e.get('note', '')))
    if pics:
        h.append('<div class=board>')
        for f in pics:
            h.append('<a href="%s"><img src="%s" alt="" loading=lazy></a>' % (f, small(f, 'tiny')))
        h.append('</div>')
        h.append('<div class=cnt>%d PICTURES ON THIS PHASE &nbsp;·&nbsp; '
                 'EVERYTHING WE HAVE, DRAWN AND SHOT, GOOD AND ABANDONED</div>' % len(pics))
    for st in style_for(e.get('n', '')):
        h.append('<div class=sref><h4>%s</h4><p>%s</p><div class=vids>'
                 % (st.get('title', ''), st.get('note', '')))
        for v in st.get('videos', []):
            h.append('<div class=vid><iframe src="https://www.youtube-nocookie.com/embed/%s" '
                     'title="%s" loading=lazy allowfullscreen '
                     'referrerpolicy="strict-origin-when-cross-origin"></iframe>'
                     '<span>%s <a class=play href="https://www.youtube.com/watch?v=%s" '
                     'target=_blank rel=noopener>PLAY &nearr;</a></span></div>'
                     % (v['id'], v['title'], v['title'], v['id']))
        h.append('</div></div>')
    h.append('</div>')
h.append('</div>')
h.append('<p class=lede>The sheets, the frame, the layer rules, the frame rate scale, the glossary '
         'and the full change log are on the <a href="breakdown.html">breakdown</a> page.</p>')
open(os.path.join(ROOT, 'brainstorm.html'), 'w').write(
    page('Brainstorm', ''.join(h), here='brainstorm', depth=0))

# ---------------------------------------------------------------- the check
# A build that produces invisible pages is worse than a build that fails, because
# it looks like it worked. On 28.8.2026 the gate was switched off and every page
# went blank in the middle of a production day. Never again: prove the pages are
# visible before saying the build is done.
import glob as _g
_bad = []
for _f in _g.glob(os.path.join(ROOT, '*.html')) + _g.glob(os.path.join(ROOT, 'BB_C_*', '*.html')):
    _h = open(_f).read()
    _vis = re.search(r'<div id=app style="display:(\w+)"', _h)
    _has_gate = 'class=gate' in _h
    if not _vis:
        _bad.append((_f, 'no app wrapper'))
    elif _vis.group(1) == 'none' and not _has_gate:
        _bad.append((_f, 'hidden with no gate to open it'))
    elif len(_h) < 2000:
        _bad.append((_f, 'suspiciously small, %d bytes' % len(_h)))
if _bad:
    for _f, _why in _bad:
        print('  BLANK PAGE: %s  %s' % (os.path.relpath(_f, ROOT), _why))
    raise SystemExit('BUILD REFUSED: %d page(s) would render blank' % len(_bad))

print('built: landing, documentation, %d scene pages, all visible' % len(SCENES))
