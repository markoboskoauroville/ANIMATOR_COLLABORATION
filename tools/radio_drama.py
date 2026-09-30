"""The radio drama page: the film told out loud, played from the site.

Marko, 30.9.2026: "I need that actual radio drama to be played from that site.
There should also be a play button as on the film. The main page for how the
film moves, listen 1:21 seconds. So the same principles apply to the radio
drama."

So this page works like the film page's LISTEN cue: one brass button per scene
with its length, the words of that scene printed under it, ONE player for the
whole page (pressing a second cue stops the first). On top, one button plays
all ten scenes in order and walks the page down with it. English first because
it is complete and it is what the film is judged in; the Croatian v7 beside it
behind a switch, its unrecorded lines shown dim so what is missing is visible.

build_site.py calls drama_page(CAT). Run on its own it rewrites the drama part
of radiodrama.html in place from catalog.json, for when the whole build cannot
run:  python3 tools/radio_drama.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAY = '<svg class=ic-p viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg>'
STOP = '<svg class=ic-s viewBox="0 0 24 24"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>'

CSS = """<style>
/* radio drama, 30.9.2026. The film page's LISTEN cue, one per scene. */
.rd-top{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin:18px 0 8px}
.rd-lang{display:flex;gap:0;border:1px solid var(--rule);border-radius:3px;overflow:hidden}
.rd-lang button{border:0;background:none;padding:7px 12px;cursor:pointer;
 font:600 10px ui-monospace,monospace;letter-spacing:.12em;color:var(--dim)}
.rd-lang button[data-on="1"]{background:var(--brass);color:#17150f}
.rd-all{display:flex;align-items:center;gap:10px;border:0;background:none;cursor:pointer;padding:0}
.rd-all>svg{width:40px;height:40px;border-radius:50%;background:var(--brass);fill:#17150f;
 padding:12px;box-sizing:border-box;flex:0 0 40px}
.rd-all svg.ic-s,.rd-cue svg.ic-s{display:none}
.rd-all[data-on="1"] svg.ic-p,.rd-cue[data-on="1"] svg.ic-p{display:none}
.rd-all[data-on="1"] svg.ic-s,.rd-cue[data-on="1"] svg.ic-s{display:block}
.rd-all span{font:600 11px/1.35 ui-monospace,monospace;letter-spacing:.1em;
 text-transform:uppercase;color:var(--dim);text-align:left}
.rd-all[data-on="1"] span{color:var(--brass)}
.rd-bar{height:3px;background:var(--rule);margin:6px 0 18px;position:relative}
.rd-bar b{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--brass);display:block}
.rd-sc{border-top:1px solid var(--rule);padding:14px 0 6px}
.rd-sc h3{display:flex;align-items:center;gap:12px;margin:0 0 8px;font-size:15px}
.rd-sc h3 .n{font:600 10px ui-monospace,monospace;color:var(--dim);letter-spacing:.1em}
.rd-cue{display:flex;align-items:center;gap:8px;border:0;cursor:pointer;background:none;
 padding:0;margin:0 0 0 auto}
.rd-cue>svg{width:26px;height:26px;border-radius:50%;background:var(--brass);fill:#17150f;
 padding:7px;box-sizing:border-box;flex:0 0 26px}
.rd-cue span{font:600 9.5px/1.35 ui-monospace,monospace;letter-spacing:.08em;
 text-transform:uppercase;color:var(--dim)}
.rd-cue[data-on="1"] span{color:var(--brass)}
.rd-sc[data-on="1"] h3{color:var(--brass)}
.rd-ln{margin:0 0 6px;line-height:1.5}
.rd-ln .sp{font:600 9.5px ui-monospace,monospace;letter-spacing:.1em;color:var(--dim);
 margin-right:8px}
.rd-ln.silent{opacity:.4}
.rd-hide{display:none}
</style>"""

JS = """<script>
/* ONE player for the page, the film page's rule: a second cue stops the first.
   PLAY THE WHOLE RADIO DRAMA runs the scenes of the language shown, in order. */
(function(){
  var au = new Audio(); au.preload = 'none';
  var now = null, chain = false;
  var all = document.getElementById('rd-all'), bar = document.querySelector('.rd-bar b');
  function cues(){ var l = document.querySelector('.rd-lang [data-on="1"]').dataset.l;
    return [].slice.call(document.querySelectorAll('.rd-set[data-l="'+l+'"] .rd-cue')); }
  function mark(c, on){ if (!c) return; c.dataset.on = on ? '1' : '0';
    c.closest('.rd-sc').dataset.on = on ? '1' : '0'; }
  function stop(){ mark(now, false); now = null; chain = false; all.dataset.on = '0'; }
  function play(c){
    if (now && now !== c) mark(now, false);
    now = c; au.src = c.dataset.src; au.currentTime = 0; mark(c, true);
    au.play().catch(function(){ stop(); });
  }
  document.querySelectorAll('.rd-cue').forEach(function(c){
    c.addEventListener('click', function(){
      chain = false; all.dataset.on = '0';
      if (now === c && !au.paused){ au.pause(); return; }
      if (now === c && au.paused && au.currentTime > 0){ au.play(); mark(c, true); return; }
      play(c);
    });
  });
  all.addEventListener('click', function(){
    if (chain && !au.paused){ au.pause(); all.dataset.on = '0'; return; }
    if (chain && au.paused && now){ au.play(); all.dataset.on = '1'; mark(now, true); return; }
    chain = true; all.dataset.on = '1'; var c = cues()[0]; play(c);
    c.closest('.rd-sc').scrollIntoView({behavior:'smooth', block:'start'});
  });
  au.addEventListener('ended', function(){
    if (!chain){ stop(); return; }
    var list = cues(), i = list.indexOf(now);
    if (i < 0 || i + 1 >= list.length){ stop(); return; }
    play(list[i+1]); list[i+1].closest('.rd-sc').scrollIntoView({behavior:'smooth', block:'start'});
  });
  au.addEventListener('pause', function(){ if (now && au.currentTime < au.duration) mark(now, false);
    if (chain) all.dataset.on = '0'; });
  au.addEventListener('play', function(){ if (chain) all.dataset.on = '1'; });
  au.addEventListener('timeupdate', function(){
    if (!now || !au.duration) return;
    var list = cues(), i = list.indexOf(now), tot = 0, done = 0;
    list.forEach(function(c, k){ var s = +c.dataset.sec; tot += s; if (k < i) done += s; });
    bar.style.width = (100 * (done + au.currentTime) / tot) + '%';
  });
  document.querySelectorAll('.rd-lang button').forEach(function(b){
    b.addEventListener('click', function(){
      au.pause(); stop(); bar.style.width = '0';
      document.querySelectorAll('.rd-lang button').forEach(function(x){ x.dataset.on = x === b ? '1' : '0'; });
      document.querySelectorAll('.rd-set').forEach(function(s){ s.classList.toggle('rd-hide', s.dataset.l !== b.dataset.l); });
      var t = document.getElementById('rd-total'); t.textContent = b.dataset.total;
    });
  });
})();
</script>"""


def mmss(sec):
    sec = int(round(sec))
    return '%d:%02d' % (sec // 60, sec % 60)


def _set(lang, scenes, lines, speaker_names, hidden):
    out = ['<div class="rd-set%s" data-l="%s">' % (' rd-hide' if hidden else '', lang)]
    for i, sc in enumerate(scenes, 1):
        out.append('<div class=rd-sc id="%s-%s"><h3><span class=n>%02d</span>%s'
                   '<button class=rd-cue type=button data-src="%s" data-sec="%.2f" '
                   'aria-label="listen: %s">%s%s<span>LISTEN &nbsp;%s</span></button></h3>'
                   % (lang, sc['id'], i, html.escape(sc['title']), sc['url'], sc['sec'],
                      html.escape(sc['title']), PLAY, STOP, mmss(sc['sec'])))
        for ln in lines:
            if ln.get('scene') != sc['id']:
                continue
            recorded = bool(ln.get('audio') or ln.get('file'))
            out.append('<p class="rd-ln%s"><span class=sp>%s</span>%s</p>'
                       % ('' if recorded else ' silent',
                          html.escape(speaker_names.get(ln['speaker'], ln['speaker'])),
                          html.escape(ln['text'])))
        out.append('</div>')
    out.append('</div>')
    return ''.join(out)


def drama_page(cat):
    en, en_sc = cat.get('radio_drama_en', []), cat.get('radio_drama_en_scenes', [])
    hr, hr_sc = cat.get('radio_drama_v7', []), cat.get('radio_drama_v7_scenes', [])
    if not en_sc:
        return ''
    t_en = sum(s['sec'] for s in en_sc)
    t_hr = sum(s['sec'] for s in hr_sc)
    silent = sum(1 for x in hr if not x.get('audio'))
    o = [CSS,
         '<h1>The radio drama</h1>',
         '<p class=lede><b>The whole film told out loud, which is where everything in it comes from.</b> '
         'Ten scenes, one file each, with the words of each scene under its button so you can read '
         'along. In English Beatrice narrates, Edmund is Manan and Hugh is Viveka. In Croatian '
         'Gabrijela narrates and Srećko is Manan%s.</p>'
         % (('; %d lines of the first scene are written and not yet recorded, shown faint' % silent)
            if silent else ''),
         '<div class=rd-top><button class=rd-all id=rd-all type=button>%s%s'
         '<span>PLAY THE WHOLE RADIO DRAMA<br><b id=rd-total>%s</b></span></button>'
         '<div class=rd-lang><button type=button data-l=en data-on=1 data-total="%s">ENGLISH</button>'
         '%s</div></div><div class=rd-bar><b></b></div>'
         % (PLAY, STOP, mmss(t_en), mmss(t_en),
            ('<button type=button data-l=hr data-on=0 data-total="%s">HRVATSKI</button>' % mmss(t_hr))
            if hr_sc else ''),
         _set('en', en_sc, en, {'NARRATOR': 'NARRATOR'}, False)]
    if hr_sc:
        o.append(_set('hr', hr_sc, hr, {}, True))
    o.append(JS)
    return ''.join(o)


if __name__ == '__main__':
    cat = json.load(open(os.path.join(ROOT, 'catalog.json')))
    p = os.path.join(ROOT, 'radiodrama.html')
    s = open(p).read()
    body = drama_page(cat)
    # replace an earlier drama section, or put it in front of the music heading
    s = re.sub(r'<!--rd-->.*?<!--/rd-->', '', s, flags=re.S)
    a = s.index('<h1>The music, written for the film</h1>')
    s = s[:a] + '<!--rd-->' + body + '<!--/rd-->' + s[a:].replace(
        '<h1>The music, written for the film</h1>', '<h2>The music, written for the film</h2>', 1)
    open(p, 'w').write(s)
    print('radiodrama.html: %d bytes of drama' % len(body))
