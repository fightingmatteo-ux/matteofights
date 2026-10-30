"""Copy every key on this laptop into the clipboard as one block, ready to paste into the claude.ai/code cloud
environment (environment menu in the session title bar > Edit > Environment variables). Once that is pasted, every
cloud session in that environment has all the keys, from any device: phone, browser, someone else's laptop.

    python -P tools/cloud/env_block.py           # to the clipboard (nothing printed)
    python -P tools/cloud/env_block.py --print   # print it instead
    python -P tools/cloud/env_block.py --names   # only the key names, to check what is there

Reads secrets/*.env and secrets.local.env (whichever exist). Values that span lines (cookies, rclone.conf) are left
out; a JSON value, or a path to a .json file, is squeezed onto one line. Run it again after any token refresh and
paste again. Same script in matteofights and gypsy-amazon-OS: each business gets its own cloud environment, because
both use the same names (CLOUDFLARE_API_TOKEN, R2_*, MODAL_*) for different accounts.
"""
import json
import pathlib
import platform
import subprocess
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents if (p / ".git").exists())

# other names some scripts read for the same key (set only when missing)
ALIASES = {"CLOUDFLARE_API_TOKEN": "CLOUDFLARE_BUILD_TOKEN", "CLOUDFLARE_D1_TOKEN": "CLOUDFLARE_BUILD_TOKEN",
           "IG_ACCESS_TOKEN": "IG_GRAPH_ACCESS_TOKEN"}


def parse(path):
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.removeprefix("export ").strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        out[k] = v
    return out


def one_line(v):
    p = pathlib.Path(v) if len(v) < 300 and v.endswith(".json") else None
    if p and not p.is_absolute():
        p = ROOT / p
    if p and p.is_file():
        v = p.read_text(encoding="utf-8-sig")
    if v[:1] in "{[":
        try:
            return json.dumps(json.loads(v), separators=(",", ":"))
        except ValueError:
            pass
    return None if "\n" in v else v


def main():
    files = sorted((ROOT / "secrets").glob("*.env")) + [ROOT / "secrets.local.env"]
    files = [f for f in files if f.is_file()]
    if not files:
        sys.exit(f"No secrets/*.env or secrets.local.env in {ROOT}. Run this on the laptop that has the keys.")
    env, skipped = {}, []
    for f in files:
        env.update(parse(f))
    for name, src in ALIASES.items():
        if not env.get(name) and env.get(src):
            env[name] = env[src]
    cloud = ROOT / "tools/cloud/cloud.json"
    if not env.get("CLOUDFLARE_ACCOUNT_ID") and cloud.is_file():
        env["CLOUDFLARE_ACCOUNT_ID"] = json.loads(cloud.read_text(encoding="utf-8")).get("account_id", "")
    lines = []
    for k, v in env.items():
        v = one_line(v) if v else None
        (lines.append(f"{k}={v}") if v else skipped.append(k))
    block = "\n".join(lines) + "\n"

    if "--names" in sys.argv:
        print("\n".join(l.split("=", 1)[0] for l in lines))
    elif "--print" in sys.argv:
        print(block, end="")
    else:
        cmd = {"Windows": ["clip"], "Darwin": ["pbcopy"]}.get(platform.system(), ["xclip", "-selection", "clipboard"])
        subprocess.run(cmd, input=block.encode("utf-8"), check=True)
    print(f"{len(lines)} keys from {', '.join(f.name for f in files)}"
          + ("" if "--print" in sys.argv or "--names" in sys.argv else " copied to the clipboard."), file=sys.stderr)
    if skipped:
        print(f"Left out (empty or multi-line): {', '.join(skipped)}", file=sys.stderr)
    print("Paste into: claude.ai/code > environment menu (session title bar) > Edit > Environment variables. "
          "New sessions get them.", file=sys.stderr)


if __name__ == "__main__":
    main()
