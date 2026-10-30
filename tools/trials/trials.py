"""Hook tests on talking heads, the "trial reel maxing" loop (@browniegainz reference, 2026-10-30):

  round 1  5 hooks of the same reel, all trial reels the same day (15:00-16:00 NY), verdict at 24 h
  round 2  the Edit worker re-cuts the round-1 winner 5 ways (EDITS), aimed at where viewers drop off (skip rate,
           avg watch, and Matteo's retention-graph note if he sends one); same day slots, verdict at 24 h
  then     only the round-2 verdict tells Matteo to share to the grid (or to share the round-1 cut if no re-edit beat it)

Running tallies of which OPENING types (round 1) and which EDITS (round 2) win, so results outlive one reel.

    python -P tools/trials/trials.py label <queue id> <opening|edit> [--length short] [--parent <queue id>]
    python -P tools/trials/trials.py schedule <set> 2026-10-26                       # same-day slots for a set
    python -P tools/trials/trials.py run          # pull + verdict + learn (the "Hook tests" workflow)
    python -P tools/trials/trials.py pull | verdict | learn | status

A test ("set") = queue items sharing `trial_set` (defaults to `reel`) with 2+ variants. Round-1 variants carry
`opening` (one of OPENINGS) and `length`; round-2 variants carry `round: 2`, `edit` (one of EDITS) and `parent` (the
round-1 winner's queue id), in the set `<round-1 set>-r2`. Variants post SLOTS_NY apart in the 15:00-16:00 New York
window, all to non-followers, so every variant gets the same audience and hour. Nothing here approves or posts.

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
EDITS = {   # round 2: ways to re-cut a winner, each aimed at a drop-off
    "trim-open": "start on the first strong word: cut breaths, 'so', the walk-in (skip rate is the leak)",
    "first-frame": "open on the most striking frame (tape, impact, b-roll) with the hook line over it",
    "text-hook": "same cut, a new on-screen hook text (sharper, shorter, the top opening type)",
    "cut-the-dip": "remove the beat where viewers leave (retention note, or the point at avg watch)",
    "shorter": "under 20 s: hook, the one point that matters, payoff",
    "faster": "tighter: every pause out, jump cuts, b-roll every 2-3 s through the middle",
    "payoff-first": "flash the payoff (the KO, the result) in the first 2 s, then rewind into the story",
    "loop-end": "last line runs into the first, so the replay feels like one take",
}
LENGTHS = ("full", "short")
SLOTS_NY = ("15:00", "15:15", "15:30", "15:45", "16:00")
HOURS = 24
ROUNDS = 2          # round 2 = the re-edit round; the playbook allows more, the edit worker's 3 runs a day don't
HOLD_RETENTION_H = 4   # round-2 job waits this long for Matteo's retention-graph note before the worker cuts
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

def label(qid, kind, length, parent=None):
    if not store.get("queue", qid):
        sys.exit(f"no queue item {qid}")
    if kind in EDITS:
        if not parent:
            sys.exit("a round-2 edit needs --parent <round-1 winner queue id>")
        p = store.get("queue", parent) or {}
        set_id = (p.get("trial_set") or p.get("reel")) + "-r2"
        store.patch("queue", qid, {"edit": kind, "round": 2, "parent": parent, "trial_set": set_id,
                                   "opening": p.get("opening"), "length": length})
        print(f"{qid}: round 2, {kind}, set {set_id}"); return
    if kind not in OPENINGS:
        sys.exit(f"must be an opening ({', '.join(OPENINGS)}) or an edit ({', '.join(EDITS)})")
    store.patch("queue", qid, {"opening": kind, "length": length})
    print(f"{qid}: {kind}, {length}")


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
        r2 = any(i.get("round") == 2 for i in items)
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
            "round": 2 if r2 else 1,
            "variants": [{"id": r["id"], "variant": by_id[r["id"]]["variant"], "hook": by_id[r["id"]].get("hook"),
                          "opening": by_id[r["id"]].get("opening"), "length": by_id[r["id"]].get("length", "full"),
                          "edit": by_id[r["id"]].get("edit"), "parent": by_id[r["id"]].get("parent"),
                          "media_id": by_id[r["id"]]["media_id"], "permalink": by_id[r["id"]].get("permalink"),
                          "score": r["score"], **r["n"]} for r in rows]}
        why = summary(win, median)
        lose = "; ".join(f"{by_id[r['id']]['variant']} {summary(r, None)}" for r in rows[1:])
        opening = f", {w['edit']} edit" if r2 else (f", {w['opening']} opening" if w.get("opening") else "")
        head = (f"🏆 {'Re-edit round' if r2 else 'Hook test'} done: {set_id} ({HOURS} h, {len(rows)} variants)\n\n"
                f"Winner: {w['variant']}{opening}\n\"{w.get('hook', '')}\"\n{why}\n\nThe others: {lose}\n\n"
                + ("Too close to call, so the views decide. " if close else ""))
        if r2:
            share = beats_parent(win, w)
            text = head + (f"Share {w['variant']} to your followers now: open it in Instagram, tap the trial reel label, "
                           f"Share to followers. {w.get('permalink', '')}" if share is not False else
                           f"No re-edit beat the round-1 cut ({share_note(w)}), so share that one instead: "
                           f"{(store.get('queue', w['parent']) or {}).get('permalink', '')}")
            if w.get("no_grid"):
                text = head + "This reel is marked not for the grid (no_grid), so nothing to share."
        else:
            iterate(set_id, w, win, verdicts)
            text = head + (f"Round 2 next: I re-cut {w['variant']} 5 ways, aimed at where people drop off, and queue them "
                           f"unapproved for your yes. Want the cuts to follow the exact drop-offs? In the next "
                           f"{HOLD_RETENTION_H} h open the reel's Insights, look at the retention graph and send where it "
                           f"drops (a Studio revision note on {w['id']}, e.g. \"drops at 3 s and 12 s\", or a screenshot "
                           f"upload with the note \"retention {w['id']}\"). Don't share it to the grid yet. "
                           f"{w.get('permalink', '')}")
        tally = learn(verdicts)
        if tally:
            text += f"\n\nAcross all tests so far: {tally}"
        notes.append({"id": f"trial-{set_id}", "text": text})
        ledger(set_id, verdicts[set_id], median)
        print(text)
    save(VERDICTS, verdicts)
    save(NOTES, notes)


def beats_parent(win, w):
    """Round-2 winner vs the round-1 cut it came from: True/False on hold + watch, None when numbers are missing."""
    p = store.get("queue", w.get("parent") or "") or {}
    if not p.get("media_id"):
        return None
    pn, wn = numbers(p["media_id"]), win["n"]
    got = [(wn[k] - pn[k]) * (-1 if k == "skip_rate" else 1) for k in ("skip_rate", "avg_watch_s")
           if wn.get(k) is not None and pn.get(k) is not None]
    return sum(1 for d in got if d > 0) >= 1 if got else None


def share_note(w):
    p = store.get("queue", w.get("parent") or "") or {}
    return f"round-1 {p.get('variant', '?')} held viewers better"


def diagnose(win, verdicts):
    """Where the winner leaks, from its numbers against every past variant: 'opening' or 'middle'."""
    holds = [100 - x["skip_rate"] for v in verdicts.values() for x in v["variants"] if x.get("skip_rate") is not None]
    hold = win["parts"].get("hold")
    if hold is not None and holds and hold < statistics.median(holds):
        return "opening"
    return "middle"


def iterate(set_id, w, win, verdicts):
    """Round 1 decided: write the re-edit brief and open a D1 request the Edit worker picks up after the hold."""
    if ROUNDS < 2:
        return
    leak = diagnose(win, verdicts)
    edits = (["trim-open", "first-frame", "text-hook", "cut-the-dip", "shorter"] if leak == "opening"
             else ["cut-the-dip", "faster", "shorter", "payoff-first", "trim-open"])
    n = win["n"]
    brief = [f"# Round 2: re-cut {w['id']} 5 ways", "",
             f"Round-1 winner of `{set_id}` ({w.get('opening') or '?'} opening): \"{w.get('hook', '')}\"",
             f"Numbers at {HOURS} h: skip rate {n.get('skip_rate')}%, avg watch {n.get('avg_watch_s')} s, "
             f"{n.get('views')} views. Main leak: **{leak}**"
             + (" (fewer people than usual stay past 3 s)." if leak == "opening" else
                f" (people stay for the hook, then leave around {n.get('avg_watch_s')} s)."),
             "", "Before cutting, check for Matteo's retention note (Studio revision on this reel, or an upload with the "
             "note `retention <id>`). If he sent drop-off times, `cut-the-dip` and `faster` work on those exact seconds.",
             "", "Five cuts, one per variant, everything else unchanged so the test reads clean:", ""]
    brief += [f"- {chr(65 + k)}: `{e}`: {EDITS[e]}" for k, e in enumerate(edits)]
    brief += ["", f"Queue ids `{w['id']}-r2-<letter>`, label each with "
              f"`trials.py label <id> <edit> --parent {w['id']}`, then `trials.py schedule {set_id}-r2 <next free day>`."]
    path = DIR / "iterate" / f"{set_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(brief) + "\n", encoding="utf-8")
    hold = iso(now() + dt.timedelta(hours=HOLD_RETENTION_H))
    try:
        from edit import requests_cli
        requests_cli.db().put("request", f"iterate-{set_id}", {
            "status": "open", "kind_detail": "iterate", "target": w["id"], "text": "\n".join(brief),
            "brief": str(path.relative_to(ROOT)), "hold_until": hold, "at": iso(now())})
        print(f"{set_id}: round-2 request opened for the edit worker (after {hold})")
    except Exception as e:   # no D1 here: the brief file still tells the next session what to cut
        print(f"{set_id}: round-2 brief written, D1 request not opened ({e})")


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
                    f"talking head, {('round 2, ' + str(x.get('edit')) + ' edit') if v.get('round') == 2 else (x.get('opening') or '?') + ' opening'}, "
                    f"{x.get('length')} | own experience | trial | {views} | "
                    f"{x.get('follows') if x.get('follows') is not None else '?'} | {x.get('shares', '')} | {x.get('saves', '')} | | "
                    f"{'**WINNER**' if win else 'no'} | {hold}{watch}score {x['score']} (auto verdict) |")
    if rows:
        head = head.rstrip("\n") + "\n" + "\n".join(rows) + "\n"
    w = next(x for x in v["variants"] if x["id"] == v["winner"])
    kind = "edit" if v.get("round") == 2 else "opening"
    line = (f"- {v['decided_at'][:10]} (auto, {set_id}): {w.get(kind) or '?'} {kind} won "
            f"{'(too close to call) ' if v['too_close'] else ''}over "
            + ", ".join(f"{x.get(kind) or '?'}" for x in v["variants"] if x["id"] != v["winner"]) + ".")
    tail = tail.rstrip("\n") + "\n" + line + "\n"
    LEDGER.write_text(head + sep + tail, encoding="utf-8")


# ------------------------------------------------------------------ learning across tests

def learn(verdicts=None):
    """Tally openings over every decided test -> learnings.md. Returns a one-line summary (or '')."""
    verdicts = verdicts if verdicts is not None else load(VERDICTS, {})
    stats, edits = {}, {}
    for set_id, v in verdicts.items():
        n = len(v["variants"])
        for rank, x in enumerate(v["variants"]):
            if v.get("round") == 2:
                e = edits.setdefault(x.get("edit") or "unlabelled", {"tests": 0, "wins": 0, "rank_pct": []})
                e["tests"] += 1
                e["wins"] += int(x["id"] == v["winner"] and not v["too_close"])
                e["rank_pct"].append(1 - rank / (n - 1))
                continue
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
    if edits:
        md += ["", "## Round 2: which re-edit wins", "", "| Edit | Variants | Clear wins | Avg placing |", "|---|---|---|---|"]
        for k in sorted(edits, key=lambda k: -statistics.mean(edits[k]["rank_pct"])):
            md.append(f"| {k} | {edits[k]['tests']} | {edits[k]['wins']} | {pct(100 * statistics.mean(edits[k]['rank_pct']))} |")
    md += ["", "## Tests", ""]
    for set_id, v in sorted(verdicts.items(), key=lambda kv: kv[1]["decided_at"]):
        md.append(f"- {v['decided_at'][:10]} {set_id}: " + " > ".join(
            f"{x['variant']} {(x.get('edit') if v.get('round') == 2 else x.get('opening')) or '?'} ({x['score']})"
            for x in v["variants"])
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
            print(f"   {i['variant']:5} {i.get('edit') or i.get('opening') or 'UNLABELLED':11} {i.get('length', 'full'):5} {i.get('status'):8} "
                  f"{i.get('posted_at') or i.get('not_before')}  {i.get('hook', '')}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["label", "schedule", "pull", "verdict", "learn", "run", "status"])
    p.add_argument("args", nargs="*")
    p.add_argument("--length", default="full", choices=LENGTHS)
    p.add_argument("--parent")
    a = p.parse_args()
    if a.cmd == "label":
        label(a.args[0], a.args[1], a.length, a.parent)
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
