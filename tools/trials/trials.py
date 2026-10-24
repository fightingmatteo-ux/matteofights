"""Hook tests on talking heads: 4 trial-reel variants the same day, a verdict at 72 h, a Telegram nudge to share the
winner, and a running tally of which OPENING types win across every test (the self-learning part).

    python -P tools/trials/trials.py label <queue id> <opening> [--length short]   # tag a variant
    python -P tools/trials/trials.py schedule <set> 2026-10-26                       # same-day slots for a set
    python -P tools/trials/trials.py run          # pull + verdict + learn (the "Hook tests" workflow, every 3 h)
    python -P tools/trials/trials.py pull | verdict | learn | status

A test ("set") = queue items sharing `trial_set` (defaults to `reel`) with 2+ variants. Each variant carries
`opening` (one of OPENINGS) and `length` (full|short), so results add up across reels instead of dying with one test.
Same day: variants post SLOTS_NY apart in the 15:00-16:00 New York window (min_gap 0.25 h between them), all to
non-followers, so every variant gets the same audience and hour. Nothing here approves or posts anything.

Numbers: Instagram API insights per media id (pull, needs IG_ACCESS_TOKEN) -> production/trials/metrics.json, with
Buzzfy's production/control/metrics.json (skip rate, follows) filling gaps. Verdict once every variant is 72 h old:
score = weighted share of the best value per metric (past 3 s, avg watch, views, saves+shares per 1k, follows per 1k);
metrics missing for any variant drop out. Writes production/trials/verdicts.json, LEDGER.md rows, a Telegram note
(production/control/notes.json, sent by control.py notify) and production/trials/learnings.md.
"""
import argparse, datetime as dt, json, os, re, statistics, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import state as store  # noqa: E402

DIR = ROOT / "production" / "trials"
METRICS, VERDICTS, LEARN = DIR / "metrics.json", DIR / "verdicts.json", DIR / "learnings.md"
BUZZFY = ROOT / "production" / "control" / "metrics.json"
NOTES = ROOT / "production" / "control" / "notes.json"
LEDGER = ROOT / "production" / "reels" / "LEDGER.md"
IG = "https://graph.instagram.com/v21.0"

OPENINGS = {
    "contrast": "two kinds of people side by side (Beginners X. Fighters Y.)",
    "reframe": "it's not X, it's Y (Your freeze isn't technique. It's your head.)",
    "story": "drops into a moment (My first fight was stacked against me.)",
    "result": "the outcome or paradox first (I knocked him out. They called it a draw.)",
    "number": "a hard number or age up front (I was 16. His sixth fight.)",
    "question": "asks the viewer (Always sparring someone bigger?)",
    "curiosity": "withholds the payoff (Nobody tells you this about your first fight.)",
    "identity": "who the viewer is (If you still shadowbox at 1am, this is you.)",
    "lesson": "the takeaway first (Steal this from Saenchai.)",
}
LENGTHS = ("full", "short")
SLOTS_NY = ("15:00", "15:20", "15:40", "16:00")
HOURS = 72
WEIGHTS = {"hold": 0.30, "watch": 0.25, "reach": 0.20, "keep": 0.15, "follows": 0.10}
METRIC_LABEL = {"hold": "past 3 s", "watch": "avg watch", "reach": "views", "keep": "saves+shares/1k", "follows": "follows/1k"}
CLOSE = 0.05   # winner within 5% of the runner-up = too close to call


def now():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sets():
    """{set id: [variants sorted by variant letter]} for every set with 2+ variants."""
    out = {}
    for i in store.all("queue"):
        if i.get("variant") in (None, "-") or not (i.get("trial_set") or i.get("reel")):
            continue
        out.setdefault(i.get("trial_set") or i["reel"], []).append(i)
    return {k: sorted(v, key=lambda i: i["variant"]) for k, v in out.items() if len(v) >= 2}


# ------------------------------------------------------------------ labels and slots

def label(qid, opening, length):
    if opening not in OPENINGS:
        sys.exit(f"opening must be one of: {', '.join(OPENINGS)}")
    if not store.get("queue", qid):
        sys.exit(f"no queue item {qid}")
    store.patch("queue", qid, {"opening": opening, "length": length})
    print(f"{qid}: {opening}, {length}")


def ny_to_utc(day, hhmm):
    from zoneinfo import ZoneInfo
    local = dt.datetime.fromisoformat(f"{day}T{hhmm}:00").replace(tzinfo=ZoneInfo("America/New_York"))
    return iso(local.astimezone(dt.timezone.utc))


def schedule(set_id, day):
    items = sets().get(set_id)
    if not items:
        sys.exit(f"no set {set_id} (needs 2+ queue items with that trial_set/reel)")
    if len(items) > len(SLOTS_NY):
        sys.exit(f"{len(items)} variants, only {len(SLOTS_NY)} same-day slots")
    for i, hhmm in zip(items, SLOTS_NY):
        if i.get("status") != "queued":
            print(f"{i['id']}: {i.get('status')}, left alone"); continue
        store.patch("queue", i["id"], {"trial_set": set_id, "not_before": ny_to_utc(day, hhmm),
                                       "min_gap_hours": 0.25 if hhmm != SLOTS_NY[0] else 2.5,
                                       "slot_note": f"hook test, same day: {day} {hhmm} NY (trials.py schedule)"})
        print(f"{i['id']}: {day} {hhmm} NY")


# ------------------------------------------------------------------ numbers

def ig_get(path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    with urllib.request.urlopen(f"{IG}/{path}?{urllib.parse.urlencode(params)}", timeout=30) as r:
        return json.load(r)


def insights(media_id):
    """Every metric we can get; one bad metric name must not cost the others."""
    names = ["views", "reach", "shares", "saved", "ig_reels_avg_watch_time", "reels_skip_rate", "follows"]
    try:
        data = ig_get(f"{media_id}/insights", metric=",".join(names))["data"]
    except Exception:
        data = []
        for n in names:
            try:
                data += ig_get(f"{media_id}/insights", metric=n)["data"]
            except Exception:
                pass
    m = {x["name"]: (x.get("values") or [{}])[0].get("value", x.get("total_value", {}).get("value")) for x in data}
    watch = m.get("ig_reels_avg_watch_time")
    return {"views": m.get("views"), "reach": m.get("reach"), "shares": m.get("shares"), "saves": m.get("saved"),
            "avg_watch_s": round(watch / 1000, 1) if watch is not None else None,
            "skip_rate": m.get("reels_skip_rate"), "follows": m.get("follows"), "at": iso(now())}


def pull():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("pull: no IG_ACCESS_TOKEN, using the numbers already saved"); return
    got = load(METRICS, {})
    decided = set(load(VERDICTS, {}))
    for set_id, items in sets().items():
        if set_id in decided:
            continue
        for i in items:
            if i.get("media_id"):
                got[i["media_id"]] = insights(i["media_id"])
                print(f"{i['id']}: {got[i['media_id']]}")
    save(METRICS, got)


def numbers(media_id):
    """API numbers, Buzzfy's filling anything the API didn't give."""
    api, bz = load(METRICS, {}).get(media_id, {}), load(BUZZFY, {}).get("reels", {}).get(media_id, {})
    return {k: api.get(k) if api.get(k) is not None else bz.get(k)
            for k in ("views", "reach", "shares", "saves", "avg_watch_s", "skip_rate", "follows")}


# ------------------------------------------------------------------ verdict

def score(rows):
    """rows: [{id, n}] -> adds 'parts' (raw values) and 'score' (0-1). Uses only metrics every variant has."""
    for r in rows:
        n, v = r["n"], r["n"].get("views")
        r["parts"] = {"hold": 100 - n["skip_rate"] if n.get("skip_rate") is not None else None,
                      "watch": n.get("avg_watch_s"), "reach": v,
                      "keep": ((n.get("saves") or 0) + (n.get("shares") or 0)) / v * 1000 if v else None,
                      "follows": n["follows"] / v * 1000 if v and n.get("follows") is not None else None}
    used = [k for k in WEIGHTS if all(r["parts"][k] is not None for r in rows) and max(r["parts"][k] for r in rows) > 0]
    total = sum(WEIGHTS[k] for k in used)
    for r in rows:
        r["score"] = round(sum(WEIGHTS[k] * r["parts"][k] / max(x["parts"][k] for x in rows) for k in used) / total, 3)
    return used


def pct(x):
    return f"{x:.0f}%"


def summary(r, median):
    p, out = r["parts"], []
    if p["hold"] is not None:
        out.append(f"{pct(p['hold'])} stayed past 3 s")
    if p["watch"] is not None:
        out.append(f"{p['watch']} s avg watch")
    if p["reach"] is not None:
        out.append(f"{p['reach']:,} views" + (f" ({p['reach'] / median:.2f}x normal)" if median else ""))
    if p["keep"] is not None:
        out.append(f"{p['keep']:.0f} saves+shares per 1k")
    return ", ".join(out)


def verdict():
    verdicts, notes = load(VERDICTS, {}), load(NOTES, [])
    median = load(BUZZFY, {}).get("median_views")
    for set_id, items in sets().items():
        if set_id in verdicts:
            continue
        if any(i.get("status") != "posted" or not i.get("media_id") for i in items):
            continue
        last = max(parse(i["posted_at"]) for i in items)
        if now() - last < dt.timedelta(hours=HOURS):
            continue
        rows = [{"id": i["id"], "n": numbers(i["media_id"])} for i in items]
        if any(r["n"].get("views") is None for r in rows):
            print(f"{set_id}: waiting for numbers"); continue
        used = score(rows)
        rows.sort(key=lambda r: -r["score"])
        win, second = rows[0], rows[1]
        close = (win["score"] - second["score"]) < CLOSE * win["score"]
        by_id = {i["id"]: i for i in items}
        w = by_id[win["id"]]
        verdicts[set_id] = {
            "decided_at": iso(now()), "winner": win["id"], "too_close": close, "metrics_used": used,
            "variants": [{"id": r["id"], "variant": by_id[r["id"]]["variant"], "hook": by_id[r["id"]].get("hook"),
                          "opening": by_id[r["id"]].get("opening"), "length": by_id[r["id"]].get("length", "full"),
                          "media_id": by_id[r["id"]]["media_id"], "permalink": by_id[r["id"]].get("permalink"),
                          "score": r["score"], **r["n"]} for r in rows]}
        why = summary(win, median)
        lose = "; ".join(f"{by_id[r['id']]['variant']} {summary(r, None)}" for r in rows[1:])
        opening = f", {w['opening']} opening" if w.get("opening") else ""
        text = (f"🏆 Hook test done: {set_id} (72 h, {len(rows)} variants)\n\n"
                f"Winner: {w['variant']}{opening}\n\"{w.get('hook', '')}\"\n{why}\n\nThe others: {lose}\n\n"
                + ("Too close to call, so the views decide: " if close else "")
                + f"Share {w['variant']} to your followers now: open it in Instagram, tap the trial reel label, "
                  f"Share to followers. {w.get('permalink', '')}")
        tally = learn(verdicts)
        if tally:
            text += f"\n\nAcross all tests so far: {tally}"
        notes.append({"id": f"trial-{set_id}", "text": text})
        ledger(set_id, verdicts[set_id], median)
        print(text)
    save(VERDICTS, verdicts)
    save(NOTES, notes)


def ledger(set_id, v, median):
    """Append one LEDGER.md row per variant (skip media ids already there) and a pattern line."""
    text = LEDGER.read_text(encoding="utf-8")
    head, sep, tail = text.partition("\n## Patterns so far")
    rows = []
    for x in v["variants"]:
        if x["media_id"] in head:
            continue
        win = x["id"] == v["winner"]
        hold = f"{100 - x['skip_rate']:.0f}% past 3 s, " if x.get("skip_rate") is not None else ""
        watch = f"{x['avg_watch_s']} s watch, " if x.get("avg_watch_s") is not None else ""
        views = f"{x['views']} ({x['views'] / median:.2f}x)" if median else str(x["views"])
        rows.append(f"| {v['decided_at'][:10]} | {set_id} | {x['variant']} | {x['media_id']} | {x.get('hook', '')} | "
                    f"talking head, {x.get('opening') or '?'} opening, {x.get('length')} | own experience | trial | {views} | "
                    f"{x.get('follows') if x.get('follows') is not None else '?'} | {x.get('shares', '')} | {x.get('saves', '')} | | "
                    f"{'**WINNER**' if win else 'no'} | {hold}{watch}score {x['score']} (auto verdict) |")
    if rows:
        head = head.rstrip("\n") + "\n" + "\n".join(rows) + "\n"
    w = next(x for x in v["variants"] if x["id"] == v["winner"])
    line = (f"- {v['decided_at'][:10]} (auto, {set_id}): {w.get('opening') or '?'} opening won "
            f"{'(too close to call) ' if v['too_close'] else ''}over "
            + ", ".join(f"{x.get('opening') or '?'}" for x in v["variants"] if x["id"] != v["winner"]) + ".")
    tail = tail.rstrip("\n") + "\n" + line + "\n"
    LEDGER.write_text(head + sep + tail, encoding="utf-8")


# ------------------------------------------------------------------ learning across tests

def learn(verdicts=None):
    """Tally openings over every decided test -> learnings.md. Returns a one-line summary (or '')."""
    verdicts = verdicts if verdicts is not None else load(VERDICTS, {})
    stats = {}
    for set_id, v in verdicts.items():
        n = len(v["variants"])
        for rank, x in enumerate(v["variants"]):
            s = stats.setdefault(x.get("opening") or "unlabelled", {"tests": 0, "wins": 0, "rank_pct": [], "hold": [], "watch": []})
            s["tests"] += 1
            s["wins"] += int(x["id"] == v["winner"] and not v["too_close"])
            s["rank_pct"].append(1 - rank / (n - 1))   # 1 = first, 0 = last
            if x.get("skip_rate") is not None:
                s["hold"].append(100 - x["skip_rate"])
            if x.get("avg_watch_s") is not None:
                s["watch"].append(x["avg_watch_s"])
    if not stats:
        return ""
    order = sorted(stats, key=lambda k: (-statistics.mean(stats[k]["rank_pct"]), -stats[k]["wins"]))
    md = ["# What opens best: every hook test so far", "",
          f"_Auto-written by tools/trials/trials.py after each verdict ({len(verdicts)} tests). Placing: 100% = always first, "
          "0% = always last. Talking points and new variants should lean on the top rows and keep testing the rest._", "",
          "| Opening | Variants | Clear wins | Avg placing | Median past 3 s | Median avg watch |", "|---|---|---|---|---|---|"]
    for k in order:
        s = stats[k]
        md.append(f"| {k} | {s['tests']} | {s['wins']} | {pct(100 * statistics.mean(s['rank_pct']))} | "
                  f"{pct(statistics.median(s['hold'])) if s['hold'] else '?'} | "
                  f"{str(statistics.median(s['watch'])) + ' s' if s['watch'] else '?'} |")
    md += ["", "## Tests", ""]
    for set_id, v in sorted(verdicts.items(), key=lambda kv: kv[1]["decided_at"]):
        md.append(f"- {v['decided_at'][:10]} {set_id}: " + " > ".join(
            f"{x['variant']} {x.get('opening') or '?'} ({x['score']})" for x in v["variants"])
            + (" (too close)" if v["too_close"] else ""))
    LEARN.parent.mkdir(parents=True, exist_ok=True)
    LEARN.write_text("\n".join(md) + "\n", encoding="utf-8")
    top = order[0]
    return (f"{top} openings place best ({pct(100 * statistics.mean(stats[top]['rank_pct']))} avg placing, "
            f"{stats[top]['wins']} clear wins in {stats[top]['tests']} variants).")


def status():
    verdicts = load(VERDICTS, {})
    for set_id, items in sets().items():
        state = "decided: " + verdicts[set_id]["winner"] if set_id in verdicts else "open"
        print(f"{set_id} [{state}]")
        for i in items:
            print(f"   {i['variant']:5} {i.get('opening') or 'UNLABELLED':10} {i.get('length', 'full'):5} {i.get('status'):8} "
                  f"{i.get('posted_at') or i.get('not_before')}  {i.get('hook', '')}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["label", "schedule", "pull", "verdict", "learn", "run", "status"])
    p.add_argument("args", nargs="*")
    p.add_argument("--length", default="full", choices=LENGTHS)
    a = p.parse_args()
    if a.cmd == "label":
        label(a.args[0], a.args[1], a.length)
    elif a.cmd == "schedule":
        schedule(a.args[0], a.args[1])
    elif a.cmd == "pull":
        pull()
    elif a.cmd == "verdict":
        verdict()
    elif a.cmd == "learn":
        print(learn() or "no decided tests yet")
    elif a.cmd == "run":
        pull(); verdict(); learn()
    else:
        status()
