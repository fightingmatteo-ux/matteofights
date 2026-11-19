"""Place the cutaways for F, G, H: python3 -I work/make_broll_json.py  (writes work/broll_<V>.json)

Body clips are pinned to SOURCE seconds of the raw take (the words they show), so every variant gets the same
cutaway on the same words. Cold-open clips (G, H) are pinned to hook words. Clip files: work/precut.sh.
"""
import json

T = json.load(open("work/takes.json"))
# body: name -> (source second it starts on, duration). Words it covers in the comment.
BODY = {
    "side1": (102.10, 3.0),   # "back. When you punch, he steps to the side"
    "side2": (105.10, 3.6),   # "so after his combo, he's standing where your punches won't catch him"
    "inout": (110.25, 6.9),   # "his feet never stop, tiny steps in and out all the time, you can't plant your feet to punch
                              #  someone who's never in the same spot" (one shot, held: taste "fewer clips, held longer")
    "pivot": (163.50, 3.3),   # "He lands, then pivots around his front foot. Now he's at your side"
}


def src_to_out(edl, variant, src):
    for seg in edl["segments"]:
        rng = T["takes"][seg["name"]]
        rngs = rng if isinstance(rng[0], list) else [rng]
        t = seg["start"]
        for a, b in rngs:
            if a <= src < b:
                return t + (src - a)
            t += b - a
    return None


def word(edl, w, k=1):
    return [x for x in edl["words"] if x["w"] == w][k - 1]["s"]


for V in "FGH":
    edl = json.load(open(f"work/edl_{V}.json"))
    out = {}
    hook_end = edl["segments"][0]["end"]
    if V == "G":   # "Most people drill punches." over Matteo's own pad work, "Lomachenko drilled his feet." over Loma's feet
        cut = word(edl, "LOMACHENKO")
        out["pads"] = {"start": 0.0, "dur": round(cut, 3)}
        out["feet"] = {"start": round(cut, 3), "dur": round(hook_end - cut, 3)}
    if V == "H":   # "Why do good boxers look completely lost" over an opponent turning to find him; Matteo shows on "against Lomachenko?"
        out["lost"] = {"start": 0.0, "dur": round(min(3.6, word(edl, "AGAINST") + 0.05), 3)}
    for name, (src, dur) in BODY.items():
        t = src_to_out(edl, V, src)
        assert t is not None, (V, name)
        out[name] = {"start": round(t, 3), "dur": dur}
    spans = sorted((c["start"], c["start"] + c["dur"], n) for n, c in out.items())
    for (a0, a1, an), (b0, b1, bn) in zip(spans, spans[1:]):
        assert a1 <= b0 + 1e-6, f"{V}: {an} overlaps {bn}"
    json.dump(out, open(f"work/broll_{V}.json", "w"), indent=1)
    print(V, {n: (c["start"], c["dur"]) for n, c in out.items()})
