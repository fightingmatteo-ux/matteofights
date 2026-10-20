"""What is actually working, from the account's own numbers. Read by the threads-writer and platform-captions skills.

    python3 -P tools/threads/report.py            # markdown brief to stdout
    python3 -P tools/threads/report.py --json     # same numbers as JSON

Sources (all in the repo, written by GitHub Actions / the daily Claude check):
  production/threads/results.json   written Threads posts with views/likes/replies/reposts/shares (tools/crosspost/stats.py)
  production/control/platforms.json cross-posted reels per platform, followers
  production/control/metrics.json   Instagram reel metrics (Buzzfy, daily check) joined to production/schedule/queue.json
Rules of the brief: medians, not means (one viral post must not set the strategy); every number shows its n;
anything under MIN_N posts is labelled "too few to call" and must not change the plan on its own.
"""
import json, re, statistics as st, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import state as store  # noqa: E402  (live state: the reel queue)
MIN_N = 5          # posts per group before a pattern counts
MIN_VIEWS = 30     # posts below this are too small to rate per 1k views


def load(p, default):
    p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def per_k(n, views):
    return 1000 * (n or 0) / views if views else 0


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 1) if xs else None


def threads_stats():
    res = load("production/threads/results.json", {})
    rows = []
    for pid, r in res.items():
        v = r.get("views") or 0
        rows.append({**r, "id": pid, "views": v,
                     "reply_k": per_k(r.get("replies"), v), "share_k": per_k((r.get("reposts") or 0) + (r.get("shares") or 0), v),
                     "like_k": per_k(r.get("likes"), v), "first": r.get("text", "").splitlines()[0][:90] if r.get("text") else "",
                     "len": len(r.get("text") or ""), "q": "?" in (r.get("text") or ""), "i": bool(re.search(r"\bI\b|\bI'", r.get("text") or ""))})
    rated = [r for r in rows if r["views"] >= MIN_VIEWS]

    def group(key):
        g = {}
        for r in rated:
            g.setdefault(key(r), []).append(r)
        return {k: {"n": len(v), "views": med(r["views"] for r in v), "replies_per_1k": med(r["reply_k"] for r in v),
                    "shares_per_1k": med(r["share_k"] for r in v), "likes_per_1k": med(r["like_k"] for r in v),
                    "call": "ok" if len(v) >= MIN_N else "too few to call"} for k, v in sorted(g.items(), key=lambda kv: str(kv[0]))}

    length = lambda r: "short (<=140)" if r["len"] <= 140 else "medium (141-300)" if r["len"] <= 300 else "long (>300)"
    top = sorted(rated, key=lambda r: (r["reply_k"], r["views"]), reverse=True)
    return {"posts_measured": len(rows), "posts_rated": len(rated),
            "by_kind": group(lambda r: r.get("kind")), "by_topic": group(lambda r: r.get("topic")), "by_length": group(length),
            "question_vs_statement": group(lambda r: "has a question" if r["q"] else "no question"),
            "first_person": group(lambda r: "uses I" if r["i"] else "second person"),
            "best": [{k: r[k] for k in ("id", "kind", "views", "replies", "reply_k", "first")} for r in top[:5]],
            "worst": [{k: r[k] for k in ("id", "kind", "views", "replies", "reply_k", "first")} for r in top[-3:]] if len(top) > 8 else [],
            "most_viewed": [{k: r[k] for k in ("id", "kind", "views", "first")} for r in sorted(rated, key=lambda r: -r["views"])[:3]]}


def reel_stats():
    q = {i.get("media_id"): i for i in store.all("queue") if i.get("media_id")}
    m = load("production/control/metrics.json", {})
    rows = []
    for mid, r in (m.get("reels") or {}).items():
        it = q.get(mid, {})
        v = r.get("views")
        if not v:
            continue
        rows.append({"hook": it.get("hook") or it.get("id", mid), "format": it.get("format") or ("listicle" if str(it.get("id", "")).startswith("lst-") else "?"),
                     "views": v, "x": r.get("vs_median_x"), "follow_k": per_k(r.get("follows"), v), "share_k": per_k(r.get("shares"), v),
                     "save_k": per_k(r.get("saves"), v)})
    g = {}
    for r in rows:
        g.setdefault(r["format"], []).append(r)
    by_format = {k: {"n": len(v), "views": med(r["views"] for r in v), "x_normal": med(r["x"] for r in v),
                     "follows_per_1k": med(r["follow_k"] for r in v), "shares_per_1k": med(r["share_k"] for r in v),
                     "call": "ok" if len(v) >= MIN_N else "too few to call"} for k, v in g.items()}
    return {"median_views": m.get("median_views"), "reels_measured": len(rows), "by_format": by_format,
            "top_by_follows": [{k: round(r[k], 2) if isinstance(r[k], float) else r[k] for k in ("hook", "format", "views", "follow_k")}
                               for r in sorted(rows, key=lambda r: -r["follow_k"])[:5]],
            "top_by_views": [{k: r[k] for k in ("hook", "format", "views", "x")} for r in sorted(rows, key=lambda r: -r["views"])[:5]]}


def followers():
    p = load("production/control/platforms.json", {}).get("platforms", {})
    return {k: v.get("followers") for k, v in p.items() if isinstance(v, dict)}


def table(title, g, cols):
    if not g:
        return f"### {title}\nNo data yet.\n"
    out = [f"### {title}", "| group | n | " + " | ".join(cols) + " | call |", "|---" * (len(cols) + 3) + "|"]
    for k, v in g.items():
        out.append(f"| {k} | {v['n']} | " + " | ".join(str(v.get(c)) for c in cols) + f" | {v['call']} |")
    return "\n".join(out) + "\n"


def main():
    t, r = threads_stats(), reel_stats()
    data = {"threads": t, "reels": r, "followers": followers()}
    if "--json" in sys.argv:
        print(json.dumps(data, indent=1, ensure_ascii=False))
        return
    print("# What is working (from the account's own numbers)\n")
    print(f"Followers now: {data['followers']}\n")
    print(f"## Threads written posts: {t['posts_measured']} measured, {t['posts_rated']} with >= {MIN_VIEWS} views\n")
    if not t["posts_rated"]:
        print("No rated Threads posts yet. Write from the research defaults in the skill and keep the mix varied so the next report can compare.\n")
    for name, key in (("By kind", "by_kind"), ("By topic tag", "by_topic"), ("By length", "by_length"),
                      ("Question vs statement", "question_vs_statement"), ("First person vs second person", "first_person")):
        print(table(name, t[key], ["views", "replies_per_1k", "shares_per_1k", "likes_per_1k"]))
    if t["best"]:
        print("### Most replies per 1k views (the main Threads lever)")
        for b in t["best"]:
            print(f"- {b['id']} ({b['kind']}): {b['views']} views, {b['replies']} replies -> {b['reply_k']:.1f}/1k. \"{b['first']}\"")
        print()
    if t["worst"]:
        print("### Fewest replies per 1k views (avoid repeating these shapes)")
        for b in t["worst"]:
            print(f"- {b['id']} ({b['kind']}): {b['views']} views, {b['replies']} replies. \"{b['first']}\"")
        print()
    print(f"## Instagram reels: {r['reels_measured']} measured, account median {r['median_views']} views\n")
    print(table("By format", r["by_format"], ["views", "x_normal", "follows_per_1k", "shares_per_1k"]))
    if r["top_by_follows"]:
        print("### Top hooks by follows per 1k views (what grows the account)")
        for h in r["top_by_follows"]:
            print(f"- {h['hook']} ({h['format']}): {h['views']} views, {h['follow_k']}/1k follows")
        print()
    print("Read medians with their n. A group marked 'too few to call' is a hint, not a rule.")


if __name__ == "__main__":
    main()
