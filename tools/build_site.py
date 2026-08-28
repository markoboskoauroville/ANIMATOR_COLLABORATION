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
ENTRIES = CAT['entries']
PASS = 'kristijan'

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
:root{--paper:#f2ebda;--ink:#221f19;--dim:#8a8170;--rule:#cdbfa4;--brass:#9C7A31;--box:#e6dcc4;--slate:#20241f}
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
.bar .sp{flex:1}
.bar a.drive{color:#e0b45f;margin-left:8px;white-space:nowrap}
.bar a.drive:hover{color:#fff}
.wrap{max-width:1500px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:30px;letter-spacing:-.01em;margin:8px 0 6px}
h2{font-size:19px;margin:38px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--rule)}
.lede{max-width:760px;color:#4a453b}
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
.tag{font:600 10px ui-monospace,monospace;letter-spacing:.08em;color:#fff;
 padding:2px 7px;border-radius:2px;margin-left:6px;text-transform:uppercase}
.note{font-size:13px;line-height:1.5;color:#4a453b;margin:5px 0 0}
.bd{display:inline-block;margin-top:7px;font:600 11px ui-monospace,monospace;
 letter-spacing:.06em;text-transform:uppercase}
.log{max-width:880px}
.log .it{border-top:1px solid var(--rule);padding:13px 0}
.log .d{font:11px ui-monospace,monospace;color:var(--dim)}
.doc{display:flex;gap:20px;border-top:1px solid var(--rule);padding:20px 0;max-width:1000px}
.doc img{width:230px;border:1px solid var(--rule);background:#fff;flex:none}
.lay{display:flex;gap:18px;align-items:flex-start;border-top:1px solid var(--rule);padding:16px 0}
.lay img{width:260px;border:1px solid var(--rule);
 background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 50%/18px 18px}
.lay .n{font:600 13px ui-monospace,monospace}
.lay .s{font:11px ui-monospace,monospace;color:var(--dim);margin:3px 0 6px}
.gate{position:fixed;inset:0;background:var(--paper);z-index:99;
 display:flex;align-items:center;justify-content:center}
.gate form{text-align:center}
.gate input{font:16px ui-monospace,monospace;padding:10px 14px;border:1px solid var(--rule);
 background:#fff;width:230px}
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


def bar(here, r):
    """An invisible table. Home and documentation left, the scenes in the middle,
    and the last cell is always Google Drive, hard right."""
    o = ['<div class=bar><a class=home href="%sindex.html">BRAIN BRAKE</a>' % r,
         '<a href="%sdocumentation.html"%s>DOCUMENTATION</a>'
         % (r, ' class=on' if here == 'doc' else ''), '<span class=sp></span>']
    for n in sorted(SCENES, key=int):
        o.append('<a href="%sBB_C_%s/index.html"%s>SC%s</a>'
                 % (r, n, ' class=on' if here == n else '', n))
    o.append('<span class=sp></span>')
    o.append('<a class=drive href="%s" target=_blank rel=noopener>GDRIVE &nearr;</a>' % DRIVE)
    o.append('</div>')
    return ''.join(o)


def page(title, body, here=None, depth=0):
    r = '../' * depth
    return ('<!doctype html><html lang=en><head><meta charset=utf-8>'
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            '<title>%s</title><style>%s</style></head><body>%s'
            '<div id=app style="display:none">%s<div class=wrap>%s</div></div></body></html>'
            % (title, CSS, GATE, bar(here, r), body))


def tag(st):
    return '<span class=tag style="background:%s">%s</span>' % (STATUS.get(st, '#8a8170'), st)


def frames_of(scene):
    return [e for e in ENTRIES if e.get('kind') == 'frame'
            and e.get('frame', '').split('.')[0] == str(scene)]


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
    b = ['<h1>Scene %s &nbsp;<span style="color:#8a8170;font-weight:400">%s</span></h1>'
         % (n, SCENES[n])]
    if not fs:
        b.append('<p class=lede>Nothing here yet.</p>')
    else:
        b.append('<p class=lede>%d %s. Click a picture to open it at full size.</p>'
                 % (len(fs), 'frame' if len(fs) == 1 else 'frames'))
        for i in range(0, len(fs), 5):
            b.append('<div class=row>')
            for e in fs[i:i + 5]:
                lay = layers_of(e)
                bd = ('<a class=bd href="%s_breakdown.html">Breakdown &rarr;</a>'
                      % os.path.splitext(os.path.basename(e['file']))[0]) if lay else ''
                b.append('<div class=cell><a href="../%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s'
                         '<p class=note>%s</p>%s</div></div>'
                         % (e['file'], e['file'], e.get('frame', ''),
                            tag(e.get('status', 'proposal')),
                            e.get('note', 'note pending'), bd))
            b.append('</div>')
    open(os.path.join(ROOT, 'BB_C_%s' % n, 'index.html'), 'w').write(
        page('Scene %s' % n, ''.join(b), here=n, depth=1))

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
            rows.append('<div class=lay><a href="../%s"><img src="../%s" alt=""></a><div>'
                        '<div class=n>%s</div><div class=s>%s &nbsp;·&nbsp; %s</div>'
                        '<a href="../%s" download>Download</a></div></div>'
                        % (p, p, os.path.basename(p), dims(p), human(size_of(p)), p))
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
open(os.path.join(ROOT, 'documentation.html'), 'w').write(
    page('Documentation', ''.join(b), here='doc', depth=0))

b = ['<h1>THE BRAIN BRAKE</h1>',
     '<p class=lede>A two minute film for the Breakthrough Junior Challenge. A fourteen year old '
     'asks why a runner with nothing left can still find one more sprint. Everything here is for '
     'the animation.</p>',
     '<div class=rules><b>The artwork runs edge to edge and has no panel border.</b> '
     'The frame is yours to add as its own layer, so it can move, animate or come off.<br>'
     'Everything is <b>2731 x 1536</b>, true 16:9. Key light is <b>camera right</b>, always.<br>'
     'Nothing here is in the film until Marko says so. The status under each picture says where it '
     'stands.<br>Video files are on <b>GDrive</b>, top right of every page.</div>',
     '<h2>Scenes</h2><ul class=scenes>']
for n in sorted(SCENES, key=int):
    c = len(frames_of(n))
    b.append('<li><a href="BB_C_%s/index.html"><span class=n>SC%s</span>'
             '<span class=t>%s</span><span class=c>%s</span></a></li>'
             % (n, n, SCENES[n], '%d frames' % c if c else 'nothing yet'))
b.append('</ul><h2>What changed</h2><div class=log>')
for e in sorted(ENTRIES, key=lambda x: x.get('date', ''), reverse=True):
    who = e.get('frame') or os.path.basename(e['file'])
    b.append('<div class=it><span class=fid>%s</span>%s<div class=d>%s</div>'
             '<p class=note>%s</p></div>'
             % (who, tag(e.get('status', 'proposal')), e.get('date', ''),
                e.get('note', 'note pending')))
b.append('</div>')
open(os.path.join(ROOT, 'index.html'), 'w').write(page('The Brain Brake', ''.join(b), depth=0))

print('built: landing, documentation, %d scene pages' % len(SCENES))
