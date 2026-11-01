"""Build work/takes.json from word anchors, cutting only inside real silence (voice.wav energy), never on Whisper ends.
   python3 work/make_takes.py"""
import json, subprocess
import numpy as np
pcm = subprocess.run(["ffmpeg","-v","error","-i","assets/voice.wav","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True,check=True).stdout
x = np.frombuffer(pcm, np.float32); H = 160
db = np.array([20*np.log10(np.sqrt(np.mean(x[i:i+H]**2))+1e-9) for i in range(0, len(x)-H, H)])
db = np.convolve(db, np.ones(3)/3, mode="same")
SPEECH = -38.0
W = json.load(open("work/words.json"))
def idx(word, near):
    """the word (case/punct-insensitive) whose start is closest to `near`"""
    n = lambda s: "".join(c for c in s.upper() if c.isalnum() or c == "'")
    c = [i for i, w in enumerate(W) if n(w["text"]) == word.upper() and abs(w["start"] - near) < 1.5]
    assert c, (word, near)
    return min(c, key=lambda i: abs(W[i]["start"] - near))
def gap(i):
    """silence between word i and i+1 -> (run_start, run_end) in seconds, or a single quiet frame"""
    a, b = W[i]["end"] - 0.2, W[i + 1]["start"] + 0.35
    f0, f1 = int(a * 100), int(b * 100)
    m = db[f0:f1] < SPEECH
    best, run = None, None
    for k, q in enumerate(m):
        if q and run is None: run = k
        if (not q or k == len(m) - 1) and run is not None:
            e = k if not q else k + 1
            if best is None or e - run > best[1] - best[0]: best = (run, e)
            run = None
    if best and best[1] - best[0] >= 4:
        return (f0 + best[0]) / 100, (f0 + best[1]) / 100
    k = int(np.argmin(db[f0:f1])); t = (f0 + k) / 100
    return t, t
def start_at(word, near, lead=0.06):
    i = idx(word, near); r0, r1 = gap(i - 1)
    return round(max(r0, r1 - lead), 3)
def end_after(word, near, tail=0.12):
    i = idx(word, near); r0, r1 = gap(i)
    return round(min(r1, r0 + tail), 3)
def tighten(a, b, maxp=0.5, keep=0.32):
    """split [a,b] wherever a pause inside is longer than maxp, keeping `keep` s of it"""
    out, cur = [], a
    f0, f1 = int(a * 100), int(b * 100)
    m = db[f0:f1] < SPEECH
    run = None
    for k, q in enumerate(list(m) + [False]):
        if q and run is None: run = k
        if not q and run is not None:
            ra, rb = (f0 + run) / 100, (f0 + k) / 100
            if rb - ra > maxp and ra > a + 0.2 and rb < b - 0.2:
                out.append([round(cur, 3), round(ra + keep / 2, 3)]); cur = rb - keep / 2
            run = None
    out.append([round(cur, 3), round(b, 3)])
    return out
T = {}
# body (Body 3): "Someone told me ... They should have disqualified me" / "I thought fighting was about hurting people"
T["body1"] = tighten(start_at("SOMEONE", 61.08), end_after("ME", 73.0, tail=0.25))
T["body2"] = tighten(start_at("I", 74.0), end_after("PEOPLE", 75.46, tail=0.22))
# share (Share 3)
T["share"] = tighten(start_at("IF", 234.12), end_after("KNEW", 238.78, tail=0.2))
# loop takes: open = hook -> "his sixth", end = "It's about control" -> bridge.  seam = the pause before the hook
L = {"A": ("ITS", 96.40, "KNOW", 101.14, "I", 101.32, "SIXTH", 107.40),
     "B": ("ITS", 108.86, "KNOW", 113.84, "MY", 114.04, "SIXTH", 120.42),
     "C": ("ITS", 158.90, "ME", 163.20, "SHOULD", 163.98, "6TH", 169.14),
     "D": ("ITS", 170.50, "WHY", 174.90, "MY", 175.12, "6TH", 180.42),
     "E": ("ITS", 204.06, "FROM", 209.26, "ONE", 209.52, "SIXTH", 214.40)}
for v, (w0, t0, wb, tb, wh, th, wl, tl) in L.items():
    T["end" + v] = tighten(start_at("IT'S", t0), end_after(wb, tb, tail=0.1), maxp=0.45, keep=0.28)
    T["open" + v] = tighten(start_at(wh, th, lead=0.05), end_after(wl, tl, tail=0.3), maxp=0.45, keep=0.28)
def first_speech(t, thr=-34.0):
    k = int(t * 100)
    while db[k] < thr: k += 1
    return k / 100
# video starts on the first sound of the hook (frame 0 already speaks), body2 drops "'cause"
for v in L:
    a = T["open" + v][0][0]; T["open" + v][0][0] = round(max(a, first_speech(a) - 0.05), 3)
T["body2"] = [[74.11, 76.06]]
T["openC"] = [[T["openC"][0][0], 166.66], [166.92, 169.75]]
cfg = {"src": "assets/raw.mp4", "audio_src": "assets/voice.wav", "words": "work/words_asm.json", "speed": 1.0, "takes": T,
       "variants": {v: ["open" + v, "body1", "share", "body2", "end" + v] for v in L},
       "fix": {"6TH": "SIXTH", "IS": "IS"}}
json.dump(cfg, open("work/takes.json", "w"), indent=1)
# assemble.py reads {text,start,end}
json.dump(W, open("work/words_asm.json", "w"))
for k, r in T.items(): print(k, r)
