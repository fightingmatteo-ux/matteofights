"""Reel ledger: every pull of per-reel metrics -> history -> LEDGER.md with winner calls.

    python -P tools/analytics/ledger.py ingest analytics/snapshots/<date>-buzzfy.json   # or a graph snapshot
    python -P tools/analytics/ledger.py link <media_id> <slug> <V> [--note "..."]        # which reel/variant a post is
    python -P tools/analytics/ledger.py build                                            # rewrite LEDGER.md, print report

Snapshots use the Buzzfy shape ({"pulled_at", "posts": [{id, posted_at, on_grid, views, reach, ...}]}).
`tools/instagram/ig.py insights` writes the same shape from our own Meta app, so both sources mix.
History: analytics/reel-metrics.jsonl (one line per post per pull). Links: production/reels/posted.json.

Reels expose no follows, so the winner is Instagram's own distribution verdict: views at ~72 h.
A variant with clearly more shares (>= 2x and >= 5 more) wins over views; a view gap under 15 % is a
tie, broken by average watch time.
"""
import argparse, json, re, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "analytics" / "reel-metrics.jsonl"
LINKS = ROOT / "production" / "reels" / "posted.json"
LEDGER = ROOT / "production" / "reels" / "LEDGER.md"
METRICS = ["views", "reach", "likes", "comments", "shares", "saves", "avg_watch_time_s", "skip_rate_pct"]
TARGET_H, MIN_H, MAX_H = 72, 48, 120   # a "72 h" reading is the one closest to 72 h inside 48-120 h
START, END = "<!-- ledger:start -->", "<!-- ledger:end -->"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_history():
    if not HISTORY.exists():
        return []
    return [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_links():
    return json.loads(LINKS.read_text(encoding="utf-8")) if LINKS.exists() else {}


def ingest(path):
    snap = json.loads(Path(path).read_text(encoding="utf-8"))
    pulled = snap["pulled_at"]
    seen = {(r["id"], r["pulled_at"]) for r in load_history()}
    new = []
    for p in snap.get("posts", []):
        if p.get("kind", "reel") != "reel" or p.get("views") is None or (p["id"], pulled) in seen:
            continue
        age = (ts(pulled) - ts(p["posted_at"])).total_seconds() / 3600
        rec = {"id": p["id"], "pulled_at": pulled, "age_h": round(age, 1), "posted_at": p["posted_at"],
               "on_grid": p.get("on_grid"), "permalink": p.get("permalink"),
               "caption": (p.get("caption_first_line") or "").strip()}
        rec.update({m: p.get(m) for m in METRICS})
        new.append(rec)
    with HISTORY.open("a", encoding="utf-8") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(new)} readings added from {path} (pulled {pulled}).")


def link(media_id, slug, variant, note):
    links = load_links()
    links[media_id] = {"slug": slug, "variant": variant, **({"note": note} if note else {})}
    LINKS.write_text(json.dumps(links, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{media_id} -> {slug} {variant}")


def best_reading(readings):
    """The reading closest to 72 h if one falls in the window, else the latest one."""
    window = [r for r in readings if MIN_H <= r["age_h"] <= MAX_H]
    if window:
        return min(window, key=lambda r: abs(r["age_h"] - TARGET_H)), True
    return max(readings, key=lambda r: r["pulled_at"]), False


def pick_winner(rows):
    """rows: [(variant, reading)] all >= 48 h. Returns (variant, reason) or (None, reason)."""
    if len(rows) < 2:
        return None, "one variant"
    by_shares = sorted(rows, key=lambda x: x[1].get("shares") or 0, reverse=True)
    s1, s2 = (by_shares[0][1].get("shares") or 0), (by_shares[1][1].get("shares") or 0)
    if s1 >= 2 * s2 and s1 - s2 >= 5:
        return by_shares[0][0], f"shares {s1} vs {s2}"
    by_views = sorted(rows, key=lambda x: x[1].get("views") or 0, reverse=True)
    v1, v2 = (by_views[0][1].get("views") or 0), (by_views[1][1].get("views") or 0)
    if v2 and v1 / v2 >= 1.15:
        return by_views[0][0], f"views {v1:,} vs {v2:,}"
    top = [x for x in by_views if (x[1].get("views") or 0) >= v1 / 1.15]
    w = max(top, key=lambda x: x[1].get("avg_watch_time_s") or 0)
    return w[0], f"views within 15 %, watch {w[1].get('avg_watch_time_s')} s"


def fmt(v, kind=None):
    if v is None:
        return "–"
    if kind == "s":
        return f"{v:.1f}s"
    if kind == "%":
        return f"{v:.0f}%"
    return f"{v:,}"


def build(days):
    hist, links = load_history(), load_links()
    if not hist:
        sys.exit("No history yet. Run `ingest` first.")
    now = max(ts(r["pulled_at"]) for r in hist)
    posts = {}
    for r in hist:
        posts.setdefault(r["id"], []).append(r)
    latest = {pid: max(rs, key=lambda r: r["pulled_at"]) for pid, rs in posts.items()}
    for pid, rs in posts.items():  # grid state: newest reading that knows it (Graph pulls don't)
        known = [r for r in sorted(rs, key=lambda r: r["pulled_at"]) if r.get("on_grid") is not None]
        latest[pid] = {**latest[pid], "on_grid": known[-1]["on_grid"] if known else None}

    # Baseline: median views of settled reels (their ~72 h reading, or lifetime once pulls started later).
    settled = [best_reading(rs)[0]["views"] for rs in posts.values()
               if max(r["age_h"] for r in rs) >= MIN_H and best_reading(rs)[0].get("views")]
    median = statistics.median(settled) if settled else None

    # Winner calls per linked reel (all variants >= 48 h old).
    groups, verdicts = {}, {}
    for pid, l in links.items():
        if pid in posts:
            groups.setdefault(l["slug"], []).append((l["variant"], pid))
    calls = []
    for slug, vs in sorted(groups.items()):
        rows = [(v, best_reading(posts[pid])[0]) for v, pid in vs]
        if all(r["age_h"] >= MIN_H for _, r in rows):
            w, why = pick_winner(rows)
            if w:
                for v, pid in vs:
                    verdicts[pid] = "**WINNER**" if v == w else "lost"
                wpid = next(pid for v, pid in vs if v == w)
                done = latest[wpid].get("on_grid")
                calls.append(f"- `{slug}`: **{w}** wins ({why})." + (" On the grid." if done else " **Share it to the grid.**"))
        else:
            for _, pid in vs:
                verdicts[pid] = "pending"
            young = min(r["age_h"] for _, r in rows)
            calls.append(f"- `{slug}`: waiting, youngest variant is {young:.0f} h old (call at 72 h).")

    grid = [r for r in latest.values() if r.get("on_grid")]
    last_grid = max((ts(r["posted_at"]) for r in grid), default=None)
    gap = (now - last_grid).days if last_grid else None

    cutoff = now.timestamp() - days * 86400
    show = [pid for pid, r in latest.items() if ts(r["posted_at"]).timestamp() >= cutoff or pid in links]
    show.sort(key=lambda pid: latest[pid]["posted_at"], reverse=True)

    lines = [START, f"_Built {now:%Y-%m-%d %H:%M} UTC from `analytics/reel-metrics.jsonl` by `tools/analytics/ledger.py build`. "
             "Do not edit between the markers; edit `production/reels/posted.json` and rebuild._", "",
             "### Status"]
    if gap is not None:
        warn = " **Too long: followers see nothing new. Share a winner today.**" if gap >= 3 else ""
        lines.append(f"- Last grid post: {last_grid:%Y-%m-%d} ({gap} days ago).{warn}")
    if median:
        lines.append(f"- Baseline: median views of a settled reel = {median:,.0f} (over {len(settled)} reels); ×median compares to it.")
    lines += calls or ["- No linked tests yet. `ledger.py link <media_id> <slug> <V>` after posting."]
    unlinked = [pid for pid in show if pid not in links and not latest[pid].get("on_grid")
                and ts(latest[pid]["posted_at"]).timestamp() >= now.timestamp() - 14 * 86400]
    if unlinked:
        lines.append(f"- {len(unlinked)} recent trial reel(s) not linked to a reel folder: "
                     + ", ".join(f"`{p}`" for p in unlinked))
    lines += ["", "| Posted | Reel | V | Caption opens | Grid | At | Views | ×median | Reach | Watch | Skip | Shares | Saves | Comm. | Verdict |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for pid in show:
        r, in_window = best_reading(posts[pid])
        l = links.get(pid, {})
        cap = re.sub(r"[|\n]", " ", r["caption"])[:55]
        cap = f"[{cap}]({r['permalink']})" if r.get("permalink") else cap
        at = f"{r['age_h']:.0f}h" + ("" if in_window or r["age_h"] > MAX_H else " ⏳")
        rel = f"{r['views'] / median:.1f}" if median and r.get("views") else "–"
        lines.append(" | ".join([
            f"| {r['posted_at'][:10]}", f"`{l['slug']}`" if l else "", l.get("variant", ""), cap,
            {True: "✅", False: "trial"}.get(latest[pid].get("on_grid"), "?"), at, fmt(r.get("views")), rel, fmt(r.get("reach")),
            fmt(r.get("avg_watch_time_s"), "s"), fmt(r.get("skip_rate_pct"), "%"), fmt(r.get("shares")),
            fmt(r.get("saves")), fmt(r.get("comments")), verdicts.get(pid, "") + " |"]))
    lines.append(END)

    text = LEDGER.read_text(encoding="utf-8")
    block = "\n".join(lines)
    if START in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        text = text.replace("## Patterns so far", block + "\n\n## Patterns so far")
    LEDGER.write_text(text, encoding="utf-8")
    print("\n".join(l for l in lines[3:] if l.startswith("- ")))
    print(f"LEDGER.md rebuilt: {len(show)} reels.")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest"); i.add_argument("snapshot", nargs="+")
    l = sub.add_parser("link"); l.add_argument("media_id"); l.add_argument("slug"); l.add_argument("variant"); l.add_argument("--note")
    b = sub.add_parser("build"); b.add_argument("--days", type=int, default=45, help="show reels posted in the last N days")
    a = p.parse_args()
    if a.cmd == "ingest":
        for s in a.snapshot:
            ingest(s)
    elif a.cmd == "link":
        link(a.media_id, a.slug, a.variant, a.note)
    else:
        build(a.days)


if __name__ == "__main__":
    main()
