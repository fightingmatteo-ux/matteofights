"""Free stock b-roll from Mixkit (Mixkit License: free for social, no attribution).

  python -P mixkit.py search boxing "running rain" ...   # lists: orientation id title
  python -P mixkit.py get <outdir> <id> [<id> ...]        # downloads 1080p (720p fallback) as mk<id>.mp4

Prefer "vert" results for 9:16 reels.
"""
import html
import os
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def search(terms):
    seen = set()
    for term in terms:
        slug = re.sub(r"\s+", "-", term.strip().lower())
        try:
            s = fetch(f"https://mixkit.co/free-stock-video/{slug}/").decode("utf-8", "ignore")
        except Exception as e:  # noqa: BLE001
            print(f"# {term}: {e}")
            continue
        print(f"# {term}")
        for m in re.finditer(r'item-id-value="(\d+)"', s):
            i = m.group(1)
            if i in seen:
                continue
            seen.add(i)
            before = s[max(0, m.start() - 700):m.start()]
            o = "vert" if "--vertical" in before else "hori"
            t = re.search(r'overlay-video-title">\s*(.*?)\s*</span>', s[m.end():m.end() + 3000], re.S)
            print(f"{o} {i} {html.unescape(t.group(1)) if t else '?'}")


def get(outdir, ids):
    os.makedirs(outdir, exist_ok=True)
    for i in ids:
        dst = os.path.join(outdir, f"mk{i}.mp4")
        if os.path.exists(dst):
            print("have", dst)
            continue
        for q in ("1080", "720"):
            try:
                data = fetch(f"https://assets.mixkit.co/videos/{i}/{i}-{q}.mp4")
                open(dst, "wb").write(data)
                print(f"got {dst} ({q}p, {len(data) // 1024} KB)")
                break
            except Exception:  # noqa: BLE001
                continue
        else:
            print("FAILED", i)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "search":
        search(sys.argv[2:])
    elif sys.argv[1] == "get":
        get(sys.argv[2], sys.argv[3:])
