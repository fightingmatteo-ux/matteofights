"""Drop caption tokens that are Whisper spill-over at a cut (the word is mostly outside the range): python3 work/postfix_edl.py A B C D E"""
import json, sys
for v in sys.argv[1:]:
    p = f"work/edl_{v}.json"; d = json.load(open(p))
    bounds = list(d["joins"]) + [d["duration"]]
    keep, drop = [], []
    for w in d["words"]:
        if any(abs(w["e"] - B) < 0.006 and B - w["s"] < 0.35 for B in bounds):
            drop.append(w["w"]); continue
        keep.append(w)
    d["words"] = keep; json.dump(d, open(p, "w"), indent=1)
    print(v, "dropped", drop)
