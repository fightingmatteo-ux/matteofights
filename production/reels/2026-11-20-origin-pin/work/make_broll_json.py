"""Place the cutaways for A, B, C: python3 -I work/make_broll_json.py  (writes work/broll_<V>.json + work/clips.txt)

Body clips are pinned to SOURCE seconds of the raw take (the words they show), so every variant gets the same
cutaway on the same words. Cold-open clips (B, C) are pinned to hook words. precut.sh cuts the files from clips.txt.
Rule (taste.md): b-roll shows exactly what the words say at that moment. "Now" footage must look sharp; the old pad
clips (beginner) only appear on the beginner years. No kick clip near "I can't jump" (a viewer would call it out).
"""
import json

T = json.load(open("work/takes.json"))
# name: (kind, source file, clip start, clip dur, crop centre x)   files: precut.sh (Drive ids) + media release
CLIPS = {
    "superpro": ("photo", "superpro.jpg", 0, 2.6, ""),        # BJJ at 10, Super Pro Samui (Matteo circled, left kid)
    "striking": ("clip", "super8.mp4", 1.0, 2.1, 0.5),       # first striking years: Super8 pads (graded good at 1.0)
    "booked":   ("clip", "first-fight-2.mp4", 0.5, 2.4, 0.5),  # the stadium, fighters in the ring
    "hadnt":    ("clip", "broll-pads-chaiya.mp4", 4.4, 2.5, 0.42),  # training as a beginner, punches on pads
    "hospital": ("photo", "hospital.jpg", 0, 2.0, ""),        # appendicitis: Matteo in the gown, duck face
    "stadium":  ("clip", "first-fight-2.mp4", 22.9, 2.05, 0.5),  # Matteo's pick: his kicks at 24 s (black shorts)
    "trained":  ("clip", "super8.mp4", 60.6, 2.0, 0.5),       # "so I trained three more months": Super8 kick/knee combos (graded good)
    "swiss":    ("clip", "impact-mma.mov", 15.2, 4.0, 0.5),   # "five countries: Thailand ... Brazil": ONE held clip of his sharp Impact MMA kicks (Matteo 11-20: the 0.6 s flashes looked buggy)
    "kickend":  ("clip", "kicking.mov", 19.6, 2.3, 0.5),      # "but I can do this": the high kick on the bag (Matteo: sharp kicks)
    "headkick": ("clip", "headkick.mov", 4.6, 2.2, 0.6, 1.45),  # then his head kick (Matteo's pick), zoomed past the dark bars
    "hand":     ("photo", "hand.jpg", 0, 1.6, ""),            # boxer's fracture: "Just a bit swollen"
    "xray":     ("photo", "xray.jpg", 0, 4.4, ""),            # broken fibula, torn ACL ... "I can't jump" (covers 2 look-aways)
    "coldB":    ("clip", "broll-pads-chaiya.mp4", 19.4, 0, 0.4),  # B frame 0: the beginner kick (dur set below)
    "coldC":    ("clip", "first-fight-2.mp4", 6.0, 0, 0.5),   # C frame 0: the stadium, "the day before my first fight"
    "coldC2":   ("photo", "hospital_hook.jpg", 0, 0, ""),     # C: "...I ended up in the hospital" (face lower: clear of the board)
}
# body: name -> source second it starts on. Words it covers in the comment.
BODY = {
    "superpro": 13.50,   # "Brazilian jiu-jitsu at 10. Three years on the mat"
    "striking": 19.75,   # "So I switched to striking"
    "booked":   125.35,  # "Then I booked my first Muay Thai fight"
    "hadnt":    133.95,  # "So if I hadn't trained that day, I couldn't sleep"
    "hospital": 157.30,  # "I got appendicitis" (A, B; C has it in the hook)
    "stadium":  159.35,  # "pushed back three months, at a different stadium"
    "trained":  161.45,  # "So I trained three more months"
    "swiss":    236.25,  # "Thailand, Switzerland, Italy, Morocco, Brazil" (starts early: he looks away before the word)
    "kickend":  306.90,  # the 4.5 s after "but I can do this" (his room sound under the bed)
    "headkick": 309.20,
    "hand":     276.85,  # "Boxer's fracture"
    "xray":     283.20,  # "Broken fibula and fully torn ACL. I can't jump." (spans the p7/p8 join)
}


def src_to_out(edl, src):
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


durs = {}
for V in "ABC":
    edl = json.load(open(f"work/edl_{V}.json"))
    out = {}
    if V == "B":   # "School came easy to me" over his beginner kick; his face on "Fighting was the first thing that didn't"
        d = round(word(edl, "FIGHTING") - 0.06, 3)
        out["coldB"] = {"start": 0.0, "dur": d}
        durs["coldB"] = max(durs.get("coldB", 0), d)
    if V == "C":   # "The day before my first fight" over the stadium, "I ended up in the hospital" over the gown photo
        cut = round(word(edl, "ENDED") - 0.35, 3)
        end = edl["segments"][0]["end"]
        out["coldC"] = {"start": 0.0, "dur": cut}
        out["coldC2"] = {"start": cut, "dur": round(end - cut, 3)}
        durs["coldC"], durs["coldC2"] = cut, round(end - cut, 3)
    for name, src in BODY.items():
        if V == "C" and name == "hospital":
            continue
        t = src_to_out(edl, src)
        assert t is not None, (V, name)
        out[name] = {"start": round(t, 3), "dur": CLIPS[name][3]}
    spans = sorted((c["start"], c["start"] + c["dur"], n) for n, c in out.items())
    for (a0, a1, an), (b0, b1, bn) in zip(spans, spans[1:]):
        assert a1 <= b0 + 1e-6, f"{V}: {an} overlaps {bn}"
    json.dump(out, open(f"work/broll_{V}.json", "w"), indent=1)
    print(V, " ".join(f"{n}@{c['start']:.2f}+{c['dur']}" for n, c in sorted(out.items(), key=lambda x: x[1]["start"])))

with open("work/clips.txt", "w") as f:
    f.write("# name kind source start dur cropx   (written by make_broll_json.py)\n")
    for n, (kind, src, a, d, x, *z) in CLIPS.items():
        d = durs.get(n, d) + 0.1  # a hair longer than placed: no black frame at the out-point
        f.write(f"{n} {kind} {src} {a} {d:.2f} {x or 0.5} {z[0] if z else 1}\n")
