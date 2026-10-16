"""Score every recorded take of every beat so the best one is picked on the audio, not on the transcript.

    python -P score_takes.py <original recording> <candidates.json> <out.json>

candidates.json: {"beat": {"script": "the line as written", "takes": [[start, end], ...]}, ...} (source seconds)
For each take: re-transcribes just that range with a disfluency prompt (Whisper otherwise cleans "um" and
stutters away), then measures word confidence, mid-sentence hesitations (> 0.45 s between words that are not
across a full stop), repeated words, fillers, and how closely the words match the script. Lower `penalty` = better.
Learned 2026-10-16: picking takes from the clean transcript alone shipped stutters and double cuts.
"""
import difflib, json, re, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

src, cand_path, out_path = sys.argv[1:4]
cands = json.load(open(cand_path, encoding="utf-8"))
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, dtype=np.float32)
model = WhisperModel("medium.en", device="cpu", compute_type="int8")
PROMPT = "Umm, so, uh, I, I mean, like... he, he would, um, step off the line."
FILLERS = {"UM", "UMM", "UH", "UHH", "ER", "AH", "HMM", "LIKE", "OKAY", "SO"}
norm = lambda t: re.sub(r"[^A-Z0-9' ]", "", t.upper().replace("-", " ")).split()

result = {}
for beat, c in cands.items():
    target = norm(c["script"])
    rows = []
    for a, b in c["takes"]:
        clip = audio[int((a - 0.05) * 16000): int((b + 0.25) * 16000)]
        segs, _ = model.transcribe(clip, word_timestamps=True, beam_size=5, initial_prompt=PROMPT,
                                   condition_on_previous_text=False, vad_filter=False)
        ws = [w for s in segs for w in s.words]
        toks = [(norm(w.word) or [""])[0] for w in ws]
        probs = [w.probability for w in ws]
        hes = 0
        for w0, w1 in zip(ws, ws[1:]):
            if w1.start - w0.end > 0.45 and not re.search(r"[.?!,]$", w0.word.strip()):
                hes += 1
        reps = sum(1 for x, y in zip(toks, toks[1:]) if x and x == y)
        lead_fill = sum(1 for t in toks if t in FILLERS and t not in target)
        sim = difflib.SequenceMatcher(None, [t for t in toks if t], target).ratio()
        low = sum(1 for p in probs if p < 0.5)
        pen = round((1 - sim) * 10 + hes * 2.5 + reps * 4 + lead_fill * 3 + low * 1.5 + (1 - (min(probs) if probs else 0)) * 2, 2)
        rows.append({"take": [a, b], "text": " ".join(w.word.strip() for w in ws), "sim": round(sim, 3),
                     "hesitations": hes, "repeats": reps, "fillers": lead_fill, "low_conf_words": low,
                     "min_prob": round(min(probs), 2) if probs else None, "penalty": pen})
        print(f"{beat:8} {a:7.2f}-{b:7.2f} pen {pen:5.2f} sim {sim:.2f} hes {hes} rep {reps} fill {lead_fill} low {low} | {rows[-1]['text'][:90]}", flush=True)
    rows.sort(key=lambda r: r["penalty"])
    result[beat] = rows
json.dump(result, open(out_path, "w", encoding="utf-8"), indent=1)
print("best:", {k: v[0]["take"] for k, v in result.items()})
