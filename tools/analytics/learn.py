"""Learning loop: every posted reel's numbers, kept for good, so every next hook, edit and format is picked from
results instead of guesses. Runs in the Platform stats workflow (every 2 h, Instagram token already there).

    python3 -P tools/analytics/learn.py            # pull, checkpoint, decide hook tests, refresh metrics + ledger

What it writes:
  analytics/reel-history.json        per reel: 24h / 72h / 7d checkpoints + latest numbers, daily followers,
                                     decided hook tests. The permanent record (platforms.json keeps only 10 days).
  production/control/metrics.json    reels{media_id} = latest numbers + vs_median_x. Feeds the style lab
                                     (tools/style/lab.py), tools/threads/report.py ("what is working", read by the
                                     caption/hook skills) and the dashboard. Buzzfy-only fields (follows) are kept.
  production/control/notes.json      winner calls -> Telegram ("B won ... share it to your grid")
  production/reels/LEDGER.md         auto results table between the ledger:auto markers
Winner rule (hook tests = queue items sharing "reel" with variants A/B/C), decided once every variant is >= 72 h:
views at ~72 h = Instagram's distribution verdict; a variant with >= 2x the shares (and >= 5 more) wins over views;
a view gap under 15 % is a tie broken by average watch time. Read-only on Instagram; never posts.
"""
import datetime as dt, json, os, statistics, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "production" / "schedule" / "queue.json"
HISTORY = ROOT / "analytics" / "reel-history.json"
CTL = ROOT / "production" / "control"
LEDGER = ROOT / "production" / "reels" / "LEDGER.md"
IG = "https://graph.instagram.com/v23.0"
METRICS = "reach,views,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time"
CHECKPOINTS = {"24h": 24, "72h": 72, "7d": 168}
TRACK_DAYS = 14          # after this a reel's numbers barely move; stop spending API calls on it
REFRESH_H = 12           # settled reels (> 72 h) are re-pulled at most this often
START, END = "<!-- ledger:auto:start -->", "<!-- ledger:auto:end -->"


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
    p.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def get(path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    try:
        with urllib.request.urlopen(f"{IG}/{path}?{urllib.parse.urlencode(params)}", timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode(errors="replace")[:200]}


def insights(media_id):
    r = get(f"{media_id}/insights", metric=METRICS)
    if "error" in r:
        print(f"  {media_id}: no insights ({r['error'][:120]})")
        return None
    v = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in r.get("data", [])}
    skip = get(f"{media_id}/insights", metric="reels_skip_rate")  # newer metric; not on every reel
    for extra in ("follows", "profile_visits"):  # documented for feed posts; asked per reel in case Meta returns them
        r2 = get(f"{media_id}/insights", metric=extra)
        if "error" not in r2:
            v[extra] = (r2.get("data") or [{}])[0].get("values", [{}])[0].get("value")
    watch = v.get("ig_reels_avg_watch_time")
    return {"views": v.get("views"), "reach": v.get("reach"), "likes": v.get("likes"), "comments": v.get("comments"),
            "shares": v.get("shares"), "saves": v.get("saved"), "interactions": v.get("total_interactions"),
            "follows": v.get("follows"), "profile_visits": v.get("profile_visits"),
            "avg_watch_s": round(watch / 1000, 1) if watch is not None else None,
            "skip_rate": None if "error" in skip else (skip.get("data") or [{}])[0].get("values", [{}])[0].get("value")}


def pull(queue, hist, t):
    posted = [i for i in queue if i.get("status") == "posted" and i.get("media_id") and i.get("posted_at")]
    pulled = 0
    for it in posted:
        age_h = (t - parse(it["posted_at"])).total_seconds() / 3600
        h = hist["reels"].setdefault(it["media_id"], {"id": it["id"], "posted_at": it["posted_at"], "checkpoints": {}})
        h.update({k: it[k] for k in ("reel", "variant", "hook", "format", "permalink") if it.get(k)})
        # a checkpoint only counts near its mark: a reel first seen at 8 days gets no fake "24 h" numbers
        due = [c for c, hrs in CHECKPOINTS.items() if hrs <= age_h <= hrs * 1.5 and c not in h["checkpoints"]]
        last = parse(h["latest"]["at"]) if h.get("latest") else None
        fresh = last and (t - last).total_seconds() < REFRESH_H * 3600
        if age_h > TRACK_DAYS * 24 and not due or (age_h > 72 and fresh and not due):
            continue
        m = insights(it["media_id"])
        if not m:
            continue
        pulled += 1
        m["at"] = iso(t)
        h["latest"] = m
        for c in due:  # first pull past the mark; with a 2 h cadence that's within ~2 h of it
            h["checkpoints"][c] = {**m, "age_h": round(age_h, 1)}
    return pulled


def at72(h):
    return h["checkpoints"].get("72h") or h.get("latest") or {}


def decide(hist, t):
    """Call each hook test once all its variants are >= 72 h old. Returns new decisions."""
    tests = {}
    for mid, h in hist["reels"].items():
        if h.get("reel") and h.get("variant") not in (None, "", "-"):
            tests.setdefault(h["reel"], []).append((mid, h))
    new = []
    for reel, vs in tests.items():
        old = lambda h: (t - parse(h["posted_at"])).total_seconds() >= 72 * 3600 and h.get("latest")
        if reel in hist["decisions"] or len(vs) < 2 or not all(old(h) for _, h in vs):
            continue
        rows = sorted(vs, key=lambda x: at72(x[1]).get("views") or 0, reverse=True)
        top, second = rows[0], rows[1]
        win, why = top, "most views at 72 h"
        sh = lambda x: at72(x[1]).get("shares") or 0
        sharer = max(rows, key=sh)
        if sharer is not top and sh(sharer) >= 2 * max(sh(top), 1) and sh(sharer) - sh(top) >= 5:
            win, why = sharer, "2x the shares"
        else:
            v1, v2 = at72(top[1]).get("views") or 0, at72(second[1]).get("views") or 0
            if v1 and (v1 - v2) / v1 < 0.15:
                w = lambda x: at72(x[1]).get("avg_watch_s") or 0
                win = max((top, second), key=w)
                why = "views within 15 %, longer average watch"
        d = {"winner": win[1]["variant"], "media_id": win[0], "why": why, "decided_at": iso(t),
             "variants": {h["variant"]: {k: at72(h).get(k) for k in ("views", "shares", "saves", "avg_watch_s")}
                          for _, h in vs}}
        hist["decisions"][reel] = d
        new.append((reel, d))
    return new


def refresh_metrics(hist, t):
    """Keep production/control/metrics.json current for every tracked reel (it used to need a manual Buzzfy check)."""
    m = load(CTL / "metrics.json", {})
    settled = sorted((h for h in hist["reels"].values() if h.get("latest") and
                      (t - parse(h["posted_at"])).total_seconds() > 48 * 3600), key=lambda h: h["posted_at"])[-14:]
    if len(settled) >= 5:
        m["median_views"] = statistics.median(at72(h).get("views") or 0 for h in settled)
        m["median_basis"] = f"own Graph API: views at 72 h, latest {len(settled)} reels older than 48 h"
    med = m.get("median_views")
    reels = m.setdefault("reels", {})
    for mid, h in hist["reels"].items():
        x = h.get("latest")
        if not x:
            continue
        r = reels.setdefault(mid, {})
        r.update({k: x.get(k) for k in ("views", "reach", "shares", "saves", "comments", "likes", "avg_watch_s")})
        if x.get("skip_rate") is not None:
            r["skip_rate"] = x["skip_rate"]
        if x.get("follows") is not None:
            r["follows"] = x["follows"]
        r.setdefault("follows", None)  # if Instagram won't give it per reel, a Buzzfy pull fills it and it's kept
        r["vs_median_x"] = round(x["views"] / med, 2) if med and x.get("views") is not None else None
        r["provisional"] = (t - parse(h["posted_at"])).total_seconds() < 72 * 3600
    m["updated"] = iso(t)
    save(CTL / "metrics.json", m)


def tell(new):
    notes = load(CTL / "notes.json", [])
    for reel, d in new:
        parts = [f"{v}: {s['views'] or 0:,} views, {s['shares'] or 0} shares" for v, s in sorted(d["variants"].items())]
        notes.append({"id": f"win-{reel}", "text": f"🏆 {reel}: {d['winner']} won ({d['why']}).\n" + "\n".join(parts) +
                      f"\n\nShare {d['winner']} to your grid in the Instagram app (trial reels can't be shared by the API)."})
    if new:
        save(CTL / "notes.json", notes)


def ledger(hist):
    rows = sorted(hist["reels"].values(), key=lambda h: h["posted_at"], reverse=True)
    out = [START, "### Auto results (tools/analytics/learn.py, every 2 h; don't edit by hand)", "",
           "| Posted | Reel / hook | V | Views now | 24h | 72h | 7d | Shares | Saves | Avg watch | Skip % | Winner |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for h in rows:
        c, x = h["checkpoints"], h.get("latest") or {}
        test = h.get("variant") not in (None, "", "-")
        name = (h.get("reel") if test else h.get("hook") or h["id"])[:60]
        won = hist["decisions"].get(h.get("reel"), {}).get("winner")
        mark = "🏆" if won and won == h.get("variant") else ("" if not won else "·")
        out.append(f"| {h['posted_at'][:10]} | {name} | {h.get('variant', '') if test else ''} | {x.get('views', '')} | {c.get('24h', {}).get('views', '')} | "
                   f"{c.get('72h', {}).get('views', '')} | {c.get('7d', {}).get('views', '')} | {x.get('shares', '')} | "
                   f"{x.get('saves', '')} | {x.get('avg_watch_s', '')} | {x.get('skip_rate') or ''} | {mark} |")
    out.append(END)
    text = LEDGER.read_text(encoding="utf-8")
    block = "\n".join(out)
    text = text[:text.index(START)] + block + text[text.index(END) + len(END):] if START in text else text.rstrip() + "\n\n" + block + "\n"
    LEDGER.write_text(text, encoding="utf-8")


def main():
    if not os.environ.get("IG_ACCESS_TOKEN"):
        print("No IG_ACCESS_TOKEN: learning loop skipped")
        return
    t = now()
    queue = load(QUEUE, {"items": []})["items"]
    hist = load(HISTORY, {"reels": {}, "decisions": {}, "followers": {}})
    me = get("me", fields="followers_count")
    if me.get("followers_count") is not None:
        hist["followers"][t.strftime("%Y-%m-%d")] = me["followers_count"]
    n = pull(queue, hist, t)
    new = decide(hist, t)
    save(HISTORY, hist)
    refresh_metrics(hist, t)
    tell(new)
    ledger(hist)
    print(f"learn: pulled {n} reels, {len(hist['reels'])} tracked, {len(new)} new winner call(s)")


if __name__ == "__main__":
    sys.exit(main())
