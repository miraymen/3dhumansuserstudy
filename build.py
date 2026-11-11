"""Builds index.html from manifest.json (written by prepare_media.py). One self-contained page: styles and scripts inline, the media
in videos/. Blind: no method names anywhere; the people and each person's six results are shuffled in the browser for every visitor,
and the results are labelled A-F in the order shown.
    python3 build.py ["status line"] ["text of a missing result's tile"]
"""
import html
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.load(open(HERE / "manifest.json"))
STATUS = sys.argv[1] if len(sys.argv) > 1 else ""
PENDING = sys.argv[2] if len(sys.argv) > 2 else "not available"
AC, AR = M["column_aspects"]["clip"], M["column_aspects"]["result"]
# The responses go to a Google Form (form.json: {"action": ".../formResponse", "fields": {"participant": "entry.N", ...}}, from the
# form's pre-filled link): a plain form submission, no script and no permissions.
FORM = json.load(open(HERE / "form.json")) if (HERE / "form.json").exists() else {}
import time
VERSION = time.strftime("%Y-%m-%d %H:%M")
QUESTION = "Which 3D reconstruction looks most like the person in the video?"

CSS = """
:root { --bg: #fbfbfa; --fg: #1d1d1f; --muted: #6b6b70; --line: #e4e4e2; --accent: #1f5fbf; --warn: #b3261e; }
@media (prefers-color-scheme: dark) { :root { --bg: #141416; --fg: #ececee; --muted: #9a9aa2; --line: #2c2c31; --accent: #8ab4f8; --warn: #ff8a80; } }
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
header { max-width: 1100px; margin: 0 auto; padding: 40px 16px 8px; }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 12px; letter-spacing: -0.01em; }
header p { color: var(--muted); margin: 0 0 10px; max-width: 900px; }
.status { color: var(--warn) !important; font-weight: 600; }
.controls { max-width: 1100px; margin: 0 auto; padding: 8px 16px 18px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
button { font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid var(--line); background: transparent; color: var(--fg); cursor: pointer; }
button:hover { border-color: var(--accent); color: var(--accent); }
.grid { padding: 0 16px 64px; }
.inner { max-width: 1240px; margin: 0 auto; }
.cols button.on { background: var(--accent); color: #fff; border-color: var(--accent); }
.colhead { position: sticky; top: 0; z-index: 5; background: var(--bg); display: flex; gap: 6px; padding: 8px 0 6px; border-bottom: 1px solid var(--line); }
.colhead div { font-size: 13px; font-weight: 600; color: var(--muted); text-align: center; }
.person { margin-top: 56px; padding-top: 8px; border-top: 1px solid var(--line); }
.pname { display: flex; gap: 12px; align-items: baseline; margin: 0 0 8px; }
.pname h2 { font-size: 18px; margin: 0; }
.pname a { color: var(--accent); font-size: 13px; text-decoration: none; }
.clipwrap { max-width: 640px; margin: 0 auto 18px; }
.results { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 700px) { .results { grid-template-columns: repeat(2, 1fr); gap: 10px; } }
.cell { display: flex; flex-direction: column; gap: 8px; }
.cell .tile { width: 100%; }
.pick { width: 100%; font-weight: 700; font-size: 16px; padding: 6px 0; }
.pick.sel { background: var(--accent); color: #fff; border-color: var(--accent); }
.pick:disabled { opacity: 0.45; cursor: default; }
.q { font-weight: 600; margin: 0 0 8px; }
.tile { position: relative; background: #fff; border-radius: 4px; overflow: hidden; cursor: zoom-in; }
.tile video { display: block; width: 100%; height: 100%; object-fit: contain; background: #fff; }
.tile.clip video { object-fit: cover; background: #000; }
.tile .lab { position: absolute; top: 6px; left: 6px; background: rgba(0,0,0,0.62); color: #fff; font-size: 13px; font-weight: 700;
             border-radius: 4px; padding: 1px 7px; pointer-events: none; }
.tile.na { cursor: default; display: flex; align-items: center; justify-content: center; color: #888; font-size: 13px; }
.form { display: flex; gap: 12px; align-items: center; justify-content: center; margin: 16px 0 0; }
.sctl { display: flex; gap: 10px; justify-content: center; margin: 0 0 14px; }
.form .q { font-weight: 600; margin-right: 6px; }
.form .choices button { min-width: 38px; font-weight: 700; }
.form .choices button.sel { background: var(--accent); color: #fff; border-color: var(--accent); }
.form .submit { background: var(--fg); color: var(--bg); border-color: var(--fg); }
.form .submit:disabled, .form .choices button:disabled { opacity: 0.45; cursor: default; }
.form .msg { color: var(--muted); font-size: 13px; }
.form .msg.ok { color: #188038; font-weight: 600; }
.tile.sel { outline: 4px solid var(--accent); outline-offset: -4px; }
.progress { font-weight: 600; }
.lb { position: fixed; inset: 0; background: rgba(0,0,0,0.88); z-index: 50; display: none; align-items: center; justify-content: center; flex-direction: column; padding: 16px; }
.lb.on { display: flex; }
.lb video { max-width: 100%; max-height: calc(100vh - 80px); background: #fff; }
.lb .cap { color: #ddd; font-size: 14px; margin-top: 10px; text-align: center; }
.lb .x { position: absolute; top: 12px; right: 18px; color: #fff; font-size: 28px; cursor: pointer; background: none; border: none; }
"""

JS = """

const io = new IntersectionObserver(es => es.forEach(e => {
  const v = e.target; if (e.isIntersecting) { if (!v.src) v.src = v.dataset.src; if (!paused && v.closest('.person').dataset.paused !== '1') v.play().catch(() => {}); } else v.pause();
}), { rootMargin: '300px 0px' });
let paused = false;
document.querySelectorAll('.tile video').forEach(v => io.observe(v));

document.getElementById('sync').onclick = () => document.querySelectorAll('.results video').forEach(v => { if (v.src) { v.currentTime = 0; v.play().catch(() => {}); } });
document.querySelectorAll('.person').forEach(sec => {
  const pb = sec.querySelector('.spause'), rb = sec.querySelector('.srestart'), vids = () => Array.from(sec.querySelectorAll('video'));
  pb.onclick = () => { const on = sec.dataset.paused !== '1'; sec.dataset.paused = on ? '1' : '0'; pb.textContent = on ? 'Play' : 'Pause';
    vids().forEach(v => on ? v.pause() : (v.src && v.play().catch(() => {}))); };
  rb.onclick = () => { sec.dataset.paused = '0'; pb.textContent = 'Pause';
    sec.querySelectorAll('.results video').forEach(v => { if (!v.src) v.src = v.dataset.src; v.currentTime = 0; v.play().catch(() => {}); }); };
});
document.getElementById('pause').onclick = e => { paused = !paused; e.target.textContent = paused ? 'Play all' : 'Pause all';
  document.querySelectorAll('.tile video').forEach(v => paused ? v.pause() : (v.src && v.play().catch(() => {}))); };
const lb = document.getElementById('lb'), body = document.getElementById('lbbody'), cap = document.getElementById('lbcap');
function closeLb() { lb.classList.remove('on'); body.innerHTML = ''; }
document.querySelectorAll('.tile[data-full]').forEach(t => t.onclick = () => {
  body.innerHTML = `<video src="${t.dataset.full}" autoplay loop muted playsinline controls></video>`;
  cap.textContent = 'Subject ' + t.closest('.person').dataset.num + (t.dataset.label ? ' · result ' + t.dataset.label : ' · input video');
  lb.classList.add('on');
});
lb.onclick = e => { if (e.target === lb || e.target.classList.contains('x')) closeLb(); };
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLb(); });
"""


FORM_JS = """
const T0 = Date.now();
function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
let pid = store('study_pid');
if (!pid) { pid = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now(); store('study_pid', pid); }
let done = {}; try { done = JSON.parse(store('study_done') || '{}') || {}; } catch (e) { done = {}; }
const secs = Array.from(document.querySelectorAll('.person'));
function progress() { document.getElementById('progress').textContent = 'Submitted ' + secs.filter(s => done[s.dataset.person]).length + ' of ' + secs.length; }
secs.forEach(sec => {
  const tiles = Array.from(sec.querySelectorAll('.results .tile[data-rid]'));
  const picks = Array.from(sec.querySelectorAll('.results .pick'));
  const sub = sec.querySelector('.submit'), msg = sec.querySelector('.msg');
  const lock = () => { picks.forEach(b => b.disabled = true); sub.disabled = true; msg.textContent = 'Submitted ✓'; msg.className = 'msg ok'; };
  picks.forEach(b => {
    const t = b.parentElement.querySelector('.tile');
    b.onclick = () => { sec.dataset.sel = t.dataset.rid; picks.forEach(x => x.classList.toggle('sel', x === b));
                        tiles.forEach(x => x.classList.toggle('sel', x === t)); sub.disabled = false; msg.textContent = ''; };
  });
  if (done[sec.dataset.person]) lock();
  sub.onclick = async () => {
    const rid = sec.dataset.sel; if (!rid) return;
    const t = tiles.find(x => x.dataset.rid === rid);
    const body = { participant: pid, person: sec.dataset.person, choice: rid, label: t.dataset.label, order: tiles.map(x => x.dataset.rid),
                   labels: tiles.map(x => x.dataset.label), seconds: Math.round((Date.now() - T0) / 1000), ua: navigator.userAgent, version: VERSION };
    if (!FORM.action) { msg.textContent = 'Not recorded: responses are not connected yet.'; msg.className = 'msg'; return; }
    sub.disabled = true; msg.textContent = 'Sending…'; msg.className = 'msg';
    const fd = new URLSearchParams();
    for (const [k, v] of Object.entries(body)) if (FORM.fields[k]) fd.append(FORM.fields[k], Array.isArray(v) ? v.join(' ') : String(v));
    try {
      await fetch(FORM.action, { method: 'POST', mode: 'no-cors', body: fd });
      done[sec.dataset.person] = rid; store('study_done', JSON.stringify(done)); lock(); progress();
    } catch (e) { sub.disabled = false; msg.textContent = 'Could not send; please try again.'; }
  };
});
progress();
"""


def vtile(it, person, aspect, cls, label, letter=""):
    rid = f' data-rid="{it["id"]}" data-label="{letter}"' if label else ""
    flex = ""
    return (f'<div class="tile {cls}"{rid} style="{flex}aspect-ratio: {aspect:.4f};" data-full="{it["full"]}" '
            f'><video data-src="{it["src"]}" poster="{it["poster"]}" muted loop playsinline preload="none"></video></div>')


def main():
    n = M["n_results"]
    colhead = (f'<div style="flex: {AC:.4f} 1 0;">Input video</div>'
               f'<div style="flex: {n * AR:.4f} 1 0;">Six 3D reconstructions (random order)</div>')
    rows, order = [], []
    byid = {p["id"]: p for p in M["people"]}
    if (HERE / "study_order.json").exists():          # the fixed order (subject order + letters), kept across rebuilds
        fixed = json.load(open(HERE / "study_order.json"))["order"]
        plan = [(byid[e["subject_id"]], [next(r for r in byid[e["subject_id"]]["results"] if r["id"] == e["labels"][L])
                                         for L in "ABCDEF" if L in e["labels"]]) for e in fixed]
    else:                                             # first build: ONE randomisation, the same for every participant
        rng = random.Random(20261111)
        people = list(M["people"]); rng.shuffle(people)
        plan = []
        for p in people:
            r_ = list(p["results"]); rng.shuffle(r_); plan.append((p, r_))
    for num, (p, res_items) in enumerate(plan, 1):
        order.append(dict(subject=num, subject_id=p["id"], labels={"ABCDEF"[i]: r["id"] for i, r in enumerate(res_items)}))
        cell = lambda inner: f'<div class="cell">{inner}</div>'
        res = [cell(vtile(r, "", AR, "", True, "ABCDEF"[i]) + f'<button class="pick" type="button">{"ABCDEF"[i]}</button>')
               for i, r in enumerate(res_items)]
        res += [cell(f'<div class="tile na" style="aspect-ratio: {AR:.4f};">{html.escape(PENDING)}</div>')] * (n - len(res))
        form = '<div class="form"><button class="submit" disabled>Submit</button><span class="msg"></span></div>'
        question = f'<p class="q">{html.escape(QUESTION)}</p>'
        rows.append(f'<section class="person" data-person="{p["id"]}" data-num="{num}"><div class="pname"><h2 class="subj">Subject {num}</h2></div>{question}'
                    f'<div class="clipwrap">{vtile(p["clip"], "", AC, "clip", False)}</div>'
                    f'<div class="sctl"><button class="srestart" type="button">Restart together</button><button class="spause" type="button">Pause</button></div>'
                    f'<div class="results">{"".join(res)}</div>{form}</section>')
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(M['title'])}</title><style>{CSS}</style></head>
<body>
<header><h1>{html.escape(M['title'])}</h1>{f'<p class="status">{html.escape(STATUS)}</p>' if STATUS else ''}{''.join(f'<p>{html.escape(t)}</p>' for t in M['intro'])}</header>
<div class="controls"><button id="sync">Restart turntables together</button><button id="pause">Pause all</button><span class="progress" id="progress"></span></div>
<div class="grid"><div class="inner">{''.join(rows)}</div></div>
<div class="lb" id="lb"><button class="x" aria-label="close">×</button><div id="lbbody"></div><div class="cap" id="lbcap"></div></div>
<script>const FORM = {json.dumps(FORM)}, VERSION = {json.dumps(VERSION)};{JS}{FORM_JS}</script>
</body></html>
"""
    (HERE / "index.html").write_text(page)
    if not (HERE / "study_order.json").exists():
        json.dump(dict(seed=20261111, note="the fixed order every participant sees: subject number -> subject id, letter -> result id "
                       "(methods and people: study_key.json)", order=order), open(HERE / "study_order.json", "w"), indent=1)
    print("index.html", len(page), "bytes,", len(M["people"]), "people")


if __name__ == "__main__":
    main()
