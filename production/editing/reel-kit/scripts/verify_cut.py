"""Check an assembled A-roll for stutters, fillers and double cuts before it goes anywhere.

    python -P verify_cut.py assets/media/aroll_A.mp4 work/edl_A.json "<full script text>"

Re-transcribes the cut with a disfluency prompt and reports: words repeated back to back, fillers, low-confidence
words, any word straddling a join (+-0.15 s), and the diff against the script. Exit 1 if anything needs a look.
"""
import difflib, json, re, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

src, edl_path, script = sys.argv[1:4]
edl = json.load(open(edl_path, encoding="utf-8"))
joins = [s["start"] for s in edl["segments"][1:]]
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
model = WhisperModel("medium.en", device="cpu", compute_type="int8")
segs, _ = model.transcribe(np.frombuffer(pcm, dtype=np.float32), word_timestamps=True, beam_size=5,
                           initial_prompt="Umm, so, uh, I, I mean, like... he, he would, um, step off the line.", condition_on_previous_text=False)
ws = [w for s in segs for w in s.words]
norm = lambda t: re.sub(r"[^A-Z0-9']", "", t.upper())
toks = [norm(w.word) for w in ws]
issues = []
for i in range(1, len(ws)):
    if toks[i] and toks[i] == toks[i - 1]:
        issues.append(f"repeat '{ws[i].word.strip()}' at {ws[i].start:.2f}")
for w in ws:
    if norm(w.word) in {"UM", "UMM", "UH", "ER", "AH", "HMM"}:
        issues.append(f"filler '{w.word.strip()}' at {w.start:.2f}")
    if w.probability < 0.45:
        issues.append(f"unclear '{w.word.strip()}' p={w.probability:.2f} at {w.start:.2f}")
    for j in joins:
        if w.start < j - 0.05 < w.end - 0.05 and (w.end - w.start) > 0.2:
            issues.append(f"word '{w.word.strip()}' straddles the join at {j:.2f}")
got = [t for t in toks if t]
want = [norm(t) for t in script.split() if norm(t)]
for op, a, b, c, e in difflib.SequenceMatcher(None, got, want).get_opcodes():
    if op != "equal":
        issues.append(f"{op}: heard '{' '.join(got[a:b])}' vs script '{' '.join(want[c:e])}'")
print("heard:", " ".join(w.word.strip() for w in ws))
print("\n".join(issues) or "clean")
sys.exit(1 if issues else 0)
