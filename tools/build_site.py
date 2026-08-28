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
.prev{border-radius:7px;overflow:hidden;background:#0e0d0a;margin:34px 0 96px;display:none;
 box-shadow:0 6px 26px rgba(0,0,0,.28)}
.prev.on{display:block}
.prev h3{margin:0;padding:9px 14px;background:#1b1a15;border-bottom:1px solid #2b2921;
 font:600 11px ui-monospace,monospace;letter-spacing:.09em;color:#8d8574;
 display:flex;align-items:center;gap:8px}
.prev h3 .dots{display:flex;gap:6px;margin-right:6px}
.prev h3 i{width:10px;height:10px;border-radius:50%;display:block}
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
.prev .acts .go:hover{color:#17150f}
.prev .acts .go.off{opacity:.35;pointer-events:none}
.tray .go{background:var(--brass);color:#17150f}
.tray .cp{background:none;color:#c9bfa4;border:1px solid #3a352b}
.ask{background:var(--box);border-left:3px solid var(--brass);padding:13px 18px;
 margin:18px 0 24px;max-width:880px;font-size:14px;color:var(--body)}
.log{max-width:880px}
.log .it{border-top:1px solid var(--rule);padding:13px 0}
.log .d{font:11px ui-monospace,monospace;color:var(--dim)}
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
  <h3><span class=dots><i style="background:#e0655a"></i><i style="background:#e0b45f"></i><i style="background:#6fa86a"></i></span>
  email composer &nbsp;·&nbsp; %s</h3>
  <pre id=pv></pre>
  <div class=acts>
    <a class=who id=who href="#" title="open this in your mail app">
      <img src="../marko.png" alt="">
      <span><span class=n>Marko</span><br><span class=e>EMAILADDR</span></span>
    </a>
    <span class=sep></span>
    <button onclick="cp()" id=cpb>copy the whole message</button>
    <button onclick="cpa()" id=cab>copy just the address</button>
  </div>
</div>
<div class=tray id=tray>
  <span id=sum></span>
  <span class=sp></span>
  <a class=go id=go href="#">go to the composer</a>
</div>
<script>
var NL=String.fromCharCode(10);
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
  document.getElementById('tray').className='tray'+((b.length+m.length)?' on':'');

  var any=(b.length+m.length)>0;
  var subj=[];
  if(b.length) subj.push('breakdown '+b.map(function(x){return x.dataset.f;}).join(', '));
  if(m.length) subj.push('modification '+m.map(function(x){return x.dataset.f;}).join(', '));
  var subject='%s request: '+subj.join('; ');
  var href='mailto:EMAILADDR?subject='+encodeURIComponent(subject)
    +'&body='+encodeURIComponent(text()+NL+NL+location.href);

  // the preview at the foot of the page, live as he ticks
  var pv=document.getElementById('pv'), pr=document.getElementById('prev');
  pr.className='prev'+(any?' on':'');
  if(any){
    var esc=function(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;');};
    pv.innerHTML='<b>To:</b>      EMAILADDR'+NL+'<b>Subject:</b> '+esc(subject)+NL+NL
      +esc(text())+NL+NL+esc(location.href)+'<span class=cur> </span>';
  }

  var g1=document.getElementById('go');
  if(g1){ g1.href='#prev'; g1.style.opacity=1; g1.style.pointerEvents='auto'; }
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
    o = ['<div class=bar><a class=home href="%sindex.html">BRAIN BRAKE</a>' % r,
         ('<span class=vb>%s</span>' % VERSION) if VERSION else '',
         '<a href="%sdocumentation.html"%s>DOCUMENTATION</a>'
         % (r, ' class=on' if here == 'doc' else ''),
         ('<a class=rt href="%s%s" target=_blank rel=noopener '
          'title="the whole film, four panels to a page">READ THROUGH &darr;</a>'
          % (r, READTHROUGH)) if READTHROUGH else '',
         '<span class=sp></span>']
    for n in sorted(SCENES, key=int):
        o.append('<a href="%sBB_C_%s/index.html"%s>SC%s</a>'
                 % (r, n, ' class=on' if here == n else '', n))
    o.append('<span class=sp></span>')
    o.append('<a class=drive href="%s" target=_blank rel=noopener>GDRIVE &nearr;</a>' % DRIVE)
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
            '<div id=app style="display:none">%s<div class=wrap>%s</div></div></body></html>'
            % (title, r, r, r, r, CSS, GATE, bar(here, r), body))


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


def overlays_of():
    """Things that sit on top of every frame rather than belonging to one scene.
    The panel border is the first: the artwork ships edge to edge and this is the
    frame, as its own transparent layer."""
    # only the current one gets the section. Retired ones stay reachable in the
    # What changed log below, with their note and their link, because nothing is deleted.
    return [e for e in ENTRIES if e.get('kind') == 'overlay'
            and e.get('status') != 'superseded']


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
    b.append('<div class=ask><b>Breakdowns are made on request.</b> A frame is delivered flat '
             'unless you ask for it to be split into background and foreground, because most '
             'frames do not need it and splitting one takes real time. Tick the ones you want '
             'and press the button at the bottom. Marko gets an email and does them.</div>')
    for e in sh:
        lbl = ('%s %s' % (e.get('title', 'character sheet'), ver(e))).strip()
        b.append('<h2>Character sheet</h2>'
                 '<div class=sheet><a href="../%s"><img src="../%s" alt=""></a>'
                 '<div class=meta><span class=fid>%s</span>%s%s'
                 '<p class=note>%s</p>%s</div></div>'
                 % (e['file'], e['file'], e.get('title', 'character sheet'),
                    ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                    tag(e.get('status', 'reference')),
                    e.get('note', 'note pending'), picks(lbl)))
    b.append('<h2>Frames</h2>')
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
                fid = e.get('frame', '')
                b.append('<div class=cell><a href="../%s"><img src="../%s" alt=""></a>'
                         '<div class=meta><span class=fid>%s</span>%s%s'
                         '<p class=note>%s</p>%s%s'
                         '</div></div>'
                         % (e['file'], e['file'], fid,
                            ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                            tag(e.get('status', 'proposal')),
                            e.get('note', 'note pending'), bd,
                            picks(('%s %s' % (fid, ver(e))).strip())))
            b.append('</div>')
    b.append((TRAY % ('scene %s' % n, 'Scene %s' % n)).replace("EMAILADDR", EMAIL))
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
    lbl = ('%s %s' % (e.get('title', 'the frame'), ver(e))).strip()
    b.insert(2, '<h2>The frame</h2>'
             '<div class=ovl><a href="%s"><img src="%s" alt=""></a>'
             '<div class=meta><span class=fid>%s</span>%s%s'
             '<p class=note>%s</p><p><a href="%s" download>Download the PNG</a></p>%s</div></div>'
             % (e['file'], e['file'], os.path.basename(e['file']),
                ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                tag(e.get('status', 'reference')), e.get('note', 'note pending'),
                e['file'], picks(lbl)))
for n in sorted(SCENES, key=int):
    c = len(frames_of(n))
    b.append('<li><a href="BB_C_%s/index.html"><span class=n>SC%s</span>'
             '<span class=t>%s</span><span class=c>%s</span></a></li>'
             % (n, n, SCENES[n], '%d frames' % c if c else 'nothing yet'))
b.append('</ul><h2>What changed</h2><div class=log>')
for e in sorted(ENTRIES, key=lambda x: x.get('date', ''), reverse=True):
    who = e.get('frame') or os.path.basename(e['file'])
    b.append('<div class=it><span class=fid>%s</span>%s%s<div class=d>%s</div>'
             '<p class=note>%s</p></div>'
             % (who, ('<span class=ver>%s</span>' % ver(e)) if ver(e) else '',
                tag(e.get('status', 'proposal')), e.get('date', ''),
                e.get('note', 'note pending')))
b.append('</div>')
if overlays_of():
    b.append((TRAY % ('the frame', 'The frame')).replace("EMAILADDR", EMAIL).replace('../marko.png', 'marko.png'))
open(os.path.join(ROOT, 'index.html'), 'w').write(page('The Brain Brake', ''.join(b), depth=0))

print('built: landing, documentation, %d scene pages' % len(SCENES))
