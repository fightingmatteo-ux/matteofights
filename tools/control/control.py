"""Control center engine: one place where Matteo's decisions land, from the dashboard or from Telegram.

    python -P tools/control/control.py act '<json>' --via dashboard   # approve_week / answer / idea / telegram update
    python -P tools/control/control.py notify                         # send Matteo what's new on Telegram

Files (all in production/control/, committed by the "Control" workflow):
  questions.json  cards Claude asks Matteo: {id, question, options[], status open|answered, answer, answered_at, via}
  ideas.json      Matteo's free-text ideas: {id, text, at, via, status new|seen, reply}
  log.json        activity feed: what happened, newest last (Claude, factory, posting, Matteo)
  metrics.json    per-reel results + account baseline, written by Claude's daily check (Buzzfy)
  notes.json      messages Claude wants delivered to Telegram (winners, replies): {id, text}
  state.json      which weeks/questions/notes were already sent
Approving a week = Matteo's explicit yes for exactly the reels in that batch (recorded with time + channel).
Telegram only listens to TELEGRAM_CHAT_ID; the dashboard only accepts Matteo's Cloudflare Access login.
"""
import argparse, datetime as dt, io, json, os, subprocess, sys, urllib.parse, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTL = ROOT / "production" / "control"
QUEUE = ROOT / "production" / "schedule" / "queue.json"
TG = "https://api.telegram.org/bot{token}/{method}"
NY = None


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(name, default):
    p = CTL / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(name, data):
    CTL.mkdir(parents=True, exist_ok=True)
    (CTL / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def log(text, who="system"):
    entries = load("log.json", [])
    entries.append({"at": now(), "who": who, "text": text})
    save("log.json", entries[-300:])


def ny(iso):
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
    return t.strftime("%a %d %b %-I:%M%p").replace("AM", "am").replace("PM", "pm")


# ---------------------------------------------------------------- actions (shared by web + Telegram)
def pending_week():
    """Rendered listicles waiting for a yes, oldest first."""
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    return [i for i in q["items"] if i["id"].startswith("lst-") and i["status"] == "queued" and not i.get("approved")]


def approve(ids, via):
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    stamp = now()
    done = []
    for i in q["items"]:
        if i["id"] in ids and i["status"] == "queued" and not i.get("approved"):
            i.update(approved=True, approved_note=f"Matteo: approved the week via {via} ({stamp})")
            done.append(i["id"])
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if done:
        log(f"Approved {len(done)} reels via {via}", "Matteo")
    return done


def answer(qid, choice, via):
    qs = load("questions.json", [])
    for x in qs:
        if x["id"] == qid and x["status"] == "open":
            x.update(status="answered", answer=choice, answered_at=now(), via=via)
            save("questions.json", qs)
            log(f"Answered \"{x['question']}\": {choice}", "Matteo")
            return x
    return None


def idea(text, via):
    ideas = load("ideas.json", [])
    item = {"id": uuid.uuid4().hex[:8], "text": text.strip()[:2000], "at": now(), "via": via, "status": "new", "reply": ""}
    ideas.append(item)
    save("ideas.json", ideas)
    log(f"New idea: {item['text'][:80]}", "Matteo")
    return item


def act(payload, via):
    a = payload.get("action")
    if a == "approve_week":
        ids = payload.get("ids") or [i["id"] for i in pending_week()]
        return {"approved": approve(set(ids), via)}
    if a == "answer":
        return {"answered": bool(answer(payload["id"], str(payload["choice"])[:500], via))}
    if a == "idea":
        return {"idea": idea(str(payload["text"]), via)}
    raise SystemExit(f"unknown action {a!r}")


# ---------------------------------------------------------------- Telegram
def tg(method, data=None, files=None):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = TG.format(token=token, method=method)
    if files:
        boundary = uuid.uuid4().hex
        body = io.BytesIO()
        for k, v in (data or {}).items():
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        for k, (name, blob, ctype) in files.items():
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\n"
                       f"Content-Type: {ctype}\r\n\r\n".encode() + blob + b"\r\n")
        body.write(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(url, body.getvalue(), {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        req = urllib.request.Request(url, json.dumps(data or {}).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if not out.get("ok"):
        raise RuntimeError(f"telegram {method}: {out}")
    return out["result"]


def buttons(rows):
    return json.dumps({"inline_keyboard": [[{"text": t, "callback_data": d[:64]} for t, d in row] for row in rows]})


def week_sheet(items):
    """Cover contact sheet for a batch (PIL), as JPEG bytes."""
    from PIL import Image
    ims = []
    for i in items:
        p = ROOT / Path(i["caption_file"]).parent / "cover.jpg"
        if p.exists():
            ims.append(Image.open(p).convert("RGB").resize((216, 384)))
    if not ims:
        return None
    cols = min(7, len(ims))
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (216 * cols, 384 * rows), "black")
    for k, im in enumerate(ims):
        sheet.paste(im, (216 * (k % cols), 384 * (k // cols)))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def send_new(chat, state):
    """Announce what Matteo hasn't seen yet: a new week to approve, open questions, replies to ideas."""
    week = pending_week()
    ids = sorted(i["id"] for i in week)
    key = ",".join(ids)
    if ids and key != state.get("announced_week"):
        lines = [f"• {ny(i['not_before'])} NY: {i.get('hook', i['id'])}" for i in sorted(week, key=lambda x: x["not_before"])]
        text = f"🥊 Next week is ready: {len(ids)} trial reels\n\n" + "\n".join(lines)
        text += "\n\nApproving = your yes for exactly these. They post automatically at the New York times above."
        sheet = week_sheet(sorted(week, key=lambda x: x["not_before"]))
        if sheet:
            tg("sendPhoto", {"chat_id": chat, "caption": "Covers, in posting order"}, {"photo": ("week.jpg", sheet, "image/jpeg")})
        batch = uuid.uuid4().hex[:8]
        state.setdefault("batches", {})[batch] = ids
        tg("sendMessage", {"chat_id": chat, "text": text[:4000],
                           "reply_markup": buttons([[("✅ Approve the week", f"aw:{batch}")]])})
        state["announced_week"] = key
        log(f"Sent the week ({len(ids)} reels) to Telegram")
    for x in load("questions.json", []):
        if x["status"] == "open" and x["id"] not in state.setdefault("sent_questions", []):
            opts = x.get("options") or []
            rows = [[(o[:40], f"q:{x['id']}:{k}")] for k, o in enumerate(opts)]
            tg("sendMessage", {"chat_id": chat, "text": f"❓ {x['question']}" + (f"\n\n{x['context']}" if x.get("context") else ""),
                               **({"reply_markup": buttons(rows)} if rows else {})})
            state["sent_questions"].append(x["id"])
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    for i in q["items"]:
        if i["status"] == "failed" and i["id"] not in state.setdefault("sent_failed", []):
            tg("sendMessage", {"chat_id": chat, "text": f"⚠️ A reel failed to post: {i.get('hook', i['id'])}\n"
                                                         f"{(i.get('error') or '')[:300]}\nClaude looks at it on the next daily check."})
            state["sent_failed"].append(i["id"])
    for n in load("notes.json", []):
        if n["id"] not in state.setdefault("sent_notes", []):
            tg("sendMessage", {"chat_id": chat, "text": n["text"][:4000]})
            state["sent_notes"].append(n["id"])


def handle_update(u, chat, state):
    """One Telegram update, forwarded by the Cloudflare webhook (control-site/functions/api/telegram.js)."""
    msg = u.get("message") or (u.get("callback_query") or {}).get("message") or {}
    frm = str((msg.get("chat") or {}).get("id", ""))
    if frm != chat:
        print(f"ignored update from chat {frm}")
        return
    if "callback_query" in u:
        data = u["callback_query"].get("data", "")
        if data.startswith("aw:"):
            ids = state.get("batches", {}).get(data[3:], [])
            done = approve(set(ids), "Telegram")
            reply = f"✅ Approved {len(done)} reels. They post automatically at the New York times." if done else "Already approved."
        elif data.startswith("q:"):
            _, qid, k = data.split(":", 2)
            qx = next((x for x in load("questions.json", []) if x["id"] == qid), None)
            if qx and qx["status"] == "open":
                answer(qid, qx["options"][int(k)], "Telegram")
                reply = f"Got it: {qx['options'][int(k)]}"
            else:
                reply = "Already answered."
        else:
            return
        outbox(state, reply, clear=msg.get("message_id"))
    elif (u.get("message") or {}).get("text"):
        text = u["message"]["text"]
        if text.startswith("/start"):
            outbox(state, "Connected. I'll send weeks to approve, winners and questions here. "
                          "Anything you type becomes an idea for Claude.")
        else:
            idea(text, "Telegram")
            outbox(state, "💡 Saved. Claude picks it up on the next daily check.")


def outbox(state, text, clear=None):
    """Replies are queued with the decision and sent only after it is pushed (a retried run never double-sends)."""
    state.setdefault("outbox", []).append({"text": text, "clear": clear})


def notify():
    """Send Matteo anything new (called after posting runs, factory runs and every action)."""
    if not (os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")):
        print("Telegram not configured: nothing sent")
        return
    state = load("state.json", {})
    chat = os.environ["TELEGRAM_CHAT_ID"]
    for m in state.pop("outbox", []):
        if m.get("clear"):
            try:
                tg("editMessageReplyMarkup", {"chat_id": chat, "message_id": m["clear"],
                                              "reply_markup": json.dumps({"inline_keyboard": []})})
            except Exception as e:
                print(f"could not clear buttons: {e}")
        tg("sendMessage", {"chat_id": chat, "text": m["text"]})
    send_new(chat, state)
    save("state.json", state)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["act", "notify"])
    p.add_argument("payload", nargs="?", default="{}")
    p.add_argument("--via", default="dashboard")
    p.add_argument("--no-notify", action="store_true", help="apply only; the workflow notifies after its push")
    a = p.parse_args()
    if a.cmd == "act":
        payload = json.loads(a.payload)
        if payload.get("action") == "telegram":
            chat = os.environ.get("TELEGRAM_CHAT_ID", "")
            state = load("state.json", {})
            handle_update(payload["update"], chat, state)
            save("state.json", state)
        else:
            print(json.dumps(act(payload, a.via)))
        if a.no_notify:
            return
    notify()


if __name__ == "__main__":
    main()
