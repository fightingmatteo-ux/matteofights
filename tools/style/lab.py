"""Style lab: the system proposes looks, Matteo picks, the factory A/B tests the pick against the current look,
and the numbers decide.

    python -P tools/style/lab.py propose hook_style poster anton split --why "..."   # comparison image + question
    python -P tools/style/lab.py apply      # answered style questions -> start the A/B test (Control workflow)
    python -P tools/style/lab.py results    # score running tests; decide once both sides have enough reels
    python -P tools/style/lab.py assign <hook_id>   # (factory) which variant this new reel gets

Loop (one experiment at a time):
  1. propose  Claude's Saturday check picks an aspect + 2-3 options from competitor outliers
              (production/competitors/outliers.json), viral research and our own results, renders them side by side
              on a clean frame of Matteo's own footage (production/style/<id>.jpg) and adds a question card. The
              bot sends the image with one button per option ("Keep current" included); the dashboard shows it too.
  2. apply    his pick becomes variant B, the current look stays variant A; look.json "test" makes the factory
              alternate A/B on every new reel (queue item "test": {exp, variant, value}).
  3. results  once A and B each have >= MIN_N reels with numbers (metrics.json, vs the account median), the lab
              writes the result, tells him, and makes the winner the default if B beats A by >= WIN_MARGIN.
Aspects: hook_style (tools/listicle/render.py HOOK_STYLES). More aspects plug in the same way (ASPECTS).
State: production/style/lab.json. Never posts anything.
"""
import argparse, datetime as dt, json, statistics, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "listicle"))
LAB = ROOT / "production" / "style" / "lab.json"
LOOK = ROOT / "production" / "listicles" / "look.json"
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
QUEUE = ROOT / "production" / "schedule" / "queue.json"
CTL = ROOT / "production" / "control"
MIN_N, WIN_MARGIN = 6, 0.15
LABELS = {"native": "Current (Instagram native serif)", "poster": "Poster (Bebas, white on red)",
          "anton": "Anton (red on black)", "split": "Split (Bebas white, last line red)"}


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def current(aspect):
    look = load(LOOK, {})
    return look.get(aspect, "native" if aspect == "hook_style" else None)


def clean_frame():
    """A frame of Matteo's own training without burned-in text: the best graded moment of an upcoming clip
    (fetched by the factory into media/listicles), else a frame from any local training clip, else a cover."""
    from PIL import Image
    import subprocess, tempfile
    cands = sorted((ROOT / "media" / "listicles").glob("*.[mM][oOpP][vV4]")) + \
        sorted((ROOT / "media").glob("**/own/*.mp4"))
    moments = load(ROOT / "production" / "listicles" / "moments.json", {})
    import technique
    for c in cands[:6]:
        good = (moments.get(c.stem) or {}).get("good") or []
        t = good[0] + 2 if good else None
        for probe in ([] if t is not None else [6, 16, 26, 36]):  # ungraded: first spot where the pose check passes
            try:
                p = technique.score(c, probe, 2.0)
            except Exception:
                continue
            if not p.get("veto") and p.get("body", 0) >= 0.35:
                t = probe + 1.0
                break
        if t is None:
            continue
        out = Path(tempfile.gettempdir(), "lab_frame.jpg")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.1f}", "-i", str(c), "-frames:v", "1", "-vf",
                            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", str(out)])
        if r.returncode == 0 and out.exists():
            return Image.open(out).convert("RGB")
    covers = sorted((ROOT / "production" / "listicles").glob("*/cover.jpg"))
    return Image.open(covers[-1]).convert("RGB").resize((1080, 1920)) if covers else Image.new("RGB", (1080, 1920), (40, 40, 40))


def render_hook_styles(values, out, hook=None):
    import render as r
    from PIL import Image, ImageDraw, ImageFont
    if not hook:
        q = [i for i in load(QUEUE, {"items": []})["items"] if i["id"].startswith("lst-") and i.get("hook")]
        hook = q[-1]["hook"] if q else "6 SIGNS YOU WERE BUILT FOR FIGHT NIGHT"
    bg = clean_frame()
    tw, th = 432, 768
    sheet = Image.new("RGB", (tw * len(values) + 12 * (len(values) - 1), th), "white")
    for n, v in enumerate(values):
        im = bg.copy()
        lay, _ = r.hook_layer(hook, 300, v)
        im.paste(lay, (0, 0), lay)
        t = im.resize((tw, th))
        d = ImageDraw.Draw(t)
        d.rectangle((0, 0, tw, 50), fill=(0, 0, 0))
        d.text((12, 9), f"{n + 1}  {v.upper()}{' (CURRENT)' if n == 0 else ''}", fill=(255, 255, 0),
               font=ImageFont.truetype(str(r.BEBAS), 36))
        sheet.paste(t, (n * (tw + 12), 0))
    sheet.save(out, "JPEG", quality=86)


ASPECTS = {"hook_style": {"render": render_hook_styles, "label": "hook text look", "values": lambda: __import__("render").HOOK_STYLES}}


def propose(aspect, options, why):
    lab = load(LAB, {"experiments": []})
    if any(e["status"] in ("proposed", "testing") for e in lab["experiments"]):
        sys.exit("an experiment is already proposed or running; one at a time keeps the result clean")
    spec = ASPECTS[aspect]
    known = spec["values"]()
    bad = [o for o in options if o not in known]
    if bad:
        sys.exit(f"unknown {aspect} option(s): {bad}; known: {list(known)}")
    ctrl = current(aspect)
    values = [ctrl] + [o for o in options if o != ctrl]
    eid = f"exp-{dt.date.today():%m%d}-{aspect}"
    img = ROOT / "production" / "style" / f"{eid}.jpg"
    img.parent.mkdir(parents=True, exist_ok=True)
    spec["render"](values, img)
    opts = [f"{n + 2}. {LABELS.get(v, v)}" for n, v in enumerate(values[1:])] + ["Keep the current one"]
    qid = "q-" + uuid.uuid4().hex[:6]
    qs = load(CTL / "questions.json", [])
    qs.append({"id": qid, "kind": "style", "exp": eid, "image": str(img.relative_to(ROOT)).replace("\\", "/"),
               "question": f"Which {spec['label']} should we test against the current one?",
               "context": (why + "\n\n" if why else "") + "1 is the current look. Your pick runs on every other reel "
                          f"until both have {MIN_N}+ reels with numbers; the better one becomes the default.",
               "options": opts, "status": "open"})
    save(CTL / "questions.json", qs)
    lab["experiments"].append({"id": eid, "aspect": aspect, "control": ctrl, "options": values[1:], "why": why,
                               "image": str(img.relative_to(ROOT)).replace("\\", "/"), "question": qid,
                               "status": "proposed", "proposed_at": now()})
    save(LAB, lab)
    print(f"proposed {eid}: {values} -> question {qid}")


def apply():
    lab = load(LAB, {"experiments": []})
    qs = {q["id"]: q for q in load(CTL / "questions.json", [])}
    look = load(LOOK, {})
    changed = False
    for e in lab["experiments"]:
        q = qs.get(e.get("question"))
        if e["status"] != "proposed" or not q or q.get("status") != "answered":
            continue
        ans = q["answer"]
        pick = next((v for n, v in enumerate(e["options"]) if ans.startswith(f"{n + 2}.")), None)
        if not pick:
            e.update(status="rejected", decided_at=now(), note=f"Matteo kept the current look ({ans})")
        else:
            e.update(status="testing", b=pick, started=now())
            look["test"] = {"exp": e["id"], "aspect": e["aspect"], "a": e["control"], "b": pick, "n": 0}
        changed = True
        print(f"{e['id']}: {e['status']} ({ans})")
    if changed:
        save(LAB, lab)
        save(LOOK, look)


def assign(hook_id):
    """Variant for the next reel while a test runs: alternate A/B. Returns (aspect, value, test record) or None."""
    look = load(LOOK, {})
    t = look.get("test")
    if not t:
        return None
    variant = "b" if t.get("n", 0) % 2 == 0 else "a"
    t["n"] = t.get("n", 0) + 1
    save(LOOK, look)
    return t["aspect"], t[variant], {"exp": t["exp"], "variant": variant, "value": t[variant]}


def results():
    lab, look = load(LAB, {"experiments": []}), load(LOOK, {})
    metrics = load(CTL / "metrics.json", {}).get("reels", {})
    items = load(QUEUE, {"items": []})["items"]
    notes = load(CTL / "notes.json", [])
    for e in lab["experiments"]:
        if e["status"] != "testing":
            continue
        side = {"a": [], "b": []}
        for i in items:
            t = i.get("test") or {}
            m = metrics.get(i.get("media_id") or "", {})
            if t.get("exp") == e["id"] and m.get("vs_median_x") is not None:
                side[t["variant"]].append(m["vs_median_x"])
        e["n"] = {k: len(v) for k, v in side.items()}
        e["median_vs_normal"] = {k: (round(statistics.median(v), 2) if v else None) for k, v in side.items()}
        if min(e["n"].values()) < MIN_N:
            continue
        a, b = e["median_vs_normal"]["a"], e["median_vs_normal"]["b"]
        winner = e["b"] if b >= a * (1 + WIN_MARGIN) else e["control"]
        e.update(status="decided", winner=winner, decided_at=now())
        if winner != e["control"]:
            look[e["aspect"]] = winner
        look.pop("test", None)
        notes.append({"id": "lab-" + e["id"], "text": f"🧪 Style test done ({e['aspect']}): {LABELS.get(e['b'], e['b'])} "
                      f"{b}x vs current {a}x the normal views over {e['n']['b']}+{e['n']['a']} reels. "
                      + (f"Switching the default to {e['b']}." if winner != e["control"] else "Keeping the current look.")})
        print(f"{e['id']} decided: {winner}")
    save(LAB, lab)
    save(LOOK, look)
    save(CTL / "notes.json", notes)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["propose", "apply", "results", "assign"])
    p.add_argument("args", nargs="*")
    p.add_argument("--why", default="")
    a = p.parse_args()
    if a.cmd == "propose":
        propose(a.args[0], a.args[1:], a.why)
    elif a.cmd == "apply":
        apply()
    elif a.cmd == "results":
        results()
    else:
        print(assign(a.args[0]))
