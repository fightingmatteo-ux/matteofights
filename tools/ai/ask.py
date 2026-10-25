"""Ask Gemini (free API key) for bulk text work so Claude's weekly limit goes to the real jobs.

Use for: batches of rough hook angles, summaries of long logs or transcripts, first-draft captions. Not for
final copy, anything that touches the queue or posting, or agent work (Claude does those).

  python -P tools/ai/ask.py "prompt"                  prompt as an argument
  echo "text" | python -P tools/ai/ask.py --stdin "summarise this"   stdin is appended to the prompt
  python -P tools/ai/ask.py --model gemini-2.5-flash-lite "..."

Key: env GEMINI_API_KEY (GitHub secret), locally read from secrets/gemini.env (git-ignored). No billing on the
key: past the free daily limit calls fail with 429 instead of charging. Exit codes: 0 ok, 2 no key,
3 rate limited / failed (the caller should do the job itself).
"""
import argparse, json, os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"   # separate daily quota, tried when the first model is rate limited


def _key():
    k = os.environ.get("GEMINI_API_KEY")
    f = ROOT / "secrets" / "gemini.env"
    if not k and f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"')
    return k


def ask(prompt, model=DEFAULT_MODEL):
    key = _key()
    if not key:
        print("ask.py: GEMINI_API_KEY not set (secrets/gemini.env or env); do the job yourself", file=sys.stderr)
        sys.exit(2)
    for m in (model, FALLBACK_MODEL) if model != FALLBACK_MODEL else (model,):
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r)
            return "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                continue
            raise RuntimeError(f"Gemini {e.code}: {e.read().decode()[:300]}") from e
        except (KeyError, IndexError) as e:
            raise RuntimeError("Gemini returned no text (blocked or empty)") from e
    raise RuntimeError("Gemini rate limited on every model (free daily limit); do the job yourself")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--stdin", action="store_true", help="append stdin to the prompt")
    a = ap.parse_args()
    prompt = a.prompt + ("\n\n" + sys.stdin.read() if a.stdin else "")
    try:
        print(ask(prompt, a.model))
    except RuntimeError as e:
        print(f"ask.py: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
