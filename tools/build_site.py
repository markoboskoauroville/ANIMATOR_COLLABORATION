#!/usr/bin/env python3
"""Build the animator site from catalog.json.

catalog.json is the only truth. Nothing on any page is written by hand, so
nothing can drift from what is actually in the repo.

    python3 tools/build_site.py

Pages: the landing page, one per scene, one breakdown per frame that has
layers, and the documentation page. Every page carries the bar and the gate.
No zips anywhere: Kristijan downloads what he needs, one file at a time.
"""
import json, os, re, glob, html, urllib.parse

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
    # 3.9.2026: audio moved to BRAINBREAK_AUDIO and its catalogue paths became
    # absolute URLs, which os.path.join happily turned into a nonsense local
    # path and then tried to measure. A remote file has no size we can read
    # here, and saying zero is honest rather than crashing the build.
    if str(rel).startswith(('http://', 'https://')):
        return 0
    p = os.path.join(ROOT, rel)
    return os.path.getsize(p) if os.path.exists(p) else 0


def dims(rel):
    if str(rel).startswith(('http://', 'https://')):
        return ''
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
.deck{background:var(--bg);border:1px solid var(--rule);border-radius:8px;
  padding:9px 11px;margin:0 0 8px}
.deck.is-playing{border-color:var(--gold)}
.deckh{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
.deckn{font:400 10.5px/1 ui-monospace,monospace;color:var(--dim)}
.wave{position:relative;height:40px;background:var(--panel);border:1px solid var(--rule);
  border-radius:3px;display:flex;align-items:flex-end;gap:1px;padding:3px;overflow:hidden}
.wave span{flex:1 1 0;background:#6B4E1E;border-radius:1px 1px 0 0;min-width:0;
  transition:background .05s linear}
.wave span.played{background:#F7D488}
.cursor{position:absolute;top:0;bottom:0;width:1px;background:var(--gold);left:0;
  pointer-events:none}
.deckf{display:flex;align-items:center;gap:10px;margin-top:6px}
/* 3.9.2026. The button was a 13px dark glyph on gold, which on a phone in
   sunlight reads as nothing at all. Baba could not find it. It is bigger now
   and the glyph is WHITE, which holds against both the gold and the glare, and
   it gets a ring when it is playing so the deck that is running is obvious
   from across the room. */
.pbtn{background:var(--gold);border:0;border-radius:999px;width:42px;height:42px;
  cursor:pointer;display:flex;align-items:center;justify-content:center;flex:none;padding:0;
  box-shadow:0 1px 0 rgba(0,0,0,.35)}
.pbtn svg{width:17px;height:17px;fill:#fff;display:block}
.pbtn.on{box-shadow:0 0 0 3px rgba(232,166,75,.35)}
.deck.is-playing .wave{border-color:var(--gold)}
.tc{font:400 11px/1 ui-monospace,monospace;color:var(--dim)}
.tc.rem{margin-left:auto}
/* ONE DECK, PLAYLIST UNDER IT. Modelled on Baba's own NOVA_TV_777 player and on
   Winamp: transport at the top, a waveform that fills as it plays, the list
   below. Forty three separate players was the wrong shape, because only one
   thing plays at a time. The VU meter is deliberately absent: he asked for the
   waveform and the controls, and a meter on a review page is decoration. */
.nova{margin:16px 0 6px;background:#0F0E0C;border:1px solid var(--rule);border-radius:10px;
  overflow:hidden}
.novatc{display:flex;justify-content:space-between;padding:11px 15px;
  font:400 15px/1 ui-monospace,monospace;color:var(--gold);border-bottom:1px solid var(--rule)}
.novatc span:last-child{color:var(--dim)}
.novah{display:flex;align-items:center;justify-content:space-between;gap:14px;
  padding:14px 15px;background:#171310;border-bottom:1px solid var(--rule)}
.novah b{display:block;font:700 15px/1.25 Inter,system-ui,sans-serif;color:var(--gold);
  letter-spacing:.01em}
.novah span{display:block;font:400 12.5px/1.45 Inter,system-ui,sans-serif;color:var(--dim);
  margin-top:3px}
.mcbtn{background:#1A1A1D;border:1px solid var(--rule);border-radius:3px;color:var(--ink);
  cursor:pointer;width:40px;height:34px;display:inline-flex;align-items:center;
  justify-content:center;flex:0 0 auto;padding:0;text-decoration:none}
.mcbtn svg{width:15px;height:15px;fill:currentColor;display:block}
.mcbtn.wide{width:auto;padding:0 12px;font:600 10px/1 ui-monospace,monospace;
  letter-spacing:.12em;color:var(--gold)}
.mcbtn.play{width:78px;height:46px;background:var(--gold);border-color:var(--gold);flex:none}
.mcbtn.play svg{width:20px;height:20px;fill:#fff}
.novascrub{padding:12px 15px;background:#0B0A09}
.wave{position:relative;height:52px;width:100%;background:#131110;
  border:1px solid var(--rule);border-radius:3px;display:flex;align-items:flex-end;
  gap:1px;padding:4px 3px;overflow:hidden}
.wave span{flex:1 1 0;background:#6B4E1E;border-radius:1px 1px 0 0;min-width:0;
  transition:background .05s linear}
.wave span.played{background:#F7D488}
.cursor{position:absolute;top:0;bottom:0;width:1px;background:#FFE7B0;left:0;pointer-events:none}
.novabar{display:flex;align-items:center;gap:8px;padding:11px 15px;flex-wrap:wrap;
  border-top:1px solid var(--rule)}
.novastate{margin-left:auto;font:400 11px/1 ui-monospace,monospace;letter-spacing:.14em;
  color:var(--dim)}
.novapl{border-top:1px solid var(--rule)}
.novaplh{display:flex;align-items:center;gap:10px;cursor:pointer;list-style:none;
  padding:12px 15px;font:600 10.5px/1 ui-monospace,monospace;letter-spacing:.16em;
  color:var(--dim)}
.novaplh::-webkit-details-marker{display:none}
.novaplh:after{content:'>';margin-left:auto;color:var(--gold);transition:transform .15s}
.novapl[open] .novaplh:after{transform:rotate(90deg)}
.novapb{padding:0 8px 12px;max-height:420px;overflow-y:auto}
.plhead{font:600 9.5px/1 ui-monospace,monospace;letter-spacing:.16em;color:var(--gold);
  text-transform:uppercase;margin:12px 0 5px;padding:0 7px}
.plline{font-size:13.5px;color:var(--dim);margin:9px 0 3px;padding:0 7px}
.plrow{display:flex;align-items:center;gap:10px;padding:7px 7px;border-radius:5px;cursor:pointer}
.plrow:hover{background:#17150F}
.plrow.on{background:#241B0D}
.plrow.on .plnm{color:var(--gold)}
.plno{font:400 10.5px/1 ui-monospace,monospace;color:var(--dim);width:22px;flex:none}
.plnm{flex:1;font:400 13px/1.3 ui-monospace,monospace;color:var(--ink);min-width:0;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.plsec{font:400 10.5px/1 ui-monospace,monospace;color:var(--dim);flex:none}
.pldl{color:var(--gold);text-decoration:none;font-size:15px;padding:2px 7px;flex:none;
  border:1px solid var(--rule);border-radius:4px}
.takec{font:600 10px/1 ui-monospace,monospace;color:#16110D;background:var(--gold);
  border-radius:999px;padding:4px 8px;flex:none}
.takecn{font:600 10px/1 ui-monospace,monospace;color:var(--dim);margin-right:7px}
.sline{margin:5px 0 0;font-size:12.5px;line-height:1.5}
.slw{display:block;font:600 9px/1 ui-monospace,monospace;letter-spacing:.14em;
  color:var(--gold);text-transform:uppercase;margin-top:5px}
.slt{display:block;color:var(--ink)}
.dlg{margin:14px 0 4px;border-left:2px solid var(--gold);padding-left:14px}
.dlgr{margin:0 0 14px}
.dlgw{font:600 10px/1 ui-monospace,monospace;letter-spacing:.16em;color:var(--gold);
  text-transform:uppercase}
.dlgl{font-size:17px;line-height:1.5;margin:4px 0 2px;color:var(--ink)}
.dlgd{font-size:12.5px;color:var(--dim);font-style:italic;margin-bottom:6px}
.dlga{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.dlga audio{height:32px;max-width:260px}
.dlgs{font:400 11px/1 ui-monospace,monospace;color:var(--dim)}
.soon{font:600 10px/1 ui-monospace,monospace;letter-spacing:.12em;color:var(--dim);
  border:1px solid var(--rule);border-radius:6px;padding:6px 10px}
.twoup{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0 6px}\n@media(max-width:760px){.twoup{grid-template-columns:1fr}}\n.twoup .srcbox{margin:0}\n.idb{margin:22px 0}
.idh{font:600 10px/1 ui-monospace,monospace;letter-spacing:.16em;color:var(--gold);
  text-transform:uppercase;margin-bottom:9px}
.idc{font-size:14.5px;line-height:1.62}
.idc pre{white-space:pre-wrap;background:var(--box);border:1px solid var(--rule);
  border-radius:9px;padding:13px 15px;font:400 12.5px/1.55 ui-monospace,monospace;
  overflow-x:auto;margin:0}
.idrefs{display:flex;gap:11px;flex-wrap:wrap}
.idrefs a{display:block;width:150px}
.idrefs img{width:100%;border-radius:7px;border:1px solid var(--rule);display:block}
.idrefs span{display:block;font:400 10px/1.4 ui-monospace,monospace;color:var(--dim);
  margin-top:5px;word-break:break-all}
.rej{display:flex;gap:13px;flex-wrap:wrap}
.rej figure{margin:0;width:190px}
.rej img{width:100%;border-radius:7px;border:1px solid var(--rule);display:block;
  filter:grayscale(.35) opacity(.82)}
.rej figcaption{font:400 10.5px/1.45 ui-monospace,monospace;color:var(--dim);margin-top:5px}
.rejtag{display:inline-block;font:600 9px/1 ui-monospace,monospace;letter-spacing:.12em;
  color:var(--dim);border:1px solid var(--rule);border-radius:5px;padding:4px 7px;
  margin-bottom:4px}
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

/* THE GUIDE. Baba, 3.9.2026: a play button beside every phase title, the same
   brass disc as the number with a black triangle in it, and a bar that is not
   there until it is playing. The bar collapses again on pause, because a row of
   dead scrubbers down a page reads as clutter and none of them mean anything
   while they are stopped. */

/* THE GUIDE CUE. Baba, 4.9.2026: a play button standing in the strip in front
   of the frames it is talking about, so a long scene can carry several and
   nobody has to guess which part of it the voice means. No progress bar: the
   cue is short, it names itself, and a row of scrubbers down a page was
   clutter. */

/* THE SOLO ROW. Baba, 5.9.2026: he wanted myNoise nested inside this page and
   stepped through with arrows. It cannot be framed, x-frame-options is
   SAMEORIGIN, so the links target a NAMED window instead: the first click opens
   it, every later click reuses the same one. Second screen, same behaviour. */

/* SHEETS ARE FOR LOOKING AT. Baba, 5.9.2026: they rendered 44 pixels wide,
   because the markup reused the storyboard strip's classes and `.tiny a` is
   25% of its parent, so a sheet became a thumbnail of a thumbnail. A page whose
   whole job is showing reference art has to SHOW it: fill the width, big cells,
   caption small and underneath, nothing else competing. Twelve key angles at
   forty four pixels is not a reference, it is a decoration. */
.sheetgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));
 gap:14px;margin:14px 0 26px}
.sheetgrid .sh{display:block;text-decoration:none;color:inherit}
.sheetgrid .sh img{width:100%;display:block;border:1px solid var(--rule);
 background:var(--card)}
.sheetgrid .sh:hover img{border-color:var(--brass)}
.sheetgrid .sh span{display:block;font:600 9.5px ui-monospace,monospace;letter-spacing:.08em;
 text-transform:uppercase;color:var(--dim);padding-top:5px}
.sheetgrid .sh:hover span{color:var(--brass)}
@media(max-width:900px){.sheetgrid{grid-template-columns:1fr}}

/* THE DIALOGUE BLOCK. A third picture, two thirds words, speaker top left, and
   one copy button per speech. Selecting text on a phone is miserable and this
   page exists so nobody has to. */
.dlg{border:1px solid var(--rule);border-radius:5px;margin:0 0 12px;overflow:hidden;
 background:var(--card)}
.dlg .dh{display:flex;align-items:center;gap:10px;padding:7px 10px;
 border-bottom:1px solid var(--rule)}
.dlg .who{font:700 10px ui-monospace,monospace;letter-spacing:.14em;color:var(--brass)}
.dlg .frm{font:600 9px ui-monospace,monospace;letter-spacing:.08em;color:var(--dim)}
.dlg .cp{margin-left:auto;border:1px solid var(--rule);border-radius:4px;background:none;
 cursor:pointer;padding:4px 11px;font:600 9px ui-monospace,monospace;letter-spacing:.1em;
 color:var(--dim)}
.dlg .cp:hover{background:var(--brass);border-color:var(--brass);color:#17150f}
.dlg .cp.done{background:var(--brass);border-color:var(--brass);color:#17150f}
.dlg .db{display:grid;grid-template-columns:1fr 2fr;gap:14px;padding:12px}
.dlg .dpic img{width:100%;display:block;border:1px solid var(--rule)}
.dlg .dtx p{margin:0 0 9px;font-size:15px;line-height:1.5;color:var(--body)}
.dlg .dtx p:last-child{margin:0}

.dlg .ttl{font-size:12px;color:var(--dim)}
.dlg .dtx .sp{border-top:1px solid var(--rule);padding:9px 0 4px}
.dlg .dtx .sp:first-child{border-top:0;padding-top:0}
.dlg .dtx .spn{display:flex;align-items:center;gap:10px;margin-bottom:5px}
.dlg .dtx .spn .cp{margin-left:auto;padding:2px 8px;font-size:8px}
.dlg .dpic img{max-height:250px;object-fit:cover}
@media(max-width:700px){.dlg .db{grid-template-columns:1fr}}
.solorow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0 18px}
.sbtn{display:inline-flex;align-items:center;justify-content:center;min-width:34px;height:30px;
 padding:0 10px;border:1px solid var(--rule);border-radius:4px;background:none;cursor:pointer;
 font:600 10px ui-monospace,monospace;letter-spacing:.08em;color:var(--dim);text-decoration:none}
.sbtn:hover,.sbtn.on{background:var(--brass);border-color:var(--brass);color:#17150f}
.sbtn.nav{margin-left:8px;font-size:12px}
.kw{margin-left:auto;font:600 10px ui-monospace,monospace;letter-spacing:.1em;color:var(--brass)}
.tiny .gcue{flex:0 0 auto;display:flex;align-items:center;gap:8px;border:0;cursor:pointer;
 background:none;padding:0 6px 0 0;margin:0;align-self:center;max-width:150px;text-align:left}
.tiny .gcue>svg{width:11px;height:11px;fill:#17150f;flex:0 0 26px;height:26px;width:26px;
 border-radius:50%;background:var(--brass);padding:7px;box-sizing:border-box}
.tiny .gcue svg.ic-s{display:none}
.tiny .gcue[data-on="1"] svg.ic-p{display:none}
.tiny .gcue[data-on="1"] svg.ic-s{display:block}
.tiny .gcue span{font:600 9.5px/1.35 ui-monospace,monospace;letter-spacing:.08em;
 text-transform:uppercase;color:var(--dim)}
.tiny .gcue[data-on="1"] span{color:var(--brass)}
.rtph .gp{width:26px;height:26px;border-radius:50%;background:var(--brass);border:0;
 padding:0;cursor:pointer;flex:0 0 26px;display:flex;align-items:center;justify-content:center;
 align-self:center}
.rtph .gp svg{width:11px;height:11px;fill:#17150f;display:block}
.rtph .gp[data-on="1"] svg.ic-p{display:none}
.rtph .gp svg.ic-s{display:none}
.rtph .gp[data-on="1"] svg.ic-s{display:block}
.rtph .gb{flex:0 1 0;width:0;height:14px;opacity:0;overflow:hidden;cursor:pointer;
 align-self:center;margin:0 0 0 14px;
 transition:flex-basis .18s ease,opacity .18s ease,margin .18s ease}
.rtph .gb[data-open="1"]{flex:1 1 auto;max-width:360px;opacity:1}
.rtph .gb[data-open="1"]~.gt{margin-left:10px}
.rtph .gb i{display:block;height:3px;margin-top:5px;background:var(--rule);position:relative}
.rtph .gb i b{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--brass);display:block}
.rtph .gt{font:600 9.5px ui-monospace,monospace;letter-spacing:.1em;color:var(--dim);
 align-self:center;opacity:0;white-space:nowrap;transition:opacity .18s ease}
.rtph .gb[data-open="1"]~.gt{opacity:1}
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


# The shared Drive folder the top bar links to. Named DRIVE_FOLDER, not DRIVE:
# the drive_links.json lookup below rebinds the bare name DRIVE, and because
# bar() reads it at call time it was emitting the entire links dict into the
# GDRIVE href instead of this URL.
DRIVE_FOLDER = 'https://drive.google.com/drive/folders/1INASz6hT4OUQo4UrpT62rMJaF24Amnuu'


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


def _phkey(v):
    """Phases are mostly numbers and one of them is 9R, the return vortex.

    2.9.2026. int() was fine while every phase was a number and threw the moment
    the flow gained a phase that is not one. Digits first, then any letters, so
    9 sorts before 9R sorts before 10 rather than crashing the build.
    """
    m = re.match(r'(\d*)([a-zA-Z]*)', str(v))
    return (int(m.group(1) or 0), m.group(2))



DIALOGUE = CAT.get('dialogue_scene19', {})


def dialogue_for(shot_id, depth=0):
    """The words, with a player and a download, under the frame they belong to.

    Baba, 3.9.2026: Kristijan should never have to ask anybody for anything. So
    the line, the direction it was read with, the audio and the file itself all
    sit on the page beside the picture. He plays it where he stands, or takes
    the mp3 for the cut.

    The voice is the Hume actress, which is a STAND IN. Baba clones Manan's own
    voice from these, so the download matters as much as the player: the file is
    the thing that gets used, the player only tells you which file you want.
    """
    rows = DIALOGUE.get(shot_id)
    if not rows:
        return ''
    r = '../' * depth
    o = ['<div class=dlg>']
    for x in rows:
        who = x.get('speaker', '')
        o.append('<div class=dlgr>')
        o.append('<div class=dlgw>%s</div>' % who)
        o.append('<div class=dlgl>%s</div>' % html.escape(x.get('line', '')))
        if x.get('direction'):
            o.append('<div class=dlgd>%s</div>' % html.escape(x['direction']))
        a = x.get('audio')
        if a:
            o.append('<div class=dlga><audio controls preload=none src="%s%s"></audio>'
                     '<a class=dl href="%s%s" download>DOWNLOAD &nbsp;MP3</a>'
                     '<span class=dlgs>%s s</span></div>'
                     % (r, a, r, a, x.get('sec', '')))
        o.append('</div>')
    o.append('</div>')
    return ''.join(o)



DRAMA = CAT.get('radio_drama', [])
DRAMA_HR = CAT.get('radio_drama_hr', [])
DRAMA_V3 = CAT.get('radio_drama_v3', [])
DRAMA_V7 = CAT.get('radio_drama_v7', [])
DRAMA_V7_SCENES = CAT.get('radio_drama_v7_scenes', [])
DRAMA_EN = CAT.get('radio_drama_en', [])
DRAMA_EN_SCENES = CAT.get('radio_drama_en_scenes', [])
MUSIC = CAT.get('music', [])
TAKES = CAT.get('manan_takes', {})
COACH = CAT.get('coach_takes', {})


def deck_block(uid, title, sub, rows, zipfile_, depth=0):
    """ONE deck, ONE transport row, ONE zip. Used for every set of audio.

    Baba, 3.9.2026, three corrections in one:

    THE PLAY BUTTON IS IN THE ROW WITH THE OTHERS. A separate big button above
    the transport meant two places to look for a control. It is a cassette deck
    now: play, then the buttons you expect beside it.

    NO DOWNLOAD PER ROW. Forty three download buttons is not a feature. The set
    is zipped once, numbered in playing order so the folder on disk reads as the
    scene, and offered as one file in the transport.

    AND THE DIALOGUE USES THIS TOO. Nineteen bare browser players were still
    sitting loose on the page while the takes had a real deck. One player shape
    for everything that makes a sound.

    rows is a list of (kind, text, src, seconds). kind is head, line or take.
    """
    if not rows:
        return ''
    r = '../' * depth
    takes = [x for x in rows if x[0] == 'take']
    o = ['<div class=nova id=nv-%s>' % uid,
         '<div class=novatc><span class=nv-el>00:00</span>'
         '<span class=nv-rem>-00:00</span></div>',
         '<div class=novah><div><b class=nv-name>%s</b>'
         '<span class=nv-sub>%s</span></div></div>' % (html.escape(title), html.escape(sub)),
         '<div class=novascrub><div class="wave nv-wave"><div class="cursor nv-cur"></div>'
         '</div></div>',
         '<div class=novabar>'
         '<button class="mcbtn play nv-play" type=button title="play">'
         '<svg class=ic-play viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg>'
         '<svg class=ic-pause viewBox="0 0 24 24" style="display:none">'
         '<path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg></button>'
         '<button class="mcbtn nv-stop" type=button title="stop">'
         '<svg viewBox="0 0 24 24"><path d="M6 6h12v12H6z"/></svg></button>'
         '<button class="mcbtn nv-first" type=button title="first">'
         '<svg viewBox="0 0 24 24"><path d="M6 5h2v14H6zM20 5v14L9 12z"/></svg></button>'
         '<button class="mcbtn nv-prev" type=button title="previous">'
         '<svg viewBox="0 0 24 24"><path d="M11 5v14L2 12zM22 5v14l-9-7z"/></svg></button>'
         '<button class="mcbtn nv-next" type=button title="next">'
         '<svg viewBox="0 0 24 24"><path d="M13 5v14l9-7zM2 5v14l9-7z"/></svg></button>'
         '<button class="mcbtn nv-last" type=button title="last">'
         '<svg viewBox="0 0 24 24"><path d="M18 5h2v14h-2zM4 5v14l11-7z"/></svg></button>'
         '%s'
         '<span class="novastate nv-state">READY</span></div>'
         % (('<a class="mcbtn wide" href="%s" download title="all of them, zipped">'
             'DOWNLOAD &nbsp;ZIP</a>' % aud(zipfile_)) if zipfile_ else ''),
         '<details class=novapl><summary class=novaplh>'
         '<span class=takec>%d</span>PLAYLIST</summary><div class=novapb>' % len(takes)]
    i = 0
    for kind, text, src, sec in rows:
        if kind == 'head':
            o.append('<div class=plhead>%s</div>' % html.escape(text))
        elif kind == 'line':
            o.append('<div class=plline>%s</div>' % html.escape(text))
        else:
            o.append('<div class=plrow data-i="%d" data-src="%s" data-name="%s">'
                     '<span class=plno>%d</span><span class=plnm>%s</span>'
                     '<span class=plsec>%s s</span></div>'
                     % (i, aud(src), html.escape(text), i + 1, html.escape(text), sec))
            i += 1
    o.append('</div></details></div>')
    return ''.join(o)


DECK_JS = """<script>
/* One controller, applied to every deck on the page. Modelled on Baba's own
   NOVA_TV_777 player: waveform that fills behind a cursor, real peaks loaded
   per file, click to scrub, and a host that does not serve HTTP Range leaves
   the audio unseekable so the scrub stops pretending rather than lying. */
(function(){
  [].slice.call(document.querySelectorAll('.nova')).forEach(function(wrap){
    var rows = [].slice.call(wrap.querySelectorAll('.plrow'));
    if (!rows.length) return;
    var q = function(c){ return wrap.querySelector(c); };
    var audio = new Audio(); audio.preload = 'metadata';
    var wave=q('.nv-wave'), cur=q('.nv-cur'), el=q('.nv-el'), rem=q('.nv-rem');
    var nm=q('.nv-name'), sub=q('.nv-sub'), btn=q('.nv-play'), st=q('.nv-state');
    var pl = wrap.querySelector('details');
    var title = nm.textContent, subtitle = sub.textContent;
    var idx=-1, chain=true, bars=[];
    for (var i=0;i<110;i++){ var b=document.createElement('span');
      b.style.height='16%'; wave.appendChild(b); }
    bars=[].slice.call(wave.querySelectorAll('span'));
    function mmss(s){ s=Math.max(0,s||0);
      return String(Math.floor(s/60)).padStart(2,'0')+':'+
             String(Math.floor(s%60)).padStart(2,'0'); }
    function dur(){ return (audio.duration && isFinite(audio.duration)) ? audio.duration : 0; }
    function canSeek(){ var s=audio.seekable; return !!(s&&s.length&&s.end(s.length-1)>1); }
    function peaks(src){
      for (var i=0;i<bars.length;i++) bars[i].style.height='16%';
      fetch(src.slice(0,-4)+'.json').then(function(r){return r.ok?r.json():null;})
        .then(function(j){ if(!j||!j.bars) return;
          for (var i=0;i<bars.length;i++){
            var v=j.bars[Math.floor(i*j.bars.length/bars.length)]||0;
            bars[i].style.height=Math.max(14,v*100)+'%'; }
        }).catch(function(){});
    }
    function paint(){
      var D=dur(), c=audio.currentTime||0, p=D?c/D:0;
      for (var i=0;i<bars.length;i++) bars[i].classList.toggle('played', i/bars.length<=p);
      cur.style.left=(p*100)+'%';
      el.textContent=mmss(c); rem.textContent='-'+mmss(D-c);
    }
    function setPlaying(on){
      btn.classList.toggle('on',on);
      btn.querySelector('.ic-play').style.display  = on?'none':'block';
      btn.querySelector('.ic-pause').style.display = on?'block':'none';
      st.textContent = on?'PLAYING':(idx>=0?'PAUSED':'READY');
    }
    function load(i,play){
      if(i<0||i>=rows.length) return;
      idx=i; rows.forEach(function(x,k){ x.classList.toggle('on',k===i); });
      audio.src=rows[i].dataset.src;
      nm.textContent=rows[i].dataset.name;
      sub.textContent=(i+1)+' of '+rows.length;
      peaks(rows[i].dataset.src); paint();
      if(play){ if(pl) pl.open=true; audio.play().catch(function(){}); }
    }
    audio.addEventListener('timeupdate',paint);
    audio.addEventListener('loadedmetadata',function(){
      paint(); wave.style.cursor=canSeek()?'pointer':'default'; });
    audio.addEventListener('play',function(){ setPlaying(true); });
    audio.addEventListener('pause',function(){ if(!audio.ended) chain=false; setPlaying(false); });
    audio.addEventListener('ended',function(){ setPlaying(false);
      if(chain && idx+1<rows.length) load(idx+1,true); });
    btn.onclick=function(){
      if(idx<0){ chain=true; load(0,true); return; }
      if(audio.paused){ chain=true; audio.play().catch(function(){}); } else audio.pause(); };
    q('.nv-stop').onclick=function(){
      audio.pause(); audio.currentTime=0; chain=false; idx=-1;
      rows.forEach(function(x){ x.classList.remove('on'); });
      nm.textContent=title; sub.textContent=subtitle; paint(); setPlaying(false); };
    q('.nv-first').onclick=function(){ chain=true; load(0,true); };
    q('.nv-last').onclick =function(){ chain=true; load(rows.length-1,true); };
    q('.nv-prev').onclick =function(){ chain=true; load(idx<=0?0:idx-1,true); };
    q('.nv-next').onclick =function(){ chain=true;
      load(idx+1>=rows.length?rows.length-1:idx+1,true); };
    wave.addEventListener('click',function(e){
      if(!canSeek()) return;
      var b=e.currentTarget.getBoundingClientRect();
      audio.currentTime=((e.clientX-b.left)/b.width)*dur(); paint(); });
    rows.forEach(function(x,i){ x.addEventListener('click',function(){ chain=true; load(i,true); }); });
    load(0,false);
  });
})();
</script>"""



def drama_block(depth=0):
    """The film as a radio drama, three voices, one file per paragraph.

    Baba is dyslexic and short sighted, so reading a page of prose to check
    whether the film is understood is the slowest possible way for him to do it.
    Listening is not a convenience here, it is the difference between checking
    the thing and not checking it.

    Narrator, Manan and Viveka on separate voices so the exchange in the
    control room plays as an exchange rather than as one person reading both
    halves of it.
    """
    if not DRAMA:
        return ''
    rows = [('head', 'THE FILM, AS IT READS OFF THE PAGE', '', 0)]
    for x in DRAMA:
        rows.append(('line', x['speaker'] + '   ' + x['text'][:90], '', 0))
        rows.append(('take', '%02d %s' % (x['n'], x['speaker']), x['audio'], x['sec']))
    return deck_block('drama', 'THE BRAIN BRAKE, READ ALOUD',
                      '%d parts, three voices, about three minutes.' % len(DRAMA),
                      rows, 'downloads/BRAIN_BRAKE_radio_drama.zip', depth)



def drama_hr_block(depth=0):
    """V2, in Croatian, with the theories spoken and the dedication at the end.

    Two things V1 was missing and Baba caught both. The theories were only
    described, never SAID, so the argument the film is built on was never heard.
    And it ended on the credits rather than on the offering.

    Russian voices reading Croatian. Speechify has no Croatian voice, and Baba's
    own suggestion was that the Slavic ones land close enough. The multilingual
    model handles the diacritics.
    """
    if not DRAMA_HR:
        return ''
    rows = [('head', 'HRVATSKI, V2, S TEORIJAMA', '', 0)]
    for x in DRAMA_HR:
        rows.append(('line', x['speaker'] + '   ' + x['text'][:90], '', 0))
        rows.append(('take', '%02d %s' % (x['n'], x['speaker']), x['audio'], x['sec']))
    return deck_block('dramahr', 'THE BRAIN BRAKE, NA HRVATSKOM',
                      '%d dijelova, tri glasa, oko \u010detiri minute. S teorijama i posvetom.'
                      % len(DRAMA_HR),
                      rows, 'downloads/BRAIN_BRAKE_radio_drama_HR_v2.zip', depth)



def drama_v3_block(depth=0):
    """V3. Croatian, on real Croatian voices, with two corrections from Baba.

    A MARATHON RUNNER runs at the start, not the boy. That was wrong in V1 and
    V2 and it matters: the film opens on somebody who has done this all his life,
    which is what makes the limit worth asking about.

    AND THE TWO HANDS PASSAGE IS OUT. Why Viveka's hand and Manan's never
    share a frame is a note about how the film is made, not part of the film.
    Explaining the craft inside the story breaks it.

    Srecko and Gabrijela, from Edge. The Russian voices reading Croatian in V2
    were a reasonable guess and they were bad; these are the real thing. Manan is
    Srecko lifted and quickened, because two voices have to carry three parts and
    the boy must not sound like the man answering him.
    """
    if not DRAMA_V3:
        return ''
    rows = [('head', 'HRVATSKI V3, SRECKO I GABRIJELA', '', 0)]
    for x in DRAMA_V3:
        rows.append(('line', x['speaker'] + '   ' + x['text'][:90], '', 0))
        rows.append(('take', '%02d %s' % (x['n'], x['speaker']), x['audio'], x['sec']))
    return deck_block('dramav3', 'THE BRAIN BRAKE, HRVATSKI V3',
                      '%d dijelova, oko pet minuta. Srecko i Gabrijela.' % len(DRAMA_V3),
                      rows, 'downloads/BRAIN_BRAKE_radio_drama_HR_v3.zip', depth)



def script_block(lines, scenes, uid, title, depth=0):
    """The words, beside the deck but OUTSIDE it.

    Baba, 3.9.2026: "the first scene is one file, and then again it breaks down
    to paragraphs". It did. The playlist carried a row per line as well as the
    scene file, so a deck that was supposed to be ten things to play read as
    seventy one paragraphs with a file buried in them. The playlist is now
    exactly the ten scenes and nothing else. The text is still here, folded,
    because Kristijan reads it while it plays, but it is no longer inside the
    thing you press play on.
    """
    o = ['<details class=novapl><summary class=novaplh>'
         '<span class=takec>%d</span>%s</summary><div class=novapb>'
         % (len(lines), html.escape(title))]
    for i, sc in enumerate(scenes, 1):
        o.append('<div class=plhead>%d.  %s</div>' % (i, html.escape(sc['title'])))
        for x in lines:
            if x.get('scene') == sc['id']:
                mark = '' if x.get('audio') or x.get('file') else '   [još nije snimljeno]'
                o.append('<div class=plline>%s</div>'
                         % html.escape(x['speaker'] + '   ' + x['text'] + mark))
    o.append('</div></details>')
    return ''.join(o)


def drama_v7_block(depth=0):
    """The film out loud, ONE FILE PER SCENE.

    Baba, 3.9.2026, two corrections in one.

    IT MUST START AT THE BEGINNING. The first cut of v7 rewrote the whole of
    scene one, so all twenty four opening lines lost their takes and the deck
    began playing at part twenty five. Most of those lines had not actually
    changed. v7 is now built by walking v6 line by line, keeping the ones that
    still describe the cut in v6's own words so the recording still fits, and
    writing new text only where a beat did not exist before. Three lines were
    dropped because the new cut made them untrue: the world rubbing up out of
    the paper in order, the freeze mid stride, and the inspection of legs then
    face then banner.

    AND NOT BY THE PARAGRAPH. Seventy seven parts is a filing system, not a
    thing to listen to. The parts are stitched into one file per scene, ten of
    them, and the text of each scene sits above its file so it can be read
    while it plays. Nine lines in scene one are written and not yet recorded;
    they show as text and the stitched file simply does not contain them.
    """
    if not DRAMA_V7_SCENES:
        return ''
    silent = sum(1 for x in DRAMA_V7 if not x.get('audio'))
    rows = [('take', '%02d %s' % (i, sc['title']), sc['url'], sc['sec'])
            for i, sc in enumerate(DRAMA_V7_SCENES, 1)]
    total = sum(sc['sec'] for sc in DRAMA_V7_SCENES)
    return deck_block('dramav7', 'THE BRAIN BRAKE, CIJELI FILM',
                      '%d scena, %d minuta %d sekundi. Jedna datoteka po sceni. Gabrijela pripovijeda, '
                      'Srecko je Manan, Viveka je nov. Još %d rečenica u prvoj '
                      'sceni čeka Gabrijelu.'
                      % (len(DRAMA_V7_SCENES), int(total) // 60, int(total) % 60, silent),
                      rows, 'downloads/BRAIN_BRAKE_radio_drama_HR_v7.zip', depth)


def drama_en_block(depth=0):
    """The same film out loud in English, so it travels.

    Baba, 3.9.2026. The Croatian drama is for Baba and Kristijan. This one is
    for everybody else the film has to reach, and the Breakthrough Junior
    Challenge is judged in English.

    Line for line with the Croatian, same seventy seven parts, same ten scenes,
    so the two can be laid side by side. Voiced on Speechify across all twenty
    one keys: Beatrice narrates, which is the same seat that reads the book, and
    Edmund and Hugh are Manan and Viveka. Three British voices so the accent
    does not wander mid scene, and the narrator names the speaker before every
    line exactly as the Croatian does.
    """
    if not DRAMA_EN_SCENES:
        return ''
    rows = [('take', '%02d %s' % (i, sc['title']), sc['url'], sc['sec'])
            for i, sc in enumerate(DRAMA_EN_SCENES, 1)]
    total = sum(sc['sec'] for sc in DRAMA_EN_SCENES)
    return deck_block('dramaen', 'THE BRAIN BRAKE, THE WHOLE FILM IN ENGLISH',
                      '%d scenes, %d minutes %d seconds. One file per scene. '
                      'Beatrice narrates, Edmund is Manan, Hugh is Viveka.'
                      % (len(DRAMA_EN_SCENES), int(total) // 60, int(total) % 60),
                      rows, 'downloads/BRAIN_BRAKE_radio_drama_EN.zip', depth)


def dialogue_wav_block(depth=0):
    """EVERY SPOKEN LINE, AS AUDIO, FOUR VOICES PER CHARACTER.

    Baba, 4.9.2026: he chooses the voice in the edit room, not here. So every
    line exists four times over and the note says the one thing that matters
    about using it: take a folder WHOLE. A character who changes voice between
    sentences is two characters.
    """
    z = ('https://raw.githubusercontent.com/markoboskoauroville/BRAINBREAK_AUDIO/'
         'main/downloads/BRAIN_BRAKE_DIALOGUE_WAV.zip')
    return ('<div class=srcbox><div class=t><b>Every spoken line, 48k wav</b>'
            '<a class=dl href="%s">DOWNLOAD &nbsp;ZIP &nbsp;26 MB</a></div>'
            '<p>Twenty three lines, ninety two files, numbered in film order. FOUR VOICES PER '
            'CHARACTER so the edit room chooses: Manan as edmund, archie, rohan or chase, and '
            'Viveka as hugh, dominic, alec or joe. Listen to the same line in all four folders and '
            'then take that folder whole; a character who changes voice between sentences is two '
            'characters. Manan\u2019s first two lines are already shot in his own voice, so those '
            'wavs are a comparison and not a replacement.</p></div>' % z)


def music_block(depth=0):
    """The two pieces written for the film.

    Here so Kristijan can hear what the picture is going to sit on. An animator
    working to the music times things differently from one working in silence,
    and these were composed before the animation, which is the right way round.
    """
    if not MUSIC:
        return ''
    rows = []
    for m in MUSIC:
        rows.append(('line', m['name'] + '   ' + m.get('note', ''), '', 0))
        rows.append(('take', m['name'], m['file'], m.get('sec', 0)))
    return deck_block('music', 'THE MUSIC, WRITTEN FOR THE FILM',
                      'Theme song and end credits. Composed before the animation.',
                      rows, 'downloads/BRAIN_BRAKE_music.zip', depth)


def takes_block(depth=0):
    rows = []
    for who, table in (('MANAN, THE OLD THEORY', TAKES),
                       ('MANAN AS VIVEKA', COACH)):
        if not table:
            continue
        rows.append(('head', who, '', 0))
        for key, blk in table.items():
            if not blk.get('takes'):
                continue
            rows.append(('line', blk.get('line', ''), '', 0))
            for t in blk['takes']:
                rows.append(('take',
                             t['name'].replace('REC0000', 'rec ').replace('CB0000', 'cb '),
                             t['file'], t.get('sec', 0)))
    n = len([x for x in rows if x[0] == 'take'])
    return deck_block('takes', 'THE RECORDED PERFORMANCE',
                      '%d takes. Manan, and Manan as Viveka.' % n,
                      rows, 'downloads/BRAIN_BRAKE_takes.zip', depth)


def dialogue_block(depth=0):
    """The scene as written, read by the Hume actress. Same deck as the takes."""
    rows = []
    for sid, lines in DIALOGUE.items():
        for x in lines:
            rows.append(('line', x.get('speaker', '') + '   ' + x.get('line', ''), '', 0))
            rows.append(('take', x.get('line', '')[:52], x.get('audio', ''), x.get('sec', 0)))
    n = len([x for x in rows if x[0] == 'take'])
    return deck_block('dlg', 'THE SCENE, READ',
                      '%d lines. A stand in read, for timing and for the cut.' % n,
                      rows, 'downloads/BRAIN_BRAKE_scene19_dialogue.zip', depth)



def lines_of(e):
    """The dialogue for one shot, as TEXT under its thumbnail.

    Baba, 3.9.2026: Kristijan does not need to listen to anything. He needs to
    know what is said over the frame he is animating, so the words go under the
    picture and in the shot's own card. The audio has its own page and does not
    pollute this one.
    """
    d = e.get('dialogue') or []
    if not d:
        return ''
    o = ['<div class=sline>']
    for x in d:
        o.append('<span class=slw>%s</span><span class=slt>%s</span>'
                 % (html.escape(x.get('speaker', '')), html.escape(x.get('line', ''))))
    o.append('</div>')
    return ''.join(o)



# EVERY AUDIO PATH POINTS AT THE AUDIO REPOSITORY. 3.9.2026. This repository
# publishes the Pages site and Pages fails SILENTLY above 1 GB; at 876 MB two
# builds failed in a row while the content was correct and nothing errored.
# Audio was what filled it, so it lives in BRAINBREAK_AUDIO and the site links
# to it. Public, no Pages site of its own, no ceiling, no credential needed.
AUDIO = 'https://raw.githubusercontent.com/markoboskoauroville/BRAINBREAK_AUDIO/main/'


def aud(path):
    """A raw link to the audio repository, from a site relative path.

    3.9.2026: this prefixed everything, including paths that were ALREADY
    absolute after the catalogue was repointed, so every source came out as
    the base glued onto a full URL and every single one 404'd. Nothing played
    and nothing said why: the deck loaded, the button worked, the browser
    fetched a dead link and stayed silent.

    An absolute URL is already the answer and is returned untouched.
    """
    path = str(path)
    if path.startswith(('http://', 'https://')):
        return path
    return AUDIO + path.lstrip('./')


def bar(here, r):
    """TWO PLACES ONLY: this page, and the archive.

    Baba, 2.9.2026: everything is on the main page now, so every other link in
    this bar was clutter competing with the one thing anybody came for. Nineteen
    scene buttons, footage, assets, brainstorm, breakdown, documentation, and a
    Drive folder, above a page that already contains all of it.

    The other pages still exist and are still built. They are LISTED ON THE
    ARCHIVE PAGE, so nothing is lost and nothing is deleted, it is simply no
    longer shouting. If a page turns out to be needed weekly it can come back;
    the cost of finding it in the archive twice is smaller than the cost of a
    bar nobody reads.
    """
    o = ['<div class=bar>',
         '<a class=home href="%sindex.html"%s>THE FILM</a>' % (r, ' class=on' if here == 'home' else ''),
         # 3.9.2026: the radio drama is the fastest way to understand the film,
         # and it was reachable only through the archive, two clicks behind a
         # page called Archive. That is the wrong place for the thing you would
         # hand somebody first.
         '<a href="%sradiodrama.html"%s>MUSIC</a>'
         % (r, ' class=on' if here == 'drama' else ''),
         # 4.9.2026: the sheets are what an animator opens BEFORE drawing
         # anything, and they were scattered across scene folders with
         # storyboard=hide, reachable only by knowing they existed.
         '<a href="%ssheets.html"%s>SHEETS</a>'
         % (r, ' class=on' if here == 'sheets' else ''),
         '<a href="%ssound.html"%s>SOUND</a>'
         % (r, ' class=on' if here == 'sound' else ''),
         '<a href="%sdialogue.html"%s>DIALOGUE</a>'
         % (r, ' class=on' if here == 'dialogue' else ''),
         '<a href="%sarchive.html"%s>ARCHIVE</a>' % (r, ' class=on' if here == 'archive' else ''),
         '<span class=sp></span>',
         ('<span class=vb>%s</span>' % VERSION) if VERSION else '',
         '<span class=sitev title="site version">v%d</span>' % SITEV,
         '<button class=th id=th onclick="tt()" title="light or dark">&#9681;</button>',
         '</div>']
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
            '</div></div>%s</body></html>'
            % (title, r, r, r, r, CSS, GATE if GATED else '',
               'none' if GATED else 'block', bar(here, r), body,
               FILM, SUBTITLE, EVENT,
               LOOP_JS if '<video' in body else ''))


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


ORIGINALS = {}
_ol = os.path.join(ROOT, 'originals.json')
if os.path.exists(_ol):
    try:
        ORIGINALS = json.load(open(_ol))
    except Exception:
        ORIGINALS = {}



def rejected_takes(e):
    """Every other version of THIS frame, newest first.

    Baba, 2.9.2026: a rejected take is not rubbish. The square vortex was
    rejected for its aspect and was the best drawing of the three. So they are
    kept, shown, and labelled, and a later session can see what was tried and
    why the chosen one won.

    Frames are siblings when their name matches up to the version suffix:
    9-1-VORTEX-UP-v1 and 9-1-VORTEX-UP-v3 are the same frame twice.
    """
    b = os.path.basename(e.get('file', ''))
    stem = re.sub(r'-v\d+(\.\w+)?$', '', os.path.splitext(b)[0])
    if not stem:
        return []
    out = []
    for o in ENTRIES:
        if o is e or not o.get('file'):
            continue
        ob = os.path.splitext(os.path.basename(o['file']))[0]
        if re.sub(r'-v\d+$', '', ob) == stem:
            out.append(o)
    def vnum(o):
        m = re.search(r'-v(\d+)$', os.path.splitext(os.path.basename(o['file']))[0])
        return int(m.group(1)) if m else 0
    return sorted(out, key=vnum, reverse=True)


def idcard_block(title, body, dim=False):
    return ('<div class=idb><div class=idh>%s</div><div class=idc%s>%s</div></div>'
            % (title, ' style="color:var(--dim)"' if dim else '', body))


def full_link(path, prefix=''):
    """Where the full resolution original lives, or the local file if it is
    still in the repository.

    Three places are tried, in this order, and the order is the history of the
    project. ORIGINALS first: BRAIN_BRAKE_ORIGINALS is public, has no Pages
    site and therefore no 1 GB ceiling, and a raw link needs no permission call
    and no credential, so there is no state that can drift. DRIVE second, still
    read so that anything not yet migrated keeps working. The local file last.

    An EMPTY url is a claim, not a link. STEP 86: the chat session writes
    {"bytes": 0, "url": ""} when it files a frame from a phone and something
    else fills it in later. So the url is tested for truth, never the row,
    or every frame waiting in that queue renders href="" on the page.
    """
    b = os.path.basename(path)
    for table in (ORIGINALS, DRIVE):
        v = table.get(b)
        if not v:
            continue
        u = v if isinstance(v, str) else v.get('url', '')
        if u:
            return u
    return prefix + path


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
        # 2.9.2026: this accepted lowercase only, so shot 9R parsed as plain 9
        # and the vortex DOWN could not be told apart from the vortex UP.
        # Its whole section rendered empty while the frames sat in the other one.
        m = _r.match(r'(\d*)([a-zA-Z]*)', p)
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


for n in sorted(SCENES, key=_phkey):
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
        b.append('<div class=sheet><a href="%s"><img src="../%s" alt=""></a>'
                 '<div class=meta><span class=fid>%s</span>%s%s'
                 '<p class=note>%s</p>%s</div></div>'
                 % (full_link(e['file'], '../'), small(e['file']), e.get('title', 'character sheet'),
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
                b.append('<div class=cell><a href="%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s%s'
                         '<p class=note>%s</p>%s%s'
                         '</div></div>'
                         % (full_link(e['file'], '../'), small(e['file'], 'tiny'), fid,
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
                k.append('<div class=cell><a href="%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s%s%s'
                         '<p class=note>%s</p>%s%s</div></div>'
                         % (full_link(e['file'], '../'),
                            small(e['file']), os.path.basename(e['file']),
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
            rows.append('<div class=lay><a href="%s"><img src="../%s" alt="" loading=lazy></a><div>'
                        '<div class=n>%s</div><div class=s>%s &nbsp;·&nbsp; %s</div>'
                        '<a href="%s" download>Download</a></div></div>'
                        % (full_link(p, '../'), small(p), os.path.basename(p), dims(p),
                           human(size_of(p)), full_link(p, '../')))
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
# ------------------------------------------------------------- radio drama page
# The film out loud, and the music it sits on. Its own page because the film page
# is for looking and this page is for listening, and mixing the two made the one
# that does the work twice as long to read.
# THE DRAMA CAME OFF THIS PAGE. Baba, 4.9.2026: it described a film that no
# longer exists. The house is vertical now, the corridor of organ rooms is gone
# and Coach Brain is Viveka, and a recording of the old cut sitting under its own
# tab is worse than no recording at all, because somebody will listen to it and
# believe it. What the drama was for is done better on the film page anyway: the
# guide cues stand in front of the frames they describe and carry the dialogue,
# acted, so the words arrive next to the picture instead of on a page of their
# own. This page is the music now, which is the one thing on it that was never
# out of date.
_rd = ['<h1>The music, written for the film</h1>',
       '<p class=lede>The theme and the end credits, composed before the animation existed. '
       '<b>The film told out loud now lives on the film page</b>, in front of the frames it '
       'describes, so the words and the pictures arrive together.</p>',
       dialogue_wav_block(), music_block(), DECK_JS]
open(os.path.join(ROOT, 'radiodrama.html'), 'w').write(
    page('The music', ''.join(_rd), here='drama', depth=0))

# ---------------------------------------------------------------- dialogue page
# The audio has its OWN page. Baba, 3.9.2026: Kristijan does not need to listen
# to anything, he needs the words under the frame he is animating, so the decks
# were taking room on the page that does the work. Nothing is lost, it simply
# stopped being in the way.
_dg = ['<h1>Dialogue and takes</h1>',
       '<p class=lede>Everything that makes a sound. <b>The scene as written, read by a stand in '
       'voice, and Manan\u2019s own recorded takes.</b> The words themselves are on the film page '
       'under each frame, which is where they are needed; this is for listening, choosing a take '
       'and taking the files.</p>',
       drama_v3_block(), drama_hr_block(), drama_block(), dialogue_block(), takes_block(), DECK_JS]
open(os.path.join(ROOT, 'dialogue.html'), 'w').write(
    page('Dialogue', ''.join(_dg), here='archive', depth=0))

if True:
    ARCHIVE.setdefault('items', [])
    # EVERY OTHER PAGE LIVES HERE NOW. 2.9.2026. The bar is the film and the
    # archive, nothing else, so the pages that used to be buttons are listed
    # here instead. They are still built and still current; they have simply
    # stopped competing with the one page anybody came for. Nothing is deleted,
    # because a page that is hard to find can be found and a page that is gone
    # cannot.
    _other = [('radiodrama.html', 'The music, written for the film',
               'The theme and the end credits, composed before the animation'),
              ('dialogue.html', 'Dialogue and takes',
               'Every line read aloud, and Manan\u2019s own takes, with the zips'),
              ('footage.html', 'Footage', 'Every live shot, its plate and its ProRes'),
              ('assets.html', 'Assets', 'The key in 3D, the vortex for Blender, the font'),
              ('brainstorm.html', 'Brainstorm', 'Everything collected per phase, kept and abandoned'),
              ('breakdown.html', 'Breakdown', 'Layers, plates and composites, frame by frame'),
              ('documentation.html', 'Documentation', 'How the film is put together'),
              ('animatic.html', 'Animatic', 'The film as a timed strip')]
    a = ['<h1>Archive</h1>',
         '<p class=lede>Everything that is not the film itself. <b>The main page holds the whole '
         'film and every download you need</b>, so nothing here is needed to do the work. It is '
         'here so it can be found when it is wanted.</p>',
         '<div class=arcg>THE OTHER PAGES</div>', '<div class=arc>']
    for _h, _n, _d in _other:
        if os.path.exists(os.path.join(ROOT, _h)):
            a.append('<div class=arcr><a href="%s">%s</a>'
                     '<span class=d>%s</span><span class=z>page</span></div>' % (_h, _n, _d))
    for _n in sorted(SCENES, key=lambda x: (len(str(x)), str(x))):
        _h = 'BB_C_%s/index.html' % _n
        if os.path.exists(os.path.join(ROOT, _h)):
            a.append('<div class=arcr><a href="%s">Scene %s</a>'
                     '<span class=d>%s</span><span class=z>page</span></div>'
                     % (_h, _n, SCENES.get(_n, '')))
    a.append('</div>')
    a += ['<div class=arcg>EVERYTHING AT FULL SIZE</div>', '<div class=arc>',
          '<div class=arcr><a href="%s" target=_blank rel=noopener>Footage on Drive</a>'
          '<span class=d>ProRes masters and every take</span><span class=z>drive</span></div>'
          % DRIVE_FOLDER,
          '<div class=arcr><a href="https://github.com/markoboskoauroville/BRAIN_BRAKE_ORIGINALS" '
          'target=_blank rel=noopener>Full resolution originals</a>'
          '<span class=d>Every still at full size, public, no sign in needed</span>'
          '<span class=z>repo</span></div>', '</div>']
    a += ['<div class=arcg>DOCUMENTS</div>',
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
        # 2.9.2026. Three rows here pointed at raw links for files that are not
        # in any repository: PRINT_PACK.pdf and read throughs v4 and v8, the two
        # 75 MB ones that were moved to Drive when they took the site over the
        # Pages ceiling. MOVED_TO_DRIVE already knew about the read throughs and
        # this builder never consulted it, so the archive advertised three
        # documents that opened on a 404 page. It consults it now, and anything
        # with neither a repository file nor a Drive entry is shown as gone
        # rather than as a link. An archive that lies about what it holds is
        # worse than one with a hole in it.
        _u = it['url']
        _local = _u.split('/main/', 1)[1] if '/main/' in _u else None
        _moved = MOVED_TO_DRIVE.get(_local) if _local else None
        _here = _local and 'ANIMATOR_COLLABORATION' in _u and \
            os.path.exists(os.path.join(ROOT, urllib.parse.unquote(_local)))
        if _moved:
            _u = _moved
        elif _local and 'ANIMATOR_COLLABORATION' in _u and not _here:
            a.append('<div class=arcr><span style="flex:1;color:var(--dim)">%s</span>'
                     '<span class=d>%s</span><span class=z>gone</span></div>'
                     % (it['name'], it.get('date', '')))
            continue
        a.append('<div class=arcr><a href="%s" target=_blank rel=noopener>%s</a>'
                 '<span class=d>%s</span><span class=z>%s MB</span></div>'
                 % (_u, it['name'], it.get('date', ''), it['mb']))
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
# A SHOT NUMBER IS WHAT PUTS A FRAME ON THE STORYBOARD. 3.9.2026: the three
# video loops were catalogued as keyframes so they would get cards and downloads
# like any drawn shot, and they carry no shot number because their place on the
# page is inside the last shot strip. Without this the grouping raised KeyError
# on the first one and the whole build stopped.
_kf = [e for e in ENTRIES if e.get('kind') == 'keyframe'
       and e.get('status') != 'superseded'
       and e.get('shot')
       and not e.get('storyboard') == 'hide']
_kf.sort(key=lambda e: shot_key(e.get('shot', '0')))
_byscene = {}
for e in _kf:
    _byscene.setdefault(str(e['shot']).split('.')[0], []).append(e)

LOOP_JS = """<script>
/* KEEP THE LOOPS LOOPING. Baba, 3.9.2026: take two ran on the desktop and
   stopped on the phone. Both clips are faststart h264 with no audio track and
   identical markup, so the file was not the difference; the length was. Take one
   is nine seconds and take two is thirty three, and a browser will carry a short
   autoplaying clip forever while it quietly gives up on a long one, especially
   on battery. The loop attribute is a request, not a guarantee.
   So: start when it scrolls into view, restart by hand when it ends, and try
   again on the first tap if autoplay was refused outright. */
(function(){
  var vs = [].slice.call(document.querySelectorAll('video[loop]'));
  if (!vs.length) return;
  function go(v){ var p = v.play(); if (p && p.catch) p.catch(function(){}); }
  vs.forEach(function(v){
    v.addEventListener('ended', function(){ v.currentTime = 0; go(v); });
    v.addEventListener('pause', function(){
      if (!v.ended && !v.dataset.held && v.readyState > 2) go(v); });
    v.addEventListener('stalled', function(){ go(v); });
  });
  if ('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if (e.isIntersecting){ e.target.dataset.held = ''; go(e.target); }
        else { e.target.dataset.held = '1'; e.target.pause(); }
      });
    }, {rootMargin: '200px'});
    vs.forEach(function(v){ io.observe(v); });
  } else { vs.forEach(go); }
  document.addEventListener('touchstart', function once(){
    vs.forEach(function(v){ if (v.paused && !v.dataset.held) go(v); });
    document.removeEventListener('touchstart', once);
  }, {passive: true});
})();
</script>"""


GUIDE_JS = """<script>
/* ONE player for every cue on the page. Baba, 4.9.2026.
   The cues sit in the strip in front of the frames they describe, so a scene
   can have several and you always know which stretch the voice is about.
   Pressing a second cue stops the first: fifteen independent players means
   fifteen voices at once on the first impatient click. No progress bar, because
   the cues are short and a row of dead scrubbers down the page said nothing. */
(function(){
  var cues = [].slice.call(document.querySelectorAll('.gcue'));
  if (!cues.length) return;
  var au = new Audio(); au.preload = 'none';
  var now = null;
  function stop(){ if (now){ now.dataset.on = '0'; now = null; } }
  cues.forEach(function(c){
    c.addEventListener('click', function(){
      if (now === c && !au.paused){ au.pause(); c.dataset.on = '0'; return; }
      if (now === c && au.paused && au.currentTime > 0){ au.play(); c.dataset.on='1'; return; }
      if (now && now !== c) now.dataset.on = '0';
      now = c; au.src = c.dataset.src; au.currentTime = 0; c.dataset.on = '1';
      au.play().catch(function(){ stop(); });
    });
  });
  au.addEventListener('ended', stop);
  au.addEventListener('pause', function(){ if (now) now.dataset.on = '0'; });
})();
</script>"""


_fl = flow_of()
GUIDE = {g['anchor']: g for g in CAT.get('flow_guide', [])}
_done = sum(len(v) for v in _byscene.values())
# _done is the number of frames ON THIS PAGE, which is not the number drawn and
# never was. Two things separate them. 22 live keyframes carry storyboard=hide,
# because a shot with both a generated stand-in and a real footage composite
# shows one of them here and keeps the other for the scene page. And some of
# what is shown is a placeholder rather than artwork. Calling the total "drawn"
# overstated the work in one direction and understated it in the other, so all
# three numbers are stated instead of one doing a job it cannot do.
_live_kf = len([e for e in ENTRIES if e.get('kind') == 'keyframe'
                and e.get('status') != 'superseded'])
_holding = sum(1 for v in _byscene.values() for e in v
               if e.get('status') == 'placeholder')
_drawn = _done - _holding
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
    # 3.9.2026. Take two's master is a FILE and not a folder, which is why it
    # was never added here and why that loop was the only one on the site with
    # no download beside it.
    'clips/key-catch-2-loop.mp4':
        'https://drive.google.com/file/d/1HkTXJx_yDQ2k3grS7m7rI3gzeV7Ixztr/view',
}


# the whole fall, sky to hand. 15-3-A and 15-4-A carry the old modern key and
# are superseded by the FALL sequence.
LASTSHOT = [
    ('BB_C_15/15-1-B-v2.png', 'turning'),
    ('BB_C_15/15-2-A-v3.png', 'letting go'),
    ('BB_C_15/15-3-FALL-2-v1.png', 'released'),
    ('BB_C_15/15-3-FALL-3-v4.png', 'the boards behind it'),
    ('BB_C_15/15-3-FALL-4-v2.png', 'the room behind it'),
    ('BB_C_15/15-3-FALL-5-v1.png', 'the house behind it'),
    (('mp4', 'clips/key-catch-loop.mp4'), 'he catches it, take one'),
    # 3.9.2026. Two takes of the catch exist and both belong here, side by
    # side, so the choice between them is made by looking rather than by
    # remembering that a second one was shot. The 1.1 GB ProRes master
    # stays on Drive; this is the whole take at 480 wide.
    (('mp4', 'clips/key-catch-2-loop.mp4'), 'he catches it, take two'),
]


# the boards do not appear whole, they are written line by line. Six states
# each, and they are the phase: two finished boards on their own show none of
# the argument being made.
# THE THEORIES STRIP IS GONE. Baba, 4.9.2026: the boards are retired. Manan
# never writes anything; he thinks it and Viveka visualises it on the hologram
# that was already standing in the room. Two chalk boards in a room with a
# holographic display was one idea too many.
#
# This list named the frames BY PATH and the strip kept printing them after they
# were superseded, exactly like the arrival strip this afternoon and the COACH
# labels an hour ago. FIFTH TIME TODAY. A hardcoded literal does not know that
# anything has been retired, and the verifier is the only thing that catches it.
THEORIES = []
THEORY_LINES = {}


def theories_strip(prefix=''):
    return strip(THEORIES,
                 'Neither board arrives finished. Manan writes what he read, line by line, in white '
                 'chalk. Viveka answers on the whiteboard in black marker: same layout, same '
                 'three lines, same gauge, every value reversed. Six build states exist for each '
                 'board and the middle one is shown here.', prefix)


# THE ARRIVAL STRIP IS GONE. Baba, 4.9.2026: it showed the horizontal house,
# he is at the door, the door open, the door shut, and every one of those was
# replaced when the house went vertical. He arrives through the hip now. The
# frames were superseded in the catalogue but this list named them by PATH, so
# they kept printing on the front page regardless of their status, which is what
# a hardcoded list always does. The loop it also carried is a catalogued frame
# with a shot number now and appears at the end of the scene like any other.
ARRIVAL = []


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
                  'onclick="event.stopPropagation()">DOWNLOAD PRORES &nearr;</a>' % drive) if drive else ''
            _cb = os.path.basename(f[1]).rsplit('.', 1)[0]
            _card = '%scard/%s.html' % (prefix, _cb)
            _open = ('<a class=vid href="%s">' % _card) if os.path.exists(
                os.path.join(ROOT, 'mid', _cb + '.jpg')) else '<span class=vid>'
            _shut = '</a>' if _open.startswith('<a') else '</span>'
            out.append('<div class=f>%s'
                       '<video src="%s%s" autoplay muted loop playsinline preload=metadata '
                       'poster="%stiny/%s.jpg" disablepictureinpicture></video>'
                       '<span class=lbl>LOOP</span>%s'
                       '<div class=n>%s%s</div></div>'
                       % (_open, prefix, f[1], prefix, _cb, _shut, label.upper(), dl))
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
        # a frame may exist only as tiny/ and mid/ now: the watch folder uploads
        # the original to Drive and keeps it out of the repository.
        _b = os.path.basename(f).rsplit('.', 1)[0].replace(' ', '_')
        if not os.path.exists(os.path.join(ROOT, f)) and \
           not os.path.exists(os.path.join(ROOT, 'tiny', _b + '.jpg')):
            continue
        out.append('<div class=f><a href="%s"><img src="%s%s" alt="" loading=lazy></a>'
                   '<div class=n>%s</div>%s</div>'
                   % (full_link(f, prefix), prefix, small(f, 'tiny'), label.upper(),
                      theory_lines(f)))
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
                 'Viveka lets the key go and it falls through an empty frame. '
                 'His hand and Manan\u2019s are never on screen together, so nothing is composited '
                 'and the lighting difference between the drawing and the footage does not matter. '
                 'The key falls out of the sky, turning and growing, and the whole film replays behind it in '
       'reverse, so faint it is almost not there: the boards, the room, the house, and the avenue as '
       'it lands. It crosses from pencil to photograph on the way down, so no single frame is the '
       'moment it becomes real. THERE IS NO CUT ANYWHERE IN THIS. The camera never stops following '
       'the key. Viveka\u2019s hand leaves the top of the fall and Manan\u2019s arrives at the '
       'bottom of it, and the two of them never share a frame because a whole journey lies between '
       'them.', prefix)


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
      '<p class=lede>The whole film as a storyboard, in order. <b>%d frames drawn, %d holding as '
      'placeholders, %d keyframes live in all.</b> The count here is lower than the last because a '
      'shot with both a generated stand-in and a real footage composite shows one of them on this '
      'page and keeps the other for its scene page. Placeholders are shown on purpose, so what is '
      'still waiting is as visible as what is finished. This page is built from the catalogue, so '
      'it is current the moment anything is filed. Everything we have collected for each phase, '
      'kept and abandoned, is on <a href="brainstorm.html">brainstorm</a>.</p>'
      % (_drawn, _holding, _live_kf),
      # THE TWO DOCUMENTS, AT THE TOP, BESIDE THE TITLE. 2.9.2026. Anybody
      # arriving here wants one of two things: to understand the film, or to
      # animate it. One box each, before a single frame, so neither has to
      # scroll to find their own door.
      '<div class=twoup>'
      '<div class=srcbox><div class=t><b>The animator read through</b>'
      # 2.9.2026. NOT OFFERED WHILE IT IS OUT OF DATE. The running order was
      # rewritten five times today and the read through still carries the old
      # one, so downloading it would hand Kristijan a document that quietly
      # contradicts the page he is looking at. A file that is wrong is worse
      # than a file that is missing, because he cannot tell which to believe.
      '<span class=soon>COMING</span></div>'
      '<p><b>Every frame in order, with what it is, what it means and HOW IT MOVES:</b> the zoom, '
      'the push, the frottage, the passage through the surface. Made to print and mark up.</p>'
      '<p style="color:var(--dim)"><b>Not ready to download.</b> The running order changed today '
      'and this document has not caught up, so it is held back rather than handed over wrong. '
      'This page is the live one and is always current.</p>'
      '</div>'
      '<div class=srcbox><div class=t><b>Brain Brake, the book</b>'
      '<span><a class=dl href="https://markoboskoauroville.github.io/BRAIN_BRAKE_BOOK/" '
      'target=_blank rel=noopener>READ &nearr;</a></span></div>'
      '<p>The book the film was made from, written as though it came first. '
      '<b>%d words, fourteen chapters</b>, rooms described that the camera only passes and reasons '
      'given that two minutes can only imply. It reads itself aloud in two voices, about sixteen '
      'minutes, remembers where you stopped, and can follow the voice word by word on the page.</p>'
      '</div></div>' % 3106,
      '<div class=rtsheet>']
for e in _fl:
    n = str(e.get('n', ''))
    frames = []
    for sc in scenes_of(e):
        frames.extend(_byscene.get(sc, []))
    frames.sort(key=lambda f: shot_key(f.get('shot', '0')))
    live = n in ('2', '4', '5')
    # phases 8 and 11 both draw on scene 6, so its frames are split between them:
    # the corridor and the rooms are the journey, the control room is Viveka.
    # every shot number is unique again as of 31.8.2026, so no phase needs to
    # filter another phase's frames out of a shared folder
    # a phase whose frames are all photographs says so: calling footage "drawn"
    # was misleading on the one phase that was shot rather than drawn
    # the label says what the frames actually are. Calling a reference still
    # "drawn" hides that a phase is still waiting for its real material.
    # a hero frame is a photograph however it was made, so it counts as shot.
    # Calling it drawn told the animator to draw a phase that was filmed.
    shot = [f for f in frames if '/live/' in f.get('file', '')
            or 'HERO' in f.get('file', '')]
    ref  = [f for f in frames if f.get('status') == 'placeholder']
    drawn = [f for f in frames if f not in shot and f not in ref]
    bits = []
    if drawn: bits.append('%d drawn' % len(drawn))
    if shot:  bits.append('%d shot' % len(shot))
    if ref:   bits.append('%d reference' % len(ref))
    st = ', '.join(bits) if bits else ('LIVE ACTION' if live else 'NOT DRAWN YET')
    _g = GUIDE.get(n)
    # THE BUTTON MOVED INTO THE STRIP. Baba, 4.9.2026: the audio belongs in
    # front of the frames it is talking about, not in the heading, and a long
    # scene can carry several. A clip pinned to a PHASE NUMBER drifted the
    # moment the running order changed and he heard the freeze frame described
    # under the bicycle. A clip pinned to a FRAME cannot drift: it names the
    # picture it starts at, and if the picture moves the button moves with it.
    rt.append('<div class=rtph><span class=n>%s</span><h3>%s</h3>'
              '<span class=st>%s</span></div>' % (n, e.get('title', ''), st))
    # A SECTION CAN EXPLAIN ITSELF. 3.9.2026: the flow entries carried notes and
    # nothing printed them, so two beats Baba had written down were invisible on
    # the page: the frame freezing while Manan walks into it with a magnifying
    # glass, and him racing his own recorded ride until he collapses. The film is
    # a progression and the page was flattening it into a list of pictures.
    if e.get('note'):
        rt.append('<p class=lede>%s</p>' % e['note'])
    # the last shot is phase 15, so its sequence belongs here in the flow rather
    # than at the foot of the page
    # a frame shown in a strip is not listed again in the grid below it, but the
    # rest of the phase still is. Suppressing the whole grid hid the rooms of the
    # house and printed EMPTY boxes over them.
    in_strip = set()
    if n == '7':
        rt.append(arrival_strip())
        in_strip = {f for f, _ in ARRIVAL if isinstance(f, str)}
    # 3.9.2026. The boards were pinned to section 9, which is the MEETING, so the
    # film showed both theories on the board before the two men had spoken. They
    # belong to section 10, which is called THE TWO THEORIES, ON THE BOARD. The
    # same fault as the key strip and the credits filter: behaviour nailed to a
    # section NUMBER while the running order moved underneath it.
    if n == '13':
        # Baba, 31.8.2026: this phase shows the strip and nothing else.
        # 2.9.2026: it is section 13 now, 'He catches it'. It was pinned to 11,
        # which is the conclusion, so the whole key sequence was printing under
        # Viveka's goodbye. The other
        # live stills and drawn attempts are still on their card pages.
        rt.append(lastshot_strip())
        frames = []
    if n == '13' and os.path.exists(os.path.join(ROOT, 'assets3d', 'brain_break_key.obj')):
        rt.append(
            '<div class=srcbox><div class=t><b>The key in 3D</b>'
            '<span><a class=dl href="assets3d/brain_break_key_blender.py" download>DOWNLOAD SCRIPT</a>&nbsp;'
            '<a class=dl href="assets3d/brain_break_key.obj" download>DOWNLOAD OBJ</a></span></div>'
            '<p>The real key modelled from the photographs, one mesh with two materials: slot 0 '
            'polished brass, slot 1 flat drawn cream. The mesh never changes, only the surface, so '
            'the key crosses from the drawn world to the real one without a vertex moving. '
            'Both files in one folder, open Blender, Scripting tab, Run.</p></div>')
    if n == '14':
        # Baba, 1.9.2026: one representative frame for the credits, not eight.
        # 2.9.2026: this was pinned to section 12, which is the VORTEX DOWN now.
        # It filtered that section for frames with CREDITS in the name, found
        # none, and rendered the section empty while its two frames sat in the
        # catalogue. Sections are named things; pinning behaviour to a number
        # breaks the moment the running order changes, which it did four times
        # today.
        # a finished card with lettering, never the blank tall plate: the plate
        # is a working asset and shows nothing about what the credits look like.
        frames = [f for f in frames if 'CLOUD-v1' in f.get('file', '')
                  and 'PLATE' not in f.get('file', '')] or \
                 [f for f in frames if 'CREDITS' in f.get('file', '')][:1]
    # THE WORDS GO WITH THE PICTURE. Baba, 3.9.2026: Kristijan should never
    # have to ask anybody for anything, so the line, how it is read, a player
    # and the mp3 itself all sit on the page beside the frames of the shot they
    # belong to. He plays it where he stands or takes the file for the cut.
    #
    # The voice is the Hume actress and it is a STAND IN: Baba clones Manan's
    # own voice from these, so the download matters as much as the player. The
    # file is what gets used; the player only tells you which file you want.
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
            # A shot can carry several lines, because the arm beat is five
            # exchanges over one picture. The existing single line renderer above
            # stays for the shots that have one; this adds the rest under the
            # thumbnail as TEXT, which is what Kristijan needs. The audio lives
            # on its own page.
            for _d in (f.get('dialogue') or []):
                ln += ('<div class=ln><span class=sp>%s</span>'
                       '<span class=tx>“%s”</span></div>'
                       % (html.escape(_d.get('speaker', '')), html.escape(_d.get('line', ''))))
            _gc = GUIDE.get(b)
            if _gc:
                rt.append('<button class=gcue type=button data-src="%s" '
                          'title="listen: %s" aria-label="listen: %s">'
                          '<svg class=ic-p viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg>'
                          '<svg class=ic-s viewBox="0 0 24 24">'
                          '<path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>'
                          '<span>%s</span></button>'
                          % (_gc['url'], html.escape(_gc['label']),
                             html.escape(_gc['label']), html.escape(_gc['label'])))
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
# the passage. A vortex built out of keys, generated rather than modelled, so
# the shape can be tuned by changing four numbers rather than by rebuilding it
if os.path.exists(os.path.join(ROOT, 'assets3d', 'brain_brake_vortex.py')):
    _as.append(
        '<div class=srcbox><div class=t><b>The passage, a vortex of keys, for Blender</b>'
        '<span><a class=dl href="assets3d/brain_brake_vortex.py" download>DOWNLOAD SCRIPT</a>&nbsp;'
        '<a class=dl href="assets3d/brain_brake_vortex_guide.obj" download>DOWNLOAD GUIDE OBJ</a>&nbsp;'
        '<a class=dl href="assets3d/brain_brake_vortex_source.py" download>DOWNLOAD SOURCE</a></span></div>'
        '<p><b>Put the script, the guide and <code>brain_break_key.obj</code> in one folder, open '
        'Blender, Scripting tab, Run.</b> You get 432 keys laid along the spiral as linked '
        'instances of the one key mesh, the funnel as a wireframe guide that is hidden in render, '
        'and <b>VORTEX_CAM</b> already animated, 100 frames at 25 fps, flying from outside the '
        'mouth into the throat and rolling with the spiral. Animate the camera, not the keys.</p>'
        '<p>The shape is Viktor Schauberger\u2019s implosion vortex and two facts do all the work. '
        'The section is a <b>rectangular hyperbola, not a cone</b>, so the wall curves inward as it '
        'descends; Schauberger held the right form for a vortex chamber was the egg, which is a '
        'section through the hyperboloid of rotation. And the plan is <b>Kepler\u2019s harmonic '
        'spiral</b>, so successive turns come in to 1, 1/2, 1/3, 1/4 of the mouth radius and the '
        'turns tighten toward the centre. That is what pulls the eye in rather than leading it '
        'along. Mouth 7 m, throat 0.70 m, 26 m deep, ten turns. The keys scale with the local '
        'radius, so coverage rises from 1.2 keys deep at the mouth to 3.1 at the throat and the '
        'wall closes up on its own. Nothing is placed by hand.</p>'
        '<p><b>The keys in this shot are pencil and they are not gold.</b> Gold in this film means '
        'found, and Manan has not found the key yet when he goes through the passage. The script '
        'assigns a third material, <b>KEY_PENCIL</b>, flat paper white with no specular and a '
        'Freestyle outline, and deliberately uses neither the brass slot nor the drawn cream one. '
        'The first gold is the key at Viveka\u2019s neck and the last is the key falling.</p>'
        '<p style="color:var(--dim)">Four numbers at the top of the script control everything: '
        '<code>MOUTH_R</code>, <code>TURNS</code>, <code>DEPTH</code>, <code>KEYS_PER_TURN</code>. '
        'Reach for <code>KEYS_PER_TURN</code> first: raise it until the wall reads solid at your '
        'camera angle, lower it if the viewport crawls. The source file regenerates the guide with '
        'no Blender and no libraries, so the geometry can be checked in any package.</p></div>')
# the key as a 3D model, one mesh with two materials so it can cross from drawn
# to real without a vertex moving
if os.path.exists(os.path.join(ROOT, 'assets3d', 'brain_break_key.obj')):
    _as.append(
        '<div class=srcbox><div class=t><b>The key in 3D, for Blender</b>'
        '<span><a class=dl href="assets3d/brain_break_key_blender.py" download>DOWNLOAD SCRIPT</a>&nbsp;'
        '<a class=dl href="assets3d/brain_break_key.obj" download>DOWNLOAD OBJ</a>&nbsp;'
        '<a class=dl href="assets3d/brain_break_key_source.py" download>DOWNLOAD SOURCE</a></span></div>'
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
        '<span><a class=dl href="font/brain_break.ttf" download>DOWNLOAD TTF</a>&nbsp;'
        '<a class=dl href="font/brain_break.otf" download>DOWNLOAD OTF</a></span></div>'
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
               '<a class=dl href="%s" target=_blank rel=noopener>DOWNLOAD ON DRIVE &nearr;</a></div>'
               '<p><b>%s</b>%s</p><p>%s</p><p style="color:var(--dim)">%s</p></div>'
               % (_f['name'], _f['url'],
                  ('Phase %s, %s. ' % (_f['phase'], _f['phase_title'])) if _f.get('phase')
                  else (_f.get('phase_title', '') + '. '),
                  _f.get('codec', ''), _f.get('what', ''), _f.get('use', '')))
open(os.path.join(ROOT, 'footage.html'), 'w').write(
    page('Footage', ''.join(_fo), here='footage', depth=0))

open(os.path.join(ROOT, 'index.html'), 'w').write(
    page('%s, %s' % (FILM.title(), SUBTITLE), ''.join(rt) + GUIDE_JS,
         here='home', depth=0))

# ------------------------------------------------------------- the card pages
# One page per frame. A medium image, never the full one, the code on the left
# and a download on the right, the layers if there are any, and what the frame
# is doing. The full file is only ever reached by pressing download.
os.makedirs(os.path.join(ROOT, 'card'), exist_ok=True)
_order = [e for e in _kf]
# _kf is the STORYBOARD set: it drops superseded frames and anything carrying
# storyboard=hide. Cards were built from it alone, so 20 catalogued frames kept
# whatever card page an older build had left on disk and were never regenerated
# again. That is how 11 pages were still serving a top bar from before the
# GDRIVE fix, and the hidden set is exactly the real footage composites that
# assets, scene and breakdown pages link to, which is where the work is done.
# So every catalogued keyframe with a mid image gets a page. The extras are
# appended AFTER _order, so the prev/next chain over indices 0..len(_order)-1 is
# byte for byte what it was: the storyboard walk is unchanged and nobody
# navigates into a superseded frame by pressing next.
_extra = [e for e in ENTRIES
          if e.get('kind') == 'keyframe' and e not in _kf and e.get('file')
          and os.path.exists(os.path.join(
              ROOT, 'mid', os.path.basename(e['file']).rsplit('.', 1)[0].replace(' ', '_') + '.jpg'))]
_cards = _order + _extra
for _i, e in enumerate(_cards):
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
    # ONE lookup order for the whole site: originals, then Drive, then local.
    # This branch used to read DRIVE on its own, which is exactly how the card
    # path and the strip path drifted apart on 1.9 and put fourteen dead links
    # on the live site. It now reads the same tables in the same order as
    # full_link(), and it still needs the size, which is why it is not simply
    # a call to it.
    _b = os.path.basename(e['file'])
    _dv = ORIGINALS.get(_b) or DRIVE.get(_b)
    # STEP 86. A row with an empty url is a CLAIM, not a link: the chat session
    # writes {"bytes": 0, "url": ""} when it files a frame from the phone, and
    # something else fills it in later. So an empty url must fall through to
    # the local file, exactly as a missing row does. Testing the row for truth
    # rather than the url would have put href="" on every frame waiting in that
    # queue, which is worse than a heavy repository because it looks like a
    # link and does nothing.
    _dvu = '' if not _dv else (_dv if isinstance(_dv, str) else _dv.get('url', ''))
    if e.get('full'):
        _href = e['full']
        mb = e.get('full_bytes', 0) / 1048576.0
    elif _dvu:
        _href = _dvu
        mb = (_dv.get('bytes', 0) / 1048576.0) if isinstance(_dv, dict) else 0.0
    else:
        _href = '../' + e['file']
        _p = os.path.join(ROOT, e['file'])
        mb = (os.path.getsize(_p) if os.path.exists(_p) else 0) / 1048576.0
    # WHAT THE BUTTON PROMISES HAS TO BE TRUE. Baba, 3.9.2026: a video card was
    # offering DOWNLOAD FULL SIZE 63 KB, and 63 KB is the 480 wide proxy that
    # loops on the page. The full size is the ProRes master on Drive, 3840 by
    # 2160. A frame carrying full_label says what its master actually is, in
    # place of a byte count that would either read 0.0 MB or describe the wrong
    # file entirely.
    # DOWNLOAD, then WHAT it is, then the measurement. Every button on the site
    # is that shape now, so a frame says FULL SIZE and a clip says PRORES, and
    # nobody has to work out which of two buttons is the real file.
    _size = e.get('full_label') or ('FULL SIZE &nbsp;' + (
        ('%.0f KB' % (mb * 1024)) if 0 < mb < 1 else ('%.1f MB' % mb)))
    _ext = '' if e.get('full_label') else ' download'
    cd = ['<div class=cardhead><span class=code>%s</span>'
          '<a class=dl href="%s"%s>DOWNLOAD &nbsp;%s</a></div>'
          % (b.upper(), _href, _ext, _size)]
    if e.get('proxy_note'):
        _p = os.path.join(ROOT, e['file'])
        _pk = (os.path.getsize(_p) if os.path.exists(_p) else 0) / 1024.0
        cd.append('<div class=srcbox><div class=t><b>The loop on this page, 480 wide</b>'
                  '<a class=dl href="../%s" download>DOWNLOAD &nbsp;480 WIDE PROXY &nbsp;%.0f KB</a></div>'
                  '<p>%s</p></div>' % (e['file'], _pk, html.escape(e['proxy_note'])))
    # WHAT IS SAID OVER THIS SHOT. Baba, 4.9.2026: all dialogue must be clearly
    # seen under each shot where it appears. It was already under the thumbnails
    # on the flow page, but lines_of was written for the card page and then never
    # called, so the one place with room to print it in full printed nothing.
    _dl = lines_of(e)
    if _dl:
        cd.append('<div class=srcbox><div class=t><b>What is said over this shot</b></div>'
                  + _dl + '</div>')

    if e.get('video'):
        # A SHOT THAT MOVES IS STILL A SHOT. Baba, 3.9.2026: a loop should behave
        # like any drawn frame, so it gets a card, a note and a download in the
        # same places. The poster is a frame lifted out of the clip, so the box
        # is never empty while it loads.
        cd.append('<video class=cardimg src="../%s" autoplay muted loop playsinline '
                  'controls poster="../mid/%s.jpg"></video>' % (e['file'], b))
    else:
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

    # THE PLATES. Baba, 3.9.2026: the compositing animator needs the frame with
    # the live action taken out so he can lay the real Manan over the top, and
    # for the vortex he needs the boy on his own as well. They go on the card
    # beside the frame they belong to rather than in a folder, because a plate
    # that has to be hunted for gets rebuilt by hand instead.
    #
    # A list and not one entry, because a shot can need several: plate, actor
    # with alpha, actor on green. Each one is shown under the frame with its own
    # full size download, and the note says how it was made, since a matte you
    # cannot trust is worse than no matte.
    for _cp in (e.get('plates') or []):
        _cpb = _cp['file'].rsplit('.', 1)[0]
        _cpo = ORIGINALS.get(_cp['file']) or {}
        _cph = _cpo.get('url') or ('../' + _cpo.get('path', 'BB_C_1/' + _cp['file']))
        _cpmb = _cpo.get('bytes', 0) / 1048576.0
        cd.append('<div class=srcbox><div class=t><b>%s</b>'
                  '<a class=dl href="%s" download>DOWNLOAD FULL SIZE &nbsp;%.1f MB</a></div>'
                  '<p>%s</p></div>'
                  % (html.escape(_cp.get('label', 'Plate')), _cph, _cpmb,
                     html.escape(_cp.get('note', ''))))
        cd.append('<img class=cardimg src="../mid/%s.jpg" alt="">' % _cpb)

    if any(k in e.get('file', '') for k in ('FALL', '15-1-A', '15-2-A', 'OBJECT_SHEET_KEY',
                                            'CHARACTER_SHEET_COACH')):
        cd.append(
            '<div class=srcbox><div class=t><b>The key in 3D</b>'
            '<span><a class=dl href="../assets3d/brain_break_key_blender.py" download>DOWNLOAD SCRIPT</a>'
            '&nbsp;<a class=dl href="../assets3d/brain_break_key.obj" download>DOWNLOAD OBJ</a></span></div>'
            '<p>The same key as a mesh, with a brass material and a drawn one. Both files in one '
            'folder, open Blender, Scripting tab, Run.</p></div>')
    for src in (e.get('source') or []):
        cd.append('<div class=srcbox><div class=t><b>%s</b>'
                  '<a class=dl href="%s" target=_blank rel=noopener>DOWNLOAD ON DRIVE &nearr;</a></div>'
                  '<p>%s</p></div>'
                  % (src.get('name', 'source footage'), src['url'], src.get('note', '')))

    for a in (e.get('audio') or []):
        amb = size_of(a['file']) / 1048576.0
        cd.append('<div class=aud><div class=t><b>%s</b>'
                  '<span>%.1f s &nbsp;&middot;&nbsp; '
                  '<a class=dl href="../%s" download title="download the wav">DOWNLOAD &nbsp;WAV &nbsp;%.1f MB</a>'
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
                      '<a class=dl href="../%s" download>DOWNLOAD &nbsp;LAYER '
                      '&nbsp;%.1f MB</a></div></div>'
                      % (lb, L.get('name', lb).upper(), L['file'], lmb))
        cd.append('</div>')

    nav = []
    _instory = _i < len(_order)
    if _instory and _i > 0:
        pb = os.path.basename(_order[_i-1]['file']).rsplit('.', 1)[0].replace(' ', '_')
        nav.append('<a href="%s.html">&larr; %s</a>' % (pb, pb))
    nav.append('<a href="../index.html">all frames</a>')
    if _instory and _i < len(_order) - 1:
        nb = os.path.basename(_order[_i+1]['file']).rsplit('.', 1)[0].replace(' ', '_')
        nav.append('<a href="%s.html">%s &rarr;</a>' % (nb, nb))
    cd.append('<p class=lede style="margin-top:26px">%s</p>' % ' &nbsp;&middot;&nbsp; '.join(nav))
    # ---------------------------------------------------------- THE ID CARD
    # Baba, 2.9.2026. A frame's page answers four questions and it answers them
    # in this order: what it is, how it was made, what was tried and rejected,
    # and what it MEANS. The last one is the reason the page exists. An animator
    # who knows why a frame is in the film fixes things nobody specified; one
    # given only a picture and a filename does not.
    #
    # Every section reads from the catalogue, so filling one in is data and not
    # code, and an empty one SAYS it is empty rather than vanishing. A missing
    # section that disappears looks finished.
    _pr = (e.get('prompt') or '').strip()
    cd.append(idcard_block('The prompt it was made from',
              '<pre>%s</pre>' % html.escape(_pr) if _pr else
              'Not recorded. This frame predates prompts being kept in the catalogue, '
              'or it was made by hand.', dim=not _pr))

    _rf = e.get('refs') or []
    if _rf:
        _r = ['<div class=idrefs>']
        for _u in _rf:
            _r.append('<a href="%s" target=_blank rel=noopener><img src="%s" alt="" '
                      'loading=lazy><span>%s</span></a>'
                      % (_u, _u, html.escape(os.path.basename(_u))))
        _r.append('</div>')
        cd.append(idcard_block('The references it came from', ''.join(_r)))
    else:
        cd.append(idcard_block('The references it came from',
                  'Not recorded.', dim=True))

    _rej = rejected_takes(e)
    if _rej:
        _r = ['<div class=rej>']
        for _o in _rej:
            _ob = os.path.basename(_o['file']).rsplit('.', 1)[0].replace(' ', '_')
            _why = (_o.get('note') or '').strip()
            # A REJECTED TAKE CARRIES ITS OWN PROMPT. When the prompt changed
            # between takes, both are on the page, and the difference between
            # them is the most useful thing on the card: what was tried, what it
            # produced, and what fixed it. Without this the same wrong prompt
            # gets run again in three weeks by somebody who has only the final
            # picture and no idea what was already ruled out.
            _op = (_o.get('prompt') or '').strip()
            _same = _op and _op == (e.get('prompt') or '').strip()
            _r.append('<figure><span class=rejtag>REJECTED TAKE</span>'
                      '<a href="%s" target=_blank rel=noopener><img src="../%s" alt="" '
                      'loading=lazy></a><figcaption>%s<br>%s%s</figcaption></figure>'
                      % (full_link(_o['file'], '../'), small(_o['file']),
                         html.escape(os.path.basename(_o['file'])),
                         html.escape(_why[:150] + ('...' if len(_why) > 150 else '')),
                         ('<br><b>Same prompt as the accepted take.</b>' if _same else
                          ('<br><details><summary style="cursor:pointer;color:var(--gold)">'
                           'its own prompt</summary><pre style="font-size:11px">%s</pre></details>'
                           % html.escape(_op)) if _op else
                          '<br>Prompt not recorded.')))
        _r.append('</div>')
        cd.append(idcard_block('Rejected takes, kept on purpose',
                  ''.join(_r) + '<p style="color:var(--dim);margin:11px 0 0">A rejected take is '
                  'not rubbish. Some were rejected for one thing only, an aspect ratio or a '
                  'colour, and are the better drawing otherwise. They are here so a later '
                  'session can see what was tried before trying it again.</p>'))

    # ------------------------------------------------------------- THE DNA
    # Baba, 2.9.2026. Every frame is made of something older than itself, and
    # WINNING_FILM sets out what. Three strands, and an animator who has them
    # makes better decisions than one who has only the picture.
    #
    #   ELEMENT   which of the signs the frame is built on. From the book:
    #             threshold, stairs, light, glow, flame, ash, WATER, the hand,
    #             kneeling standing walking, bread, the bell, sacred space.
    #             Water is the one that is both the danger and the cure, which
    #             is why it is the most useful and the most easily overused.
    #   SYMBOL    what it carries without saying. Never explained on screen.
    #   COMPOSITION  how it is organised, and why THAT arrangement. Rule of
    #             thirds for a figure who must be seen inside a world. The
    #             spiral, which moves the eye rather than merely placing
    #             things. The pyramid for something unshakeable. Symmetry for
    #             calm and official, wrong for anything unstable. Full frame
    #             for one subject and nothing else. Diagonals carry energy,
    #             horizontals carry rest.
    #
    # The book also says the structure should CHANGE across a film, because a
    # rule applied identically for two minutes stops being structure and
    # becomes wallpaper. Recording the composition per frame is what makes that
    # checkable rather than a hope.
    _dna = e.get('dna') or {}
    if _dna:
        _rows = []
        # WHERE IN THE FILM and WHERE IN THE JOURNEY come first, because they
        # are the two things that decide how long a frame holds, and an animator
        # who knows a frame is the crossing rather than a test will hold it
        # longer without being asked. See MANTRA_MANIFEST/modules/hero-journey.md.
        for _k, _lab in (('phase', 'Phase'), ('journey', 'Hero\u2019s journey'),
                         ('element', 'Element'), ('symbol', 'Symbol'),
                         ('composition', 'Composition'), ('balance', 'Balance')):
            _v = (_dna.get(_k) or '').strip()
            if _v:
                _rows.append('<p><b style="color:var(--gold)">%s.</b> %s</p>'
                             % (_lab, html.escape(_v)))
        cd.append(idcard_block('The DNA of this frame', ''.join(_rows)))
    else:
        cd.append(idcard_block('The DNA of this frame',
                  'Not set down yet. Every frame is built on an element, carries a symbol and uses '
                  'a composition, and WINNING_FILM says which ones exist. Until this is filled in, '
                  'the animator is working from the picture alone.', dim=True))

    # ------------------------------------------------------------- THE MUSIC
    # Baba, 2.9.2026. Two prompts, not one. The SCENE BED is the piece the whole
    # scene is written in, and it does not restart at every cut. The SHOT
    # ARRANGEMENT is the same piece with the instrumentation changed, so the
    # music follows the picture without the audience noticing an edit.
    #
    # Instruments come from the ELEMENT, which is why the DNA is above this and
    # not below it. Air is breath instruments, bansuri and low flutes. Water is
    # anything poured or bowed. The crown, at Viveka, is crystal, bells and
    # chime, because that is what the top of the head sounds like. A frame's
    # element decides what plays; a frame's stage in the journey decides how much
    # of it plays.
    _su = e.get('suno') or {}
    if _su:
        _m = []
        if _su.get('scene'):
            _m.append('<p><b style="color:var(--gold)">The scene bed.</b> One piece under the whole '
                      'scene. It does not restart at a cut.</p><pre>%s</pre>'
                      % html.escape(_su['scene'].strip()))
        if _su.get('shot'):
            _m.append('<p style="margin-top:15px"><b style="color:var(--gold)">This shot.</b> The '
                      'same piece, re-arranged. Change the instruments, never the key or the '
                      'tempo.</p><pre>%s</pre>' % html.escape(_su['shot'].strip()))
        if _su.get('why'):
            _m.append('<p style="margin-top:13px;color:var(--dim)">%s</p>'
                      % html.escape(_su['why'].strip()))
        cd.append(idcard_block('The music, for Suno', ''.join(_m)))
    else:
        cd.append(idcard_block('The music, for Suno',
                  'Not written yet. Every shot needs two: the scene bed it sits in, and this shot\u2019s '
                  'own arrangement of it. The instruments come from the element in the DNA above.',
                  dim=True))

    _mn = (e.get('meaning') or '').strip()
    cd.append(idcard_block('What it means, and what it does',
              html.escape(_mn).replace('\n\n', '</p><p>').join(['<p>', '</p>']) if _mn else
              'Not written yet. This frame needs its meaning set down: where it sits in the film, '
              'what it carries, how it moves the story on, and what it is doing to the audience. '
              'Ask before animating it rather than guessing from the picture.', dim=not _mn))

    open(os.path.join(ROOT, 'card', b + '.html'), 'w').write(
        page(b, ''.join(cd), here='home', depth=1))

# ---------------------------------------------------------------------------
# THE SHEETS PAGE. Baba, 4.9.2026: characters and props, in one place, at the
# top of the site.
#
# A sheet is what somebody opens BEFORE drawing anything: the turnaround that
# says what a character looks like from three sides, the prop sheet that says
# what an object does when it turns. They were scattered across scene folders
# with storyboard=hide, which kept them off the storyboard correctly and also
# made them unfindable unless you already knew they existed.
#
# Live sheets first, retired ones after, because a retired sheet is still the
# reason a design looks the way it does and deleting it loses the argument.
# THE SHEETS COME FROM THE CATALOGUE NOW. Baba, 5.9.2026: the page was showing
# Coach Brain, his desk, his wall of switches and his chair, all of which belong
# to a character and a room that no longer exist. It was a hardcoded list, so
# retiring a sheet in the catalogue changed nothing here. Sixth time today that
# a literal outlived what it pointed at.
#
# A SHEET SHOWS ONLY WHILE IT IS LIVE. Superseded ones are not listed at all,
# not even under a "retired" heading: this page is what somebody opens before
# drawing, and an outdated turnaround on it is worse than a missing one because
# it will get used.
_SHEETS = [(g['group'], g['files']) for g in CAT.get('sheets', [])]


def sheets_page():
    o = ['<h1>Characters and props</h1>',
         '<p class=lede>The turnarounds and the object studies, which is what you open BEFORE '
         'drawing anything. <b>A sheet says what a thing looks like from every side, so nobody '
         'has to guess twice.</b> Only sheets that are in the film are here. A retired one is '
         'still in the archive with the reason it went, but it is not on this page, because an '
         'outdated turnaround gets used.</p>']
    for title, items in _SHEETS:
        rows = []
        for f in items:
            ent = next((x for x in ENTRIES
                        if os.path.basename(x.get('file', '')) == f), None)
            if not ent or ent.get('status') == 'superseded':
                continue
            what = ent.get('title') or f
            b = f.rsplit('.', 1)[0].replace(' ', '_')
            if not os.path.exists(os.path.join(ROOT, 'mid', b + '.jpg')):
                continue
            card = 'card/%s.html' % b
            href = card if os.path.exists(os.path.join(ROOT, card)) else (
                (ORIGINALS.get(f) or {}).get('url', '#'))
            rows.append('<a class=sh href="%s"><img src="mid/%s.jpg" alt="" loading=lazy>'
                        '<span>%s</span></a>' % (href, b, html.escape(what)))
        if rows:
            o.append('<div class=rtph><span class=n>&#9679;</span><h3>%s</h3>'
                     '<span class=st>%d sheets</span></div>' % (title, len(rows)))
            o.append('<div class=sheetgrid>' + ''.join(rows) + '</div>')
    return ''.join(o)


open(os.path.join(ROOT, 'sheets.html'), 'w').write(
    page('Characters and props', sheets_page(), here='sheets', depth=0))


# ---------------------------------------------------------------------------
# THE SOUND PAGE. Baba, 5.9.2026: the scratch track lives on the site, so the
# sound choices are one click away instead of a list in a chat.
#
# DATA FIRST. Entries live in catalog.json under 'sound' and this page is
# generated from them, the same as everything else here. Claude Code adds what
# he has listened to; he never edits HTML.
#
# EVERY ENTRY HAS BEEN HEARD. A generator whose name sounds right and turns out
# wrong is worse than an empty list, because somebody trusts it and cuts to it.
SOUND_JS = """<script>
/* Arrow through the ten sliders without touching a URL. The links already carry
   the solo, so the arrows just click the next one and remember where you are
   per scene. Everything lands in the window named mynoise, so it never spawns
   tabs. */
(function(){
  document.querySelectorAll('.solorow').forEach(function(row){
    var solos = [].slice.call(row.querySelectorAll('.solo'));
    var at = -1;
    function go(i){
      if (!solos.length) return;
      at = (i + solos.length) % solos.length;
      solos.forEach(function(s, j){ s.classList.toggle('on', j === at); });
      window.open(solos[at].href, 'mynoise');
    }
    solos.forEach(function(s, j){
      s.addEventListener('click', function(){ at = j;
        solos.forEach(function(x, k){ x.classList.toggle('on', k === j); }); });
    });
    row.querySelectorAll('.nav').forEach(function(b){
      b.addEventListener('click', function(){ go(at + (+b.dataset.d)); });
    });
  });
})();
</script>"""


DIALOGUE_JS = """<script>
/* Copy the whole speech, and say so. The text is on the button as a data
   attribute so nothing has to be scraped out of the DOM and no selection is
   involved. execCommand is the fallback for browsers without the clipboard API
   or without a secure context. */
document.querySelectorAll('.cp').forEach(function(b){
  b.addEventListener('click', function(){
    var t = b.dataset.t;
    function done(){
      var old = b.textContent; b.textContent = 'COPIED'; b.classList.add('done');
      setTimeout(function(){ b.textContent = old; b.classList.remove('done'); }, 1400);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(t).then(done, fallback);
    } else { fallback(); }
    function fallback(){
      var a = document.createElement('textarea');
      a.value = t; a.style.position = 'fixed'; a.style.opacity = '0';
      document.body.appendChild(a); a.select();
      try { document.execCommand('copy'); done(); } catch(e) {}
      document.body.removeChild(a);
    }
  });
});
</script>"""


SOUND = CAT.get('sound', {})


def _solo(level_index, m, title):
    """One custom.php URL with a single slider at full and the rest at zero.

    l= is TEN two digit slider levels. 99 is full, 00 is off. So soloing is a
    string, not a drag: the whole recording session is ten URLs and one m=
    string, and m= is the mix, so keeping it makes any scene reproducible.
    """
    lv = ['00'] * 10
    if level_index is not None:
        lv[level_index] = '99'
    elif level_index is None:
        lv = ['50'] * 10
    return ('https://mynoise.net/NoiseMachines/custom.php?l=%s00&orig=k&m=%s&title=%s'
            % (''.join(lv), m, urllib.parse.quote(title)))


def _all(level, m, title):
    return ('https://mynoise.net/NoiseMachines/custom.php?l=%s00&orig=k&m=%s&title=%s'
            % (level * 10, m, urllib.parse.quote(title)))


def sound_page():
    o = ['<h1>Sound</h1>',
         '<p class=lede>%s</p>' % html.escape(SOUND.get('about', ''))]

    kw = {str(k['phase']): k for k in (SOUND.get('keywords') or [])}
    demo = SOUND.get('demo') or {}
    ph = SOUND.get('phases') or {}

    for e in sorted([x for x in ENTRIES if x.get('kind') == 'flow'],
                    key=lambda x: int(x['n'])):
        n = str(e['n'])
        k = kw.get(n)
        if not k and n not in ph:
            continue
        o.append('<div class=rtph><span class=n>%s</span><h3>%s</h3>'
                 '<span class=st>%s</span></div>'
                 % (n, html.escape(e.get('title', '')),
                    'mix ready' if (ph.get(n) or (demo.get('phase') == n)) else 'no mix yet'))
        if k:
            o.append('<div class=srcbox><div class=t><b>Keywords</b>'
                     '<span class=kw>%s</span></div>'
                     '<p>Type these three into the Not an AI box, press Surprise Me, and the mix '
                     'comes back in the address bar. If they are wrong, try: <b>%s</b></p></div>'
                     % (' &nbsp;&middot;&nbsp; '.join(html.escape(w) for w in k['words']),
                        ' &middot; '.join(html.escape(w) for w in k.get('alt', []))))
        mix = (ph.get(n) or {}).get('mix') or (demo if demo.get('phase') == n else None)
        if mix:
            m, title = mix['m'], mix.get('title', 'scene ' + n)
            btns = ['<a class=sbtn target=mynoise href="%s">ALL UP</a>' % _all('99', m, title),
                    '<a class=sbtn target=mynoise href="%s">HALF</a>' % _all('50', m, title)]
            for i in range(10):
                btns.append('<a class="sbtn solo" target=mynoise href="%s">%d</a>'
                            % (_solo(i, m, title), i + 1))
            o.append('<div class=solorow data-scene="%s">%s'
                     '<button class="sbtn nav" type=button data-d="-1">&#9664;</button>'
                     '<button class="sbtn nav" type=button data-d="1">&#9654;</button>'
                     '</div>' % (n, ''.join(btns)))
            if demo.get('phase') == n and not ph.get(n):
                o.append('<p class=lede style="opacity:.7">%s</p>'
                         % html.escape(demo.get('note', '')))
        for it in (ph.get(n, {}).get('sounds') or []):
            u = it.get('url', '#')
            j = '&' if '?' in u else '?'
            o.append('<div class=srcbox><div class=t><b>%s</b></div><p>%s</p>'
                     '<div class=solorow>' % (html.escape(it.get('name', '')),
                                              html.escape(it.get('why', ''))))
            o.append('<a class=sbtn target=mynoise href="%s%sl=%s00">ALL UP</a>'
                     % (u, j, '99' * 10))
            o.append('<a class=sbtn target=mynoise href="%s%sl=%s00">HALF</a>'
                     % (u, j, '50' * 10))
            for i in range(10):
                lv = ['00'] * 10; lv[i] = '99'
                o.append('<a class="sbtn solo" target=mynoise href="%s%sl=%s00">%d</a>'
                         % (u, j, ''.join(lv), i + 1))
            o.append('<button class="sbtn nav" type=button data-d="-1">&#9664;</button>'
                     '<button class="sbtn nav" type=button data-d="1">&#9654;</button>'
                     '</div></div>')

    src = SOUND.get('sources') or []
    if src:
        o.append('<div class=rtph><span class=n>&#9679;</span><h3>WHERE THESE COME FROM</h3>'
                 '<span class=st>%d</span></div>' % len(src))
        o.append('<div class=lay>')
        for sn in src:
            o.append('<div class=l><div class=n><span><a href="%s" target=mynoise>%s</a></span>'
                     '<span class=t>%s</span></div></div>'
                     % (sn.get('url', '#'), html.escape(sn.get('name', '')),
                        html.escape(sn.get('note', ''))))
        o.append('</div>')
    return ''.join(o) + SOUND_JS


open(os.path.join(ROOT, 'sound.html'), 'w').write(
    page('Sound', sound_page(), here='sound', depth=0))


# ---------------------------------------------------------------------------
# THE DIALOGUE PAGE. Baba, 5.9.2026: he needs to copy lines into other apps and
# selecting text on a phone is miserable.
#
# ONE BLOCK PER SPEAKER RUN. Consecutive lines by the same character are one
# block with one copy button, because that is the unit somebody actually pastes:
# a whole speech, not a sentence. A new block starts the moment the speaker
# changes.
#
# The frame the lines play over is beside them at a third of the width, so it is
# obvious which moment is being copied. Grouped by scene, in film order.
def dialogue_page():
    o = ['<h1>Dialogue</h1>',
         '<p class=lede>Every spoken line, grouped by who says it, with the frame it plays over. '
         '<b>Press COPY and the whole speech goes to the clipboard</b>, ready to paste. Consecutive '
         'lines by one character are one block, because that is what you actually paste.</p>']
    rows = [e for e in ENTRIES
            if e.get('dialogue') and e.get('status') == 'accepted']
    rows.sort(key=shot_key)
    scenes = {}
    for e in rows:
        scenes.setdefault(str(e.get('scene', '')), []).append(e)
    for sc in sorted(scenes, key=lambda x: (len(x), x)):
        title = SCENES.get(sc, '')
        n = sum(len(e['dialogue']) for e in scenes[sc])
        o.append('<div class=rtph><span class=n>%s</span><h3>%s</h3>'
                 '<span class=st>%d lines</span></div>'
                 % (html.escape(sc), html.escape(title), n))
        for e in scenes[sc]:
            b = os.path.basename(e['file']).rsplit('.', 1)[0]
            runs, cur = [], None
            for d in e['dialogue']:
                if cur is None or d['speaker'] != cur['who']:
                    cur = {'who': d['speaker'], 'lines': []}
                    runs.append(cur)
                cur['lines'].append(d['line'])
            # THE PICTURE APPEARS ONCE PER FRAME, not once per speech. Repeating
            # it under every line pushed one exchange down three screens and
            # gave a two word answer a full size still.
            whole = '\n\n'.join('%s\n%s' % (r['who'], '\n'.join(r['lines'])) for r in runs)
            speech = []
            for r in runs:
                speech.append('<div class=sp>'
                              '<div class=spn><span class=who>%s</span>'
                              '<button class=cp type=button data-t="%s">COPY</button></div>%s</div>'
                              % (html.escape(r['who']), html.escape('\n'.join(r['lines'])),
                                 ''.join('<p>%s</p>' % html.escape(l) for l in r['lines'])))
            o.append('<div class=dlg>'
                     '<div class=dh><span class=frm>%s</span>'
                     '<span class=ttl>%s</span>'
                     '<button class=cp type=button data-t="%s">COPY THE WHOLE SCENE</button></div>'
                     '<div class=db><a class=dpic href="card/%s.html">'
                     '<img src="mid/%s.jpg" alt="" loading=lazy></a>'
                     '<div class=dtx>%s</div></div></div>'
                     % (html.escape(b), html.escape(e.get('title', '')),
                        html.escape(whole), b, b, ''.join(speech)))
    return ''.join(o) + DIALOGUE_JS


open(os.path.join(ROOT, 'dialogue.html'), 'w').write(
    page('Dialogue', dialogue_page(), here='dialogue', depth=0))

print('  %d card pages, %d on the storyboard walk' % (len(_cards), len(_order)))

# ------------------------------------------------- sweep this build's own litter
# 2.9.2026. A page that is no longer generated does not disappear, it keeps
# being served. Six card pages and one shot page were still live from an older
# catalogue, pointing at originals that exist in no repository and on no drive,
# and they had survived every rebuild since. verify_site.py found them; this
# stops them coming back.
#
# Deliberately narrow. Only the three name shapes this file owns completely,
# card/NAME.html, BB_C_n/shot-N-N.html and BB_C_n/NAME_breakdown.html, so
# nothing hand made and nothing from another tool is ever in range.
_kept = {os.path.basename(x['file']).rsplit('.', 1)[0].replace(' ', '_') + '.html'
         for x in _cards}
_swept = []
for _f in glob.glob(os.path.join(ROOT, 'card', '*.html')):
    if os.path.basename(_f) not in _kept:
        os.remove(_f)
        _swept.append(os.path.relpath(_f, ROOT))
# Shot pages are NOT swept by rule. The first attempt derived the live set from
# entry.shot and deleted seven pages the build then wrote again, so two runs in
# a row never agreed. A sweep that is not idempotent is worse than no sweep: it
# churns the repository and hides real changes in the diff. Only the two shapes
# that can be derived EXACTLY from what was just written are swept.
for _d in glob.glob(os.path.join(ROOT, 'BB_C_*')):
    for _f in glob.glob(os.path.join(_d, '*_breakdown.html')):
        _b = os.path.basename(_f)[:-len('_breakdown.html')] + '.html'
        if _b not in _kept:
            os.remove(_f)
            _swept.append(os.path.relpath(_f, ROOT))
if _swept:
    print('  swept %d page(s) this build no longer generates:' % len(_swept))
    for _f in sorted(_swept):
        print('     %s' % _f)

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
for n in sorted(SCENES, key=_phkey):
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
    # TRAY is written for pages one directory down, which is where it is used
    # everywhere except here. breakdown.html sits at the root, so every ../ in it
    # climbs out of the repository entirely and lands on markoboskoauroville.github.io.
    # The portrait was the only casualty and it 404'd on the live site. Both
    # paths are rewritten now, the deeper one first so it is not shadowed by the
    # shorter match.
    b.append((TRAY % ('the frame', 'The frame')).replace("EMAILADDR", EMAIL)
             .replace('../mid/marko.png', 'mid/marko.png')
             .replace('../marko.png', 'marko.png'))
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
