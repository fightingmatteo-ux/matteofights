# Cuts the multi-take talking head into one A-roll per variant + remapped word timings.
#   python -P build_aroll.py A      -> assets/media/aroll_A.mp4 + edl_A.json
import json, subprocess, sys

SPEED = 1.06
RAW = "../../../media/worst-decision/raw"   # gitignored: raw footage lives in Drive input / the media release
SRC = f"{RAW}/talking_head_1011.mp4"

# Every usable take, trimmed with natural tails (room tone) so words breathe.
TAKES = {
    "hook":      (3.88, 7.45),    # Worst fighting decision of my life.
    "bjj":       (7.60, 11.30),   # I'd done three years of BJJ and I was good on the mat.
    "street":    (32.70, 36.50),  # Then I got into a fight on the street and I did what I always did.
    "takedown":  (36.66, 38.33),  # I went for the takedown.
    "except":    (45.50, 47.62),  # Except it wasn't a mat,
    "pavement":  (47.62, 48.80),  # it was pavement.
    "coldpave":  (46.00, 48.80),  # It wasn't a mat, it was pavement.   (cold-open hook)
    "knee":      (58.00, 61.10),  # We went down and both our weight landed on my left knee.
    "ligament":  (61.46, 64.30),  # Ligament damage. 6 months of rehab.
    "boxing":    (76.64, 78.90),  # I couldn't grapple so I started boxing.
    "muaythai":  (84.62, 87.55),  # Then Muay Thai. First fight at 16.
    "mats":      (96.00, 97.62),  # Mats forgive you.
    "doesnt":    (97.62, 99.15),  # Pavement doesn't.
    "coldmats":  (96.00, 99.15),  # Mats forgive you. Pavement doesn't.  (one-liner hook)
    "fibula":    (109.95, 114.70),# Since then I broke my fibula and now my ACL is completely torn.
    "loop":      (135.56, 137.28),# Because it all started with the…
}

# Only the hook changes; the body is shared. B/C drop the line their hook already used.
BODY_A = ["bjj", "street", "takedown", "except", "pavement", "knee", "ligament", "boxing", "muaythai", "mats", "doesnt", "fibula"]
VARIANTS = {
    "A": ["hook"] + BODY_A + ["loop"],
    "B": ["coldpave"] + [s for s in BODY_A if s not in ("except", "pavement")],
    "C": ["coldmats"] + [s for s in BODY_A if s not in ("mats", "doesnt")],
}

FIX = {"MAP": "MAT", "MADS": "MATS", "BUILD": "BUILT", "WEIGHTS": "WEIGHT"}
MERGE = {("COME", "IN"): "COMMENT", ("ROAD", "WORK"): "ROADWORK", ("WAIT", "LIST"): "WAITLIST"}


def build(variant):
    order = VARIANTS[variant]
    words = [w for s in json.load(open(f"{RAW}/talking_head_1011.json")) for w in s["words"]]
    fc, out_segs, out_words, t = [], [], [], 0.0
    for i, name in enumerate(order):
        a, b = TAKES[name]
        d = b - a
        fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                  f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.015:.3f}:d=0.015[a{i}];")
        toks = []
        for w in words:
            if not (w["e"] > a + 0.08 and w["s"] < b - 0.02):
                continue
            tok = "".join(ch for ch in w["w"].upper() if ch.isalnum() or ch == "'").strip("'")
            if not tok:
                continue
            tok = FIX.get(tok, tok)
            if toks and (toks[-1][0], tok) in MERGE:
                toks[-1] = (MERGE[(toks[-1][0], tok)], toks[-1][1], w["e"])
                continue
            toks.append((tok, w["s"], w["e"]))
        for tok, ws_, we_ in toks:
            out_words.append({"w": tok, "s": round((t + max(0, ws_ - a)) / SPEED, 3),
                              "e": round((t + min(d, we_ - a)) / SPEED, 3), "seg": i})
        out_segs.append({"i": i, "name": name, "start": round(t / SPEED, 3), "end": round((t + d) / SPEED, 3)})
        t += d
    n = len(order)
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];")
    # iPhone footage is full-range: convert to tv range or skin renders orange in the browser renderer
    fc.append(f"[vc]setpts=PTS/{SPEED},fps=30,scale=in_range=pc:out_range=tv,format=yuv420p[vo];"
              f"[ac]atempo={SPEED},loudnorm=I=-14:TP=-1.5:LRA=9[ao]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", SRC, "-filter_complex", "".join(fc),
                    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    f"assets/media/aroll_{variant}.mp4"], check=True)
    json.dump({"variant": variant, "duration": round(t / SPEED, 3), "segments": out_segs, "words": out_words},
              open(f"work/edl_{variant}.json", "w"), indent=1)
    print(variant, "duration", round(t / SPEED, 2))
    for s in out_segs:
        print("  ", s["i"], s["name"], s["start"], s["end"],
              " ".join(w["w"] for w in out_words if w["seg"] == s["i"]))


if __name__ == "__main__":
    for v in (sys.argv[1:] or list(VARIANTS)):
        build(v)
