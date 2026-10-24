"""Weekly carousel review: how every @matteofights carousel did, so they stop underperforming.

    python3 -P tools/carousel/report.py [--days 120]

Reads every carousel on the account (old ones too, as the baseline) through the Instagram API and pulls its
insights. Writes production/carousels/results.json (kept for good, one row per carousel) and
analytics/reports/<date>-carousels.md. Instagram has no skip rate or per-slide swipe data for carousels in the API,
so the report uses what it does give:
  - views per account reached: Instagram re-serves a carousel at slide 2 to people who didn't swipe, and each
    re-serve counts as a view. Higher = more people saw more than the cover. Our best proxy for swipe-through.
  - saves, shares, follows and profile visits per 1k reached: did it earn a keep, a send or a follow.
  - each number vs the median of our carousels (and reach vs the median reel), split by hook source, look and
    animated cover.
Claude reads the report every Monday (after the scout) and writes what it changes into production/carousels/LEARNINGS.md.
Needs IG_ACCESS_TOKEN.
"""
import argparse, datetime as dt, json, os, statistics, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "production" / "carousels"
IG = "https://graph.instagram.com/v21.0"
METRICS = ["reach", "views", "saved", "shares", "likes", "comments", "follows", "profile_visits", "total_interactions"]


def get(url, **params):
    q = urllib.parse.urlencode({**params, "access_token": os.environ["IG_ACCESS_TOKEN"]})
    return json.load(urllib.request.urlopen(f"{url}?{q}", timeout=60))


def insights(mid):
    """One call for all metrics; if Meta refuses one, fall back to asking metric by metric."""
    try:
        data = get(f"{IG}/{mid}/insights", metric=",".join(METRICS))["data"]
    except urllib.error.HTTPError:
        data = []
        for m in METRICS:
            try:
                data += get(f"{IG}/{mid}/insights", metric=m)["data"]
            except urllib.error.HTTPError:
                pass
    return {x["name"]: (x.get("values") or [{}])[0].get("value") for x in data}


def media(days):
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    out = []
    page = get(f"{IG}/me/media", fields="id,media_type,media_product_type,timestamp,caption,permalink", limit=50)
    while True:
        for m in page.get("data", []):
            if dt.datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) < since:
                return out
            out.append(m)
        nxt = page.get("paging", {}).get("next")  # carries its own query, token included
        if not nxt:
            return out
        page = json.load(urllib.request.urlopen(nxt, timeout=60))


def per_k(v, reach):
    return round(1000 * v / reach, 1) if v is not None and reach else None


def med(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(vals) if vals else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=120)
    a = p.parse_args()
    posts = {x["media_id"]: x for x in json.loads((DIR / "posts.json").read_text(encoding="utf-8"))["posts"] if x.get("media_id")}
    all_media = media(a.days)
    reels_reach = []
    rows = []
    for m in all_media:
        if m["media_type"] == "CAROUSEL_ALBUM":
            ins = insights(m["id"])
            reach = ins.get("reach")
            ours = posts.get(m["id"], {})
            rows.append({
                "media_id": m["id"], "posted": m["timestamp"], "permalink": m.get("permalink"),
                "hook": (m.get("caption") or "").strip().split("\n")[0][:100],
                "post_id": ours.get("id"), "hook_ref": ours.get("hook_ref"), "look": ours.get("look"),
                "animated": ours.get("animated"), **{k: ins.get(k) for k in METRICS},
                "views_per_reach": round(ins["views"] / reach, 2) if ins.get("views") and reach else None,
                "saves_per_k": per_k(ins.get("saved"), reach), "shares_per_k": per_k(ins.get("shares"), reach),
                "follows_per_k": per_k(ins.get("follows"), reach), "visits_per_k": per_k(ins.get("profile_visits"), reach)})
        elif m.get("media_product_type") == "REELS" and len(reels_reach) < 20:
            r = insights(m["id"]).get("reach")
            if r:
                reels_reach.append(r)

    keys = ["reach", "views_per_reach", "saves_per_k", "shares_per_k", "follows_per_k", "visits_per_k"]
    base = {k: med(rows, k) for k in keys}
    reel_med = statistics.median(reels_reach) if reels_reach else None
    for r in rows:
        r["vs_median"] = {k: round(r[k] / base[k], 2) for k in keys if r.get(k) is not None and base.get(k)}
        r["reach_vs_reels"] = round(r["reach"] / reel_med, 2) if r.get("reach") and reel_med else None

    results_path = DIR / "results.json"
    kept = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else {"carousels": {}}
    for r in rows:
        kept["carousels"][r["media_id"]] = r
    kept.update(updated=dt.date.today().isoformat(), median=base, reel_median_reach=reel_med)
    results_path.write_text(json.dumps(kept, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    def fmt(v):
        return "-" if v is None else f"{v:,}" if isinstance(v, int) else f"{v}"

    lines = [f"# Carousels, {dt.date.today().isoformat()}", "",
             f"{len(rows)} carousels in the last {a.days} days. Median reach {fmt(base['reach'])} vs median reel reach "
             f"{fmt(reel_med)}. No skip rate exists for carousels in the API; views per reach is the swipe-through proxy.", "",
             "| Posted | Hook | Source | Look | Anim | Reach | x reels | Views/reach | Saves/1k | Shares/1k | Follows/1k | Visits/1k |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: r["posted"], reverse=True):
        lines.append(f"| {r['posted'][:10]} | [{r['hook'].replace('|', '/')[:60]}]({r['permalink']}) | {r['hook_ref'] or '-'} | "
                     f"{r['look'] or '-'} | {'yes' if r['animated'] else '-'} | {fmt(r['reach'])} | {fmt(r['reach_vs_reels'])} | "
                     f"{fmt(r['views_per_reach'])} | {fmt(r['saves_per_k'])} | {fmt(r['shares_per_k'])} | "
                     f"{fmt(r['follows_per_k'])} | {fmt(r['visits_per_k'])} |")
    for field in ("hook_ref", "look", "animated"):
        groups = {}
        for r in rows:
            if r.get("post_id"):
                groups.setdefault(str(r.get(field)), []).append(r)
        if len(groups) > 1:
            lines += ["", f"## By {field}", "", "| Value | n | Reach | Views/reach | Saves/1k | Follows/1k |", "|---|---|---|---|---|---|"]
            for g, rs in sorted(groups.items()):
                lines.append(f"| {g} | {len(rs)} | {fmt(med(rs, 'reach'))} | {fmt(med(rs, 'views_per_reach'))} | "
                             f"{fmt(med(rs, 'saves_per_k'))} | {fmt(med(rs, 'follows_per_k'))} |")
    out = ROOT / "analytics" / "reports" / f"{dt.date.today().isoformat()}-carousels.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} carousels -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
