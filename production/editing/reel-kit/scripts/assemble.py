"""Multi-take / talking-points assembler: pick the best take of each beat, build one A-roll per variant.

Matteo records talking points freely (several takes per point). Claude reads the transcript printed by
transcribe.py, picks a source range per beat, and lists the beats per variant (A/B/C hook tests) in
work/takes.json:

  {
    "src": "assets/raw.mp4",            # prepped clip (prep_footage.sh), relative to the reel folder
    "words": "work/words.json",          # transcribe.py output [{text,start,end}]
    "speed": 1.0,                        # natural speed. Any time-stretch made Matteo's voice sound robotic
    "takes":    {"hook": [3.88, 7.45], "point1": [12.2, 18.9], ...},   # source seconds
    "variants": {"A": ["hook", "point1", ...], "B": ["hookB", "point1", ...]},
    "fix":      {"MAP": "MAT"}            # optional Whisper corrections for captions (UPPERCASE)
  }

Usage:  python -P assemble.py work/takes.json [A B C]
Writes per variant: assets/media/aroll_<V>.mp4 and work/edl_<V>.json
  {"variant", "duration", "segments": [{i,name,start,end}], "words": [{w,s,e,seg}]}  (output seconds)

Rules baked in (learned on worst-decision, 2026-10-12):
- Ranges keep natural tails after the last word (room tone). Whisper word ends land early; trimming on
  them clips words. Leave ~0.3-0.6 s after a reveal line: that dead space is the tension beat.
- 12 ms fades at every join so cuts never click.
"""
import json
import subprocess
import sys
from pathlib import Path

MERGE = {("COME", "IN"): "COMMENT", ("ROAD", "WORK"): "ROADWORK", ("WAIT", "LIST"): "WAITLIST"}


def norm(text, fix):
    tok = "".join(ch for ch in text.upper() if ch.isalnum() or ch == "'").strip("'")
    return fix.get(tok, tok)


def build(cfg, variant):
    speed = cfg.get("speed", 1.0)
    fix = cfg.get("fix", {})
    words = json.load(open(cfg["words"], encoding="utf-8"))
    fc, segs, out_words, inputs, t = [], [], [], [], 0.0
    order = cfg["variants"][variant]
    for i, name in enumerate(order):
        a, b = cfg["takes"][name]
        d = b - a
        # one input per take with fast seek: decoding only the take, not the whole clip
        inputs += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", cfg["src"]]
        if cfg.get("audio_src"):  # voice from the untouched original recording (same timeline)
            inputs += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", cfg["audio_src"]]
        vi, ai = (2 * i, 2 * i + 1) if cfg.get("audio_src") else (i, i)
        fc.append(f"[{vi}:v]setpts=PTS-STARTPTS[v{i}];"
                  f"[{ai}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                  f"afade=t=out:st={d - 0.015:.3f}:d=0.015[a{i}];")
        toks = []
        for w in words:
            if not (w["end"] > a + 0.08 and w["start"] < b - 0.02):
                continue
            tok = norm(w["text"], fix)
            if not tok:
                continue
            if toks and (toks[-1][0], tok) in MERGE:
                toks[-1] = (MERGE[(toks[-1][0], tok)], toks[-1][1], w["end"])
                continue
            toks.append((tok, w["start"], w["end"]))
        for tok, s, e in toks:
            out_words.append({"w": tok, "s": round((t + max(0, s - a)) / speed, 3),
                              "e": round((t + min(d, e - a)) / speed, 3), "seg": i})
        segs.append({"i": i, "name": name, "start": round(t / speed, 3), "end": round((t + d) / speed, 3)})
        t += d
    n = len(order)
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];")
    # Rubber Band (formant-preserving) when ffmpeg has it: atempo smears speech into a phasey sound
    rb = "rubberband" in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    tempo = "" if speed == 1 else (f"rubberband=tempo={speed}:formant=preserved:pitchq=quality," if rb else f"atempo={speed},")
    fc.append(f"[vc]setpts=PTS/{speed},fps=30,format=yuv420p[vo];[ac]{tempo}highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
    Path("assets/media").mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", "".join(fc),
                    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-g", "30", "-keyint_min", "30",
                    "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    f"assets/media/aroll_{variant}.mp4"], check=True)
    edl = {"variant": variant, "duration": round(t / speed, 3), "segments": segs, "words": out_words}
    json.dump(edl, open(f"work/edl_{variant}.json", "w", encoding="utf-8"), indent=1)
    print(f"{variant}: {edl['duration']:.1f}s")
    for s in segs:
        print(f"  {s['start']:6.2f}-{s['end']:6.2f} {s['name']:<12}",
              " ".join(w["w"] for w in out_words if w["seg"] == s["i"]))


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    for v in sys.argv[2:] or list(cfg["variants"]):
        build(cfg, v)
