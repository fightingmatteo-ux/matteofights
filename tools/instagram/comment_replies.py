"""Comment auto-replies in Matteo's voice, written by Claude Code on Matteo's subscription (no API key).

Matteo 2026-11-01: "fully automate comments, don't sound robotic, under 8 words, nice + value, stand your ground with
dickheads", and use his Claude subscription (CLAUDE_CODE_OAUTH_TOKEN), not an Anthropic API key. Runs in the
"Comment replies" workflow every 3 h (CLAUDE.md Actions rule) and on demand:

    python3 -P tools/instagram/comment_replies.py collect work/pending.json   # new comments that need a reply
    python3 -P tools/instagram/comment_replies.py prompt  work/pending.json work/prompt.txt
    claude -p --model haiku < work/prompt.txt > work/replies.txt              # the workflow does this
    python3 -P tools/instagram/comment_replies.py post    work/pending.json work/replies.txt

Voice and rules: tools/instagram/reply-voice.md. Which comments: on reels posted in the last 14 days (our media list +
posted queue items, so trial reels count), not ours, not "protocol" (the PROTOCOL webhook answers those), not already
answered by us, not yet in state kind "ig_reply". Follow-ups inside a thread we replied to get one more answer, max 2
per person per reel. Every reply is copied to Telegram so Matteo can delete a bad one. Kill switch: repo variable
AUTO_REPLY=off (the workflow skips).
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import state  # noqa: E402

IG = "https://graph.instagram.com/v21.0"
OWN = "matteofights"
KEYWORD = re.compile(r"\b(protocol|plan)\b", re.I)  # the auto-DM webhook answers these
MAX_PER_RUN = 60
GUARD = re.compile(r"https?:|www\.|\b(ai|bots?|automat\w*|chatgpt|claude)\b", re.I)


def ig(path, method="GET", **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    q = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{IG}/{path}?{q}")
    else:
        req = urllib.request.Request(f"{IG}/{path}", data=q.encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} {e.read().decode(errors='replace')[:300]}") from None


def now():
    return dt.datetime.now(dt.timezone.utc)


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00").replace("+0000", "+00:00"))


def recent_media():
    out = {}
    try:
        for m in ig("me/media", fields="id,caption,timestamp", limit=30).get("data", []):
            out[m["id"]] = m
    except Exception as e:  # noqa: BLE001
        print("media list:", e)
    for i in state.all("queue"):
        if i.get("media_id") and i.get("posted_at") and i["media_id"] not in out:
            out[i["media_id"]] = {"id": i["media_id"], "timestamp": i["posted_at"],
                                  "caption": (ROOT / i["caption_file"]).read_text() if i.get("caption_file") and (ROOT / i["caption_file"]).exists() else i.get("hook", "")}
    cut = now() - dt.timedelta(days=14)
    return [m for m in out.values() if ts(m["timestamp"]) > cut]


def collect(out_path):
    done = {r.get("comment") for r in state.all("ig_reply")}
    per_user = {}
    for r in state.all("ig_reply"):
        if r.get("reply"):
            per_user[(r.get("media"), r.get("user"))] = per_user.get((r.get("media"), r.get("user")), 0) + 1
    pending = []
    for m in recent_media():
        cs = None
        for f in ("id,text,username,from,timestamp,replies{id,text,username,from,timestamp}",
                  "id,text,username,timestamp,replies{id,text,username,timestamp}", "id,text,username,timestamp"):
            try:
                cs = ig(f"{m['id']}/comments", fields=f, limit=100).get("data", [])
                break
            except Exception as e:  # noqa: BLE001
                print(m["id"], "comments:", e)
        if cs is None:
            continue
        fresh = now() - dt.timedelta(days=3)   # never dig up old comments
        for x in cs + [r for c in cs for r in (c.get("replies") or {}).get("data", [])]:
            x["username"] = x.get("username") or (x.get("from") or {}).get("username") or ""
        for c in cs:
            if ts(c["timestamp"]) < fresh:
                continue
            reps = (c.get("replies") or {}).get("data", [])
            ours = [r for r in reps if r.get("username") == OWN]
            if (c["username"] and c["username"] != OWN and c.get("text") and not KEYWORD.search(c["text"]) and not ours
                    and c["id"] not in done and per_user.get((m["id"], c["username"]), 0) < 2):
                pending.append({"id": c["id"], "media": m["id"], "user": c["username"], "text": c["text"][:400],
                                "caption": (m.get("caption") or "")[:500], "thread": ""})
            # one follow-up: someone answered our reply in this thread
            if ours:
                last_ours = max(ts(r["timestamp"]) for r in ours)
                for r in reps:
                    if (r["username"] not in (OWN, "") and ts(r["timestamp"]) > last_ours and r["id"] not in done
                            and r.get("text") and per_user.get((m["id"], r["username"]), 0) < 2):
                        pending.append({"id": r["id"], "reply_to": c["id"], "media": m["id"], "user": r["username"],
                                        "text": r["text"][:400], "caption": (m.get("caption") or "")[:500],
                                        "thread": f'they said: "{c["text"][:200]}" / I replied: "{ours[-1].get("text", "")[:120]}"'})
    pending = pending[:MAX_PER_RUN]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    json.dump(pending, open(out_path, "w"), indent=1, ensure_ascii=False)
    print(f"{len(pending)} comments need a reply")
    return len(pending)


def prompt(pending_path, out_path):
    pending = json.load(open(pending_path))
    voice = (ROOT / "tools/instagram/reply-voice.md").read_text()
    items = [{"n": i, "user": p["user"], "comment": p["text"], "thread": p["thread"], "reel_caption": p["caption"][:300]}
             for i, p in enumerate(pending)]
    Path(out_path).write_text(
        voice + "\n\nWrite one reply per comment below. Answer with ONLY a JSON array, one object per comment, in order:\n"
        '[{"n": 0, "reply": "<text>"}, {"n": 1, "skip": true, "why": "<few words>"}, ...]\n\nComments:\n'
        + json.dumps(items, ensure_ascii=False, indent=1))


def tg(text):
    t, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not t or not chat:
        return
    data = json.dumps({"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{t}/sendMessage", data=data,
                                                      headers={"content-type": "application/json"}), timeout=20)
    except Exception as e:  # noqa: BLE001
        print("telegram:", e)


def clean(reply):
    reply = re.sub(r"\s*[—–]\s*", ", ", str(reply or "")).replace("#", "").strip().strip('"')
    if not reply or len(reply.split()) > 15 or GUARD.search(reply):
        return None
    return reply


def post(pending_path, replies_path):
    pending = json.load(open(pending_path))
    raw = Path(replies_path).read_text()
    m = re.search(r"\[[\s\S]*\]", raw)
    try:
        answers = {a.get("n"): a for a in json.loads(m.group(0))} if m else None
    except ValueError:
        answers = None
    if not answers:   # Claude failed or hit the subscription limit: post and record nothing, a later run retries
        print("no replies written this run; nothing posted, nothing recorded")
        return
    sent, lines = 0, []
    for i, p in enumerate(pending):
        a = answers.get(i, {"skip": True, "why": "no answer"})
        rec = {"comment": p["id"], "media": p["media"], "user": p["user"], "text": p["text"][:300], "at": now().isoformat(timespec="seconds")}
        reply = None if a.get("skip") else clean(a.get("reply"))
        if reply:
            try:
                ig(f"{p.get('reply_to', p['id'])}/replies", method="POST", message=reply)
                rec["reply"] = reply
                sent += 1
                lines.append(f"@{p['user']}: {p['text'][:120]}\n↳ {reply}")
            except Exception as e:  # noqa: BLE001
                rec["error"] = str(e)[:200]
        else:
            rec["skipped"] = a.get("why", "guard")
        state.put("ig_reply", p["id"], rec)
    print(f"sent {sent} of {len(pending)}")
    if lines:
        tg(f"💬 Replied to {sent} comment{'s' if sent != 1 else ''}:\n\n" + "\n\n".join(lines))


def again(started):
    """Webhook comments that arrived while this run worked (D1 reply_dispatch pending) get one more run, same caps."""
    import subprocess
    d1 = state.backend("d1")
    day = now().strftime("%Y-%m-%d")
    d = d1.get("reply_dispatch", day) or {}
    if (d.get("pending") or 0) / 1000 <= float(started) or d.get("n", 0) >= 48:
        print("nothing came in meanwhile")
        return
    subprocess.run(["gh", "workflow", "run", "comment-replies.yml", "-f", "source=webhook"], check=True)
    d1.put("reply_dispatch", day, {**d, "n": d.get("n", 0) + 1, "last": int(now().timestamp() * 1000), "pending": 0})
    print("started one more run for comments that came in meanwhile")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "collect":
        n = collect(sys.argv[2])
        if os.environ.get("GITHUB_OUTPUT"):
            open(os.environ["GITHUB_OUTPUT"], "a").write(f"n={n}\n")
    elif cmd == "prompt":
        prompt(sys.argv[2], sys.argv[3])
    elif cmd == "post":
        post(sys.argv[2], sys.argv[3])
    elif cmd == "again":
        again(sys.argv[2])
    else:
        sys.exit(__doc__)
