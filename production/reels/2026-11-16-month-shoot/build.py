"""Build the take-sheet prompter and the film sheet from scripts.json.

    python3 -P production/reels/2026-11-16-month-shoot/build.py

Writes prompter.html (next to this file; published as the reading page) and
production/reels/FILM-2026-11-16-month-shoot.md.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "scripts.json").read_text(encoding="utf-8"))

for r in data["reels"]:
    kinds = [t["k"] for t in r["takes"]]
    assert kinds == ["A", "B", "C", "D", "E", "BODY", "END"], (r["id"], kinds)
    for t in r["takes"]:
        assert "—" not in t["text"], f"em dash in {r['id']} {t['k']}"

page = {"reels": data["reels"]}
blob = json.dumps(page, ensure_ascii=False).replace("</", "<\\/")
tpl = (HERE / "prompter.tpl.html").read_text(encoding="utf-8")
(HERE / "prompter.html").write_text(tpl.replace("/*DATA*/", blob), encoding="utf-8")

out = [
    f"# Filming sheet: the month shoot (Pocket 3, {data['updated']})",
    "",
    "Built from `2026-11-16-month-shoot/scripts.json` (edit there, then run `build.py`). Matteo asked for reading",
    "scripts this time, read from the take-sheet page. Per reel: say the label, wait 2 s, then the take. Hooks A to E",
    "each as their own take, then BODY once, then END once (same spot, shirt, distance).",
    "",
    "Series (Matteo 2026-11-16): Saenchai is redone as Episode 1. More styles than Muay Thai: boxers, a wrestler, a",
    "kickboxer. He introduces himself in every episode, and the CTA is one comment: PLAN plus the fighter they want",
    "next. After Episode 1 the comments decide the order, so only Episode 1 says its number out loud.",
    "",
]
for group, name in (("breakdown", "Fighter breakdown series"), ("talk", "Talking heads and rants")):
    out += [f"## {name}", ""]
    for r in data["reels"]:
        if r["group"] != group:
            continue
        out += [f"### {r['slate']}: {r['title']} ({r['tag']})", "", f"Why: {r['why']}"]
        if r["note"]:
            out += [f"Before filming: {r['note']}"]
        out += [""]
        for t in r["takes"]:
            if t["k"] in ("BODY", "END"):
                out += [f"**{t['k']}**", ""] + [f"> {p}" if p else ">" for p in t["text"].split("\n")] + [""]
            else:
                out += [f"- {t['k']} ({t['type']}): {t['text']}"]
        out += [""]
(HERE.parent / "FILM-2026-11-16-month-shoot.md").write_text("\n".join(out), encoding="utf-8")
print("built", len(data["reels"]), "reels,", sum(len(r["takes"]) for r in data["reels"]), "takes")
