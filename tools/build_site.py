#!/usr/bin/env python3
"""
STEP 53 and 54. Build the animator's site from catalog.json.

    python3 tools/build_site.py

Kristijan gets a link to a web page. No GitHub account, no invitation, no idea
what a repo is. He reads what is going on, looks at every frame, downloads the
one he wants or takes a zip and has the lot.

CATALOG.JSON IS THE TRUTH AND NOTHING HERE IS TYPED BY HAND. Every word on the
page comes out of that file, so the page cannot drift from what was decided. When
Marko accepts or rejects something, the catalog changes and the site follows.

THE ZIPS ARE BUILT DETERMINISTICALLY AND THAT IS NOT A DETAIL. This runs after
every push. A zip carries the modification time of every file inside it, so an
ordinary zip of unchanged artwork is a different sequence of bytes every single
run, git sees a change, and a hundred megabytes of identical archive goes into the
history every time somebody drops in a file. Fixed timestamp, fixed order, fixed
compression, and an unchanged scene produces byte for byte the same zip, which git
correctly sees as nothing at all. The thumbnails are written the same way.

THE PASSPHRASE IS A DOORMAT, NOT A LOCK. STEP 54. It is on every page including
the eight scene pages, but Pages serves every file in this repository at a
predictable URL, so anyone who guesses a path fetches an image without ever seeing
the gate, and the passphrase is in the page source besides. It keeps a casual
visitor out of the front door. It is not access control and nothing should ever be
built on top of it as though it were.
"""

import datetime, html, json, os, shutil, sys, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, 'catalog.json')
THUMBS = os.path.join(ROOT, 'thumbs')
ZIPS = os.path.join(ROOT, 'downloads')
PASSPHRASE = 'kristijan'
THUMB_W = 720
# 1980-01-01, the earliest a zip entry can carry. Any fixed date does; this one
# is the conventional floor and makes it obvious the timestamp is deliberate.
EPOCH = (1980, 1, 1, 0, 0, 0)

STATUS = {
    'proposal':   ('Proposal',   '#9C7A31'),
    'accepted':   ('Accepted',   '#3F7A46'),
    'rejected':   ('Rejected',   '#A8412C'),
    'superseded': ('Superseded', '#6E6555'),
}

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{
  --paper:#EDE4D0; --ink:#1E1B16; --dim:#6E6555; --rule:#CDBF9F;
  --slate:#20241F; --chalk:#E6E9E0; --brass:#9C7A31;
  --disp:'Bricolage Grotesque',system-ui,sans-serif;
  --body:'Newsreader',Georgia,serif;
  --mono:'JetBrains Mono',ui-monospace,monospace;
  --w:64rem;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--body);font-size:1.12rem;line-height:1.65;font-weight:300;
  -webkit-font-smoothing:antialiased}}

/* ---------- the gate ---------- */
#gate{{position:fixed;inset:0;z-index:100;background:var(--slate);
  display:flex;align-items:center;justify-content:center;padding:24px}}
.gate-card{{width:100%;max-width:380px;background:#171A16;
  border:1px solid #333A31;padding:38px 32px 32px}}
.gate-eyebrow{{font-family:var(--mono);font-size:10px;letter-spacing:.28em;
  text-transform:uppercase;color:#8E9488;margin-bottom:18px}}
.gate-title{{font-family:var(--disp);font-size:40px;font-weight:800;line-height:.95;
  letter-spacing:.01em;text-transform:uppercase;color:var(--chalk)}}
.gate-sub{{font-family:var(--mono);font-size:11px;color:#8E9488;margin-top:10px;
  letter-spacing:.08em}}
.gate-form{{margin-top:30px}}
label.fld{{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.2em;
  text-transform:uppercase;color:#8E9488;margin-bottom:8px}}
input[type=password]{{width:100%;background:var(--slate);border:1px solid #333A31;
  color:var(--chalk);padding:13px 14px;font-family:var(--mono);font-size:15px;
  letter-spacing:.12em}}
input[type=password]:focus{{outline:2px solid var(--brass);outline-offset:1px;
  border-color:var(--brass)}}
.remember{{display:flex;align-items:center;gap:9px;margin-top:16px}}
.remember input{{width:15px;height:15px;accent-color:var(--brass)}}
.remember label{{font-family:var(--mono);font-size:11px;color:#8E9488;cursor:pointer}}
button.enter{{width:100%;margin-top:22px;padding:13px;background:var(--brass);
  border:0;color:#1A1509;cursor:pointer;font-family:var(--disp);font-size:17px;
  font-weight:700;letter-spacing:.14em;text-transform:uppercase}}
button.enter:hover{{background:#B08C3C}}
button.enter:focus-visible{{outline:2px solid var(--chalk);outline-offset:2px}}
#gate-err{{font-family:var(--mono);font-size:11px;color:#E08A6B;margin-top:14px;
  min-height:16px}}
#app{{display:none}}

/* ---------- the page ---------- */
.bar{{background:var(--slate);color:var(--chalk);padding:11px 0;
  border-bottom:1px solid #000}}
.bar-in{{max-width:var(--w);margin:0 auto;padding:0 1.4rem;display:flex;
  align-items:baseline;gap:1rem;flex-wrap:wrap}}
.bar-mark{{font-family:var(--disp);font-weight:800;font-size:19px;
  letter-spacing:.05em;text-transform:uppercase}}
.bar-mark span{{color:var(--brass)}}
.bar-meta{{font-family:var(--mono);font-size:10.5px;color:#8E9488;
  letter-spacing:.08em;margin-left:auto}}
.wrap{{max-width:var(--w);margin:0 auto;padding:0 1.4rem}}
h1{{font-family:var(--disp);font-weight:800;font-size:clamp(2rem,5vw,3.2rem);
  line-height:1.02;letter-spacing:-.01em;margin:2.4rem 0 .5rem}}
h2{{font-family:var(--disp);font-weight:700;font-size:1.5rem;letter-spacing:.01em;
  margin:2.6rem 0 .8rem;padding-bottom:.4rem;border-bottom:1px solid var(--rule)}}
.kicker{{font-family:var(--mono);font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--dim);margin-top:2.2rem}}
.lede{{font-size:1.28rem;line-height:1.6}}
p{{margin:.85rem 0}}
a{{color:#7A5E22}}
ul.rules{{list-style:none;padding:0;margin:1rem 0}}
ul.rules li{{padding:.55rem 0 .55rem 1.6rem;border-bottom:1px dotted var(--rule);
  position:relative}}
ul.rules li:before{{content:"";position:absolute;left:0;top:1.15rem;width:.7rem;
  height:1px;background:var(--brass)}}

/* ---------- downloads ---------- */
.zips{{display:flex;gap:.7rem;flex-wrap:wrap;margin:1.2rem 0 0}}
.zip{{display:block;text-decoration:none;color:var(--ink);border:1px solid var(--rule);
  background:#F4EEE0;padding:.6rem .9rem}}
.zip:hover{{border-color:var(--brass)}}
.zip b{{font-family:var(--disp);font-weight:700;font-size:.98rem;display:block}}
.zip i{{font-family:var(--mono);font-size:10px;color:var(--dim);font-style:normal}}

/* ---------- the contact sheet ---------- */
.sheet{{display:grid;grid-template-columns:repeat(auto-fill,minmax(19rem,1fr));
  gap:1.6rem;margin:1.4rem 0 3rem}}
.card{{border:1px solid var(--rule);background:#F4EEE0}}
.card img{{display:block;width:100%;height:auto;border-bottom:1px solid var(--rule)}}
.card-in{{padding:.75rem .9rem 1rem}}
.card-top{{display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}}
.fr{{font-family:var(--mono);font-weight:600;font-size:.95rem}}
.tag{{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;
  text-transform:uppercase;color:#fff;padding:.16rem .5rem}}
.card-note{{font-size:.99rem;line-height:1.55;margin:.55rem 0 0;color:#2E2A22}}
.card-sup{{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:.5rem}}
.card-dl{{font-family:var(--mono);font-size:10.5px;margin-top:.7rem;display:block}}

/* ---------- the log ---------- */
.log{{margin:1rem 0 3rem}}
.log-row{{display:flex;gap:1rem;padding:.7rem 0;border-bottom:1px dotted var(--rule);
  align-items:baseline;flex-wrap:wrap}}
.log-date{{font-family:var(--mono);font-size:10.5px;color:var(--dim);
  width:6rem;flex:none}}
.log-body{{flex:1;min-width:14rem}}
.empty{{color:var(--dim);font-style:italic}}
footer{{border-top:1px solid var(--rule);margin-top:2rem;padding:1.4rem 0 3rem;
  font-family:var(--mono);font-size:10.5px;color:var(--dim);letter-spacing:.06em}}
.scenes{{display:grid;grid-template-columns:repeat(auto-fill,minmax(13rem,1fr));
  gap:.7rem;margin:1.2rem 0 2rem}}
.scene-a{{display:block;text-decoration:none;color:var(--ink);
  border:1px solid var(--rule);background:#F4EEE0;padding:.8rem .9rem}}
.scene-a:hover{{border-color:var(--brass)}}
.scene-a b{{font-family:var(--disp);font-weight:700;display:block;font-size:1.05rem}}
.scene-a i{{font-family:var(--mono);font-size:10px;color:var(--dim);font-style:normal}}
</style>
</head>
<body>

<div id="gate">
  <div class="gate-card">
    <div class="gate-eyebrow">Animation collaboration</div>
    <div class="gate-title">The Brain<br>Brake</div>
    <div class="gate-sub">Breakthrough Junior Challenge 2026</div>
    <form class="gate-form" id="gate-form">
      <label class="fld" for="pw">Passphrase</label>
      <input type="password" id="pw" autocomplete="current-password" autofocus>
      <div class="remember">
        <input type="checkbox" id="rem" checked>
        <label for="rem">Remember me on this device</label>
      </div>
      <button type="submit" class="enter">Enter</button>
      <div id="gate-err"></div>
    </form>
  </div>
</div>

<div id="app">
<div class="bar"><div class="bar-in">
  <div class="bar-mark">THE BRAIN <span>BRAKE</span></div>
  <div class="bar-meta">{barmeta}</div>
</div></div>
<div class="wrap">
"""

TAIL = """</div>
<footer>Built from catalog.json on {built}. Nothing on this page is typed by hand.</footer>
</div>

<script>
(function(){{
  var PW='{pw}', C='bbc_auth';
  function setCookie(k,v,days){{
    var d=new Date(); d.setTime(d.getTime()+days*864e5);
    document.cookie=k+'='+encodeURIComponent(v)+';expires='+d.toUTCString()+';path=/;SameSite=Lax';
  }}
  function getCookie(k){{
    var m=document.cookie.match('(^|; )'+k+'=([^;]*)');
    return m?decodeURIComponent(m[2]):null;
  }}
  var gate=document.getElementById('gate'), app=document.getElementById('app'),
      form=document.getElementById('gate-form'), pw=document.getElementById('pw'),
      rem=document.getElementById('rem'), err=document.getElementById('gate-err');
  function open_(){{ gate.style.display='none'; app.style.display='block'; }}
  form.addEventListener('submit',function(e){{
    e.preventDefault();
    if(pw.value.trim().toLowerCase()===PW){{
      if(rem.checked) setCookie(C,'1',180);
      open_();
    }}else{{
      err.textContent='Not that one. Try again.';
      pw.value=''; pw.focus();
    }}
  }});
  if(getCookie(C)==='1') open_();
}})();
</script>
</body>
</html>
"""


def e(s):
    return html.escape(str(s), quote=True)


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:.0f} {unit}' if unit == 'B' else f'{n:.1f} {unit}'
        n /= 1024


def thumb(src, dst):
    """A contact sheet of four megabyte PNGs is not a contact sheet. Same input,
    same bytes out, so an unchanged frame is invisible to git."""
    im = Image.open(src).convert('RGB')
    if im.width > THUMB_W:
        im = im.resize((THUMB_W, round(im.height * THUMB_W / im.width)), Image.LANCZOS)
    im.save(dst, 'JPEG', quality=82, optimize=True)


def zip_folder(files, dst, root):
    """Fixed timestamp and sorted order. See the note at the top of this file:
    without it every build writes a new copy of everything into the history."""
    tmp = dst + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in sorted(files):
            info = zipfile.ZipInfo(os.path.relpath(f, root), date_time=EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(f, 'rb') as fh:
                z.writestr(info, fh.read())
    # only replace when the bytes actually differ, so mtime does not churn either
    if os.path.exists(dst) and open(dst, 'rb').read() == open(tmp, 'rb').read():
        os.remove(tmp)
        return False
    os.replace(tmp, dst)
    return True


def status_tag(status):
    label, colour = STATUS.get(status, (status.title(), '#6E6555'))
    return f'<span class="tag" style="background:{colour}">{e(label)}</span>'


def card(en, depth):
    up = '../' * depth
    thumb_rel = f'{up}thumbs/' + os.path.basename(en['file']).rsplit('.', 1)[0] + '.jpg'
    sup = (f'<div class="card-sup">Replaces {e(en["supersedes"])}</div>'
           if en.get('supersedes') else '')
    return f"""<div class="card">
  <img src="{e(thumb_rel)}" alt="Frame {e(en['frame'])}" loading="lazy">
  <div class="card-in">
    <div class="card-top"><span class="fr">{e(en['frame'])}</span>{status_tag(en['status'])}</div>
    <p class="card-note">{e(en['note'])}</p>
    {sup}
    <a class="card-dl" href="{e(up + en['file'])}" download>Download full size, {e(os.path.basename(en['file']))}</a>
  </div>
</div>"""


def page(title, barmeta, body, depth):
    built = datetime.date.today().strftime('%d.%m.%Y')
    return (HEAD.format(title=e(title), barmeta=e(barmeta))
            + body
            + TAIL.format(built=built, pw=PASSPHRASE))


def main():
    cat = json.load(open(CATALOG, encoding='utf-8'))
    entries = cat['entries']
    scenes = cat['scenes']
    os.makedirs(THUMBS, exist_ok=True)
    os.makedirs(ZIPS, exist_ok=True)

    by_scene = {n: [] for n in scenes}
    missing = []
    for en in entries:
        path = os.path.join(ROOT, en['file'])
        if not os.path.exists(path):
            missing.append(en['file'])
            continue
        n = en['file'].split('/')[0][len('BB_C_'):]
        by_scene.setdefault(n, []).append(en)
        thumb(path, os.path.join(THUMBS, os.path.basename(en['file']).rsplit('.', 1)[0] + '.jpg'))
    for f in missing:
        print(f'  MISSING, in the catalog but not on disk: {f}')

    # the zips, one per scene and one of everything
    zipinfo = {}
    every = []
    for n in sorted(scenes, key=int):
        folder = os.path.join(ROOT, f'BB_C_{n}')
        files = [os.path.join(folder, f) for f in sorted(os.listdir(folder))
                 if not f.startswith('.')] if os.path.isdir(folder) else []
        every += files
        dst = os.path.join(ZIPS, f'BB_C_{n}.zip')
        if files:
            changed = zip_folder(files, dst, ROOT)
            zipinfo[n] = (os.path.getsize(dst), changed)
        elif os.path.exists(dst):
            os.remove(dst)
    all_dst = os.path.join(ZIPS, 'BRAIN_BRAKE_ALL.zip')
    if every:
        zip_folder(every, all_dst, ROOT)
        zipinfo['all'] = (os.path.getsize(all_dst), True)
    elif os.path.exists(all_dst):
        os.remove(all_dst)

    built = datetime.date.today().strftime('%d.%m.%Y')

    # ---------- the front page ----------
    b = ['<h1>The frames, scene by scene</h1>',
         '<p class="lede">Everything made for the animation of <b>The Brain Brake</b> is here. '
         'Look at a scene, read why each frame is the way it is, and take the files you need. '
         'Nothing here is in the film yet. It is a proposal until Marko says otherwise.</p>']

    b.append('<div class="kicker">The film</div>')
    b.append('<p>A man is running a very long race and stops, spent. Then, near the end, he runs '
             'fast again. A boy called Manan wants to know where that came from. For a hundred '
             'years the answer was the muscles giving out. It is not. A part of the brain holds a '
             'reserve back and decides when to release it. Two minutes, eight scenes, fifty '
             'frames, one drawn world.</p>')

    if 'all' in zipinfo:
        size, _ = zipinfo['all']
        b.append('<div class="kicker">Take everything</div>')
        b.append(f'<div class="zips"><a class="zip" href="downloads/BRAIN_BRAKE_ALL.zip" download>'
                 f'<b>Every scene, one zip</b><i>{human(size)} &middot; made {built}</i></a></div>')

    b.append('<h2>The scenes</h2><div class="scenes">')
    for n in sorted(scenes, key=int):
        cnt = len(by_scene.get(n, []))
        word = 'nothing yet' if cnt == 0 else ('1 frame' if cnt == 1 else f'{cnt} frames')
        b.append(f'<a class="scene-a" href="BB_C_{n}/"><b>{n}. {e(scenes[n])}</b>'
                 f'<i>BB_C_{n} &middot; {word}</i></a>')
    b.append('</div>')

    b.append('<h2>The working rules</h2><ul class="rules">')
    for r in [
        '<b>Artwork is edge to edge, with no panel border.</b> The frame is not drawn into the '
        'picture. You add it yourself as its own layer, so it can change or come off without '
        'touching the art underneath.',
        '<b>2731 x 1536</b>, true 16:9. Nano Banana returns 2752 wide and it gets cropped.',
        '<b>Never crop an overlay.</b> A picture over another picture is scaled and moved, never cut.',
        '<b>Characters come from the locked references</b>, from their single figure sheet with the '
        'costume line, never from the frame they appear in.',
        '<b>Key light is camera right.</b>',
        '<b>Naming.</b> Frame number with a hyphen. <code>_v2</code> and up for a variation of an '
        'existing frame. A letter for a new frame between two, so <code>1-3a</code> sits between '
        '1.3 and 1.4 and nothing has to be renumbered.',
    ]:
        b.append(f'<li>{r}</li>')
    b.append('</ul>')

    b.append('<h2>What changed, newest first</h2>')
    rows = sorted(entries, key=lambda x: (x['date'], x['frame']), reverse=True)
    if rows:
        b.append('<div class="log">')
        for en in rows:
            n = en['file'].split('/')[0][len('BB_C_'):]
            b.append(f'<div class="log-row"><div class="log-date">{e(en["date"])}</div>'
                     f'<div class="log-body"><div class="card-top">'
                     f'<span class="fr">{e(en["frame"])}</span>{status_tag(en["status"])}'
                     f'<a href="BB_C_{n}/">scene {n}</a></div>'
                     f'<p class="card-note">{e(en["note"])}</p></div></div>')
        b.append('</div>')
    else:
        b.append('<p class="empty">Nothing logged yet.</p>')

    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(
        page('The Brain Brake, animation', f'{len(entries)} frames &middot; {built}',
             '\n'.join(b), 0))

    # ---------- a page per scene ----------
    for n in sorted(scenes, key=int):
        folder = os.path.join(ROOT, f'BB_C_{n}')
        os.makedirs(folder, exist_ok=True)
        got = by_scene.get(n, [])
        s = [f'<p class="kicker"><a href="../">All scenes</a></p>',
             f'<h1>{n}. {e(scenes[n])}</h1>',
             f'<p class="lede">Folder <code>BB_C_{n}</code>. Every frame below is a proposal '
             f'until Marko says otherwise. The note says what changed and why.</p>']
        z = []
        if n in zipinfo:
            z.append(f'<a class="zip" href="../downloads/BB_C_{n}.zip" download>'
                     f'<b>This scene, one zip</b><i>{human(zipinfo[n][0])} &middot; made {built}</i></a>')
        if 'all' in zipinfo:
            z.append(f'<a class="zip" href="../downloads/BRAIN_BRAKE_ALL.zip" download>'
                     f'<b>Every scene</b><i>{human(zipinfo["all"][0])} &middot; made {built}</i></a>')
        if z:
            s.append('<div class="zips">' + ''.join(z) + '</div>')
        if got:
            s.append('<div class="sheet">' + '\n'.join(card(en, 1) for en in
                     sorted(got, key=lambda x: x['frame'])) + '</div>')
        else:
            s.append('<p class="empty">Nothing in this scene yet.</p>')
        open(os.path.join(folder, 'index.html'), 'w', encoding='utf-8').write(
            page(f'Scene {n}, {scenes[n]}', f'Scene {n} &middot; {built}', '\n'.join(s), 1))

    print(f'built index.html and {len(scenes)} scene pages, '
          f'{len(entries)-len(missing)} frame(s) in the catalog')
    for n in sorted(zipinfo, key=lambda k: (k == 'all', k)):
        print(f'  downloads/{"BRAIN_BRAKE_ALL" if n=="all" else "BB_C_"+n}.zip  '
              f'{human(zipinfo[n][0])}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
