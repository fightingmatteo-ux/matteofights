"""Hand bulk text work to free models so Claude's weekly limit goes to the real jobs.

Use for: batches of rough hook angles, summaries of long logs or transcripts, first-draft captions. Not for final
copy, anything that touches the queue or posting, or agent work (Claude does those). Never send tokens, secrets or
private DMs: free tiers may keep prompts.

  python -P tools/ai/ask.py [--task bulk|draft|summarize] "prompt"
  echo "text" | python -P tools/ai/ask.py --stdin --task summarize "summarise this"
  python -P tools/ai/ask.py --status        today's calls per provider, which have a key

Providers and routing: tools/ai/providers.json (add a tool = add an entry). Keys: env vars (GitHub secrets),
locally secrets/ai.env or secrets/gemini.env (git-ignored), KEY=value lines. Keep billing OFF on every key: past
the free limit a call fails instead of charging. Our own daily caps stop well before that. Counters live in
.ai-usage.json (git-ignored, per machine). Exit codes: 0 ok, 2 no provider available, 3 all failed or capped
(the caller does the job itself).
"""
import argparse, datetime, json, os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONF = json.loads((Path(__file__).parent / "providers.json").read_text(encoding="utf-8"))
USAGE = ROOT / ".ai-usage.json"


def _env(name):
    if not name:
        return "local"
    if os.environ.get(name):
        return os.environ[name]
    for f in ("ai.env", "gemini.env"):
        p = ROOT / "secrets" / f
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"')
    return None


def _today():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _used():
    try:
        d = json.loads(USAGE.read_text())
        return d["counts"] if d.get("day") == _today() else {}
    except Exception:
        return {}


def _count(name):
    c = _used()
    c[name] = c.get(name, 0) + 1
    USAGE.write_text(json.dumps({"day": _today(), "counts": c}))


def _call(p, key, prompt):
    if p["kind"] == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent"
        body, hdr = {"contents": [{"parts": [{"text": prompt}]}]}, {"x-goog-api-key": key}
    else:
        url = p["base_url"].rstrip("/") + "/chat/completions"
        body, hdr = {"model": p["model"], "messages": [{"role": "user", "content": prompt}]}, {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **hdr})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    if p["kind"] == "gemini":
        return "".join(x.get("text", "") for x in d["candidates"][0]["content"]["parts"])
    return d["choices"][0]["message"]["content"]


def ask(prompt, task="bulk"):
    by_name = {p["name"]: p for p in CONF["providers"]}
    used, tried = _used(), []
    for name in CONF["tasks"][task]:
        p = by_name[name]
        key = _env(p["key_env"])
        if not key:
            continue
        if used.get(name, 0) >= p["daily_cap"]:
            tried.append(f"{name}: daily cap")
            continue
        try:
            _count(name)  # count before the call: failed calls spend quota too
            return name, _call(p, key, prompt)
        except urllib.error.HTTPError as e:
            tried.append(f"{name}: HTTP {e.code}")
        except Exception as e:
            tried.append(f"{name}: {type(e).__name__}")
    if not tried:
        raise SystemExit(_die("no provider has a key (secrets/ai.env or env); do the job yourself", 2))
    raise SystemExit(_die("all failed or capped (" + "; ".join(tried) + "); do the job yourself", 3))


def _die(msg, code):
    print("ask.py: " + msg, file=sys.stderr)
    return code


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--task", default="bulk", choices=list(CONF["tasks"]))
    ap.add_argument("--stdin", action="store_true", help="append stdin to the prompt")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        u = _used()
        for p in CONF["providers"]:
            print(f"{p['name']:16} {'key ok ' if _env(p['key_env']) else 'no key '} {u.get(p['name'], 0)}/{p['daily_cap']} today")
        return
    if not a.prompt:
        ap.error("prompt required")
    name, text = ask(a.prompt + ("\n\n" + sys.stdin.read() if a.stdin else ""), a.task)
    print(f"[{name}]", file=sys.stderr)
    print(text)


if __name__ == "__main__":
    main()
