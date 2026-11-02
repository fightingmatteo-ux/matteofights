"""Animated day cards for editorial plan reels (HTML + GSAP inside the hyperframes render, not baked video).

Design (impeccable craft floor + Emil Kowalski motion): full-frame OLED black, the day's focus as the heading (Geist
800, tight tracking), the day position as tabular numerals in the one accent (brand red), a hairline list of moves
with doses, the last move on 3+ move days blurred behind a drawn-lock pill "Comment WORD for this one", plan name +
level segmented control at the foot. Motion: one moment per card, 240 ms expo.out from 0.97 scale + 8 px blur,
rows stagger 40 ms, nothing animates from zero, no ease-in.
"""
import html

CSS = """
.dc { position:absolute; inset:0; background:#0A0A0C; font-family:"Geist",sans-serif; color:#F4F4F5; }
.dc-in { position:absolute; inset:0; padding:300px 80px 0; transform-origin:50% 40%; }
.dc-top { display:flex; justify-content:space-between; align-items:flex-end; }
.dc-h { font-weight:800; font-size:200px; line-height:.86; letter-spacing:-.055em; margin:0; }
.dc-pos { font-weight:700; font-size:64px; color:#E8112D; font-variant-numeric:tabular-nums; letter-spacing:-.02em; padding-bottom:14px; }
.dc-list { list-style:none; margin:64px 0 0; padding:0; }
.dc-list li { display:flex; gap:34px; align-items:baseline; padding:30px 0; border-top:2px solid rgba(255,255,255,.08); position:relative; }
.dc-list li:first-child { border-top:0; }
.dc-n { font-weight:600; font-size:40px; color:#71717A; font-variant-numeric:tabular-nums; width:34px; }
.dc-name { font-weight:650; font-size:54px; letter-spacing:-.025em; line-height:1.05; }
.dc-dose { display:block; margin-top:10px; font-weight:500; font-size:40px; color:#D4A24C; font-variant-numeric:tabular-nums; }
.dc-list li.lock .dc-b { filter:blur(16px); opacity:.85; }
.dc-pill { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); display:flex; gap:18px; align-items:center;
  background:#E8112D; color:#fff; font-weight:650; font-size:40px; letter-spacing:-.01em; padding:24px 40px; border-radius:999px;
  white-space:nowrap; box-shadow:0 18px 40px rgba(232,17,45,.28); }
.dc-pill svg { width:34px; height:40px; }
.dc-foot { position:absolute; left:80px; right:80px; bottom:250px; border-top:2px solid rgba(255,255,255,.08); padding-top:36px; }
.dc-plan { font-weight:600; font-size:38px; color:#A1A1AA; letter-spacing:-.01em; }
.dc-lv { display:inline-flex; margin-top:24px; padding:6px; border-radius:999px; background:#18181B; }
.dc-lv span { font-weight:600; font-size:32px; color:#A1A1AA; padding:14px 30px; border-radius:999px; }
.dc-lv span.on { background:#F4F4F5; color:#0A0A0C; }
"""
LOCK = ('<svg viewBox="0 0 34 40" fill="none"><path d="M8 17V11a9 9 0 0 1 18 0v6" stroke="#fff" stroke-width="4" '
        'stroke-linecap="round"/><rect x="2" y="17" width="30" height="21" rx="5" fill="#fff"/></svg>')


def cards(plan, keyword, windows):
    """windows: [(start, dur)] per day, variant time. Returns (html, js)."""
    days = plan["days"]
    out, js = [f"<style>{CSS}</style>"], []
    for k, (day, (s, dur)) in enumerate(zip(days, windows)):
        name = day["d"].split("·")
        head = html.escape(name[-1].strip())
        pos = name[0].strip()[:3].upper() if name[0].strip().lower().startswith(("mon", "tue", "wed", "thu", "fri")) else f"{k + 1}/{len(days)}"
        rows = []
        lock = len(day["items"]) >= 3
        for i, (ex, dose, *_) in enumerate(day["items"]):
            lk = lock and i == len(day["items"]) - 1
            body = f'<div class="dc-b"><span class="dc-name">{html.escape(ex)}</span><span class="dc-dose">{html.escape(dose).replace(" x ", " × ")}</span></div>'
            pill = f'<div class="dc-pill">{LOCK}Comment {html.escape(keyword.capitalize())} for this one</div>' if lk else ""
            rows.append(f'<li class="{"lock" if lk else ""}"><span class="dc-n">{i + 1}</span>{body}{pill}</li>')
        lv = "".join(f'<span class="{"on" if l == "Amateur" else ""}">{l}</span>' for l in ("Beginner", "Amateur", "Advanced"))
        out.append(f'<div id="dc{k}" class="clip dc" data-start="{s:.3f}" data-duration="{dur:.3f}" data-track-index="7"><div class="dc-in">'
                   f'<div class="dc-top"><h2 class="dc-h">{head}</h2><span class="dc-pos">{pos}</span></div>'
                   f'<ol class="dc-list">{"".join(rows)}</ol>'
                   f'<div class="dc-foot"><div class="dc-plan">{html.escape(plan["title"])}</div><div class="dc-lv">{lv}</div></div></div></div>')
        js.append(f'tl.fromTo("#dc{k} .dc-in", {{opacity:0, scale:0.97, filter:"blur(8px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.24, ease:"expo.out"}}, {s:.3f});')
        js.append(f'tl.fromTo("#dc{k} .dc-h", {{y:28}}, {{y:0, duration:0.26, ease:"expo.out"}}, {s:.3f});')
        js.append(f'tl.fromTo("#dc{k} .dc-list li", {{y:22, opacity:0}}, {{y:0, opacity:1, duration:0.24, ease:"expo.out", stagger:0.04}}, {s + 0.04:.3f});')
        if lock:
            js.append(f'tl.fromTo("#dc{k} .dc-pill", {{scale:0.94}}, {{scale:1, duration:0.22, ease:"expo.out"}}, {s + 0.16:.3f});')
    return "\n".join(out), "\n      ".join(js)
