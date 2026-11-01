"""Retention sound design for talking-head reels: real-sounding, layered SFX + a cue sheet -> <audio> tags.

The editorial kit's caption SFX (tick / key / whoom) sit ~20 dB under the voice and are felt, not heard. This adds
the AUDIBLE layer that carries attention through a reel (Matteo 2026-11-01: "my sound effect game is lacking"):

    python3 -P sound_design.py <outdir>          # (re)make every SFX below as 48 kHz stereo WAV

    import sound_design as sd
    tags = sd.tags([("hit", 1.20, 0.8), ("whoosh", 3.4, 0.6), ...], sfx_dir="assets/sfx/sd", track0=40)

Library (all synthesised here from layered noise, sines and a small room reverb: no downloads, no licences):
  hit        punch impact: transient crack + body thump + sub tail + room             (KO, a punch on a word)
  boom       cinematic hit: sub drop + noise burst + long reverb tail                  (the verdict line, a slam card)
  whoosh     short stereo pass-by (0.35 s), peaks at +0.18 s                          (cards, b-roll whip-ins, jump cuts)
  whoosh_l   long whoosh (0.8 s), peaks at +0.55 s                                     (into a big card)
  riser      2.0 s tension build (rising filtered noise + pitch sweep), ends hard     (into the reveal; cut the bed after)
  rev        reverse swell (0.9 s) that sucks into its end                             (lead-in to a slam)
  bell       boxing / Muay Thai ring bell, two strikes                                 ("my first fight")
  heart      two heartbeats (1.3 s)                                                    (pressure line before the walk-out)
  shutter    camera shutter + tiny freeze ring                                         (freeze frame on the foul)
  thud       soft low thud (0.25 s)                                                    (each item of a list, a number)
  glitch     0.18 s digital stutter                                                    (pattern interrupt, sparingly)

Rules (reel-sound-design skill, `.claude/skills/reel-sound-design/SKILL.md`):
- Every visual change gets a sound; every sound has a visual. Nothing plays over a spoken word's consonant attack
  unless it is the hit on that word.
- Peak SFX ~6-10 dB under the voice; booms/hits may touch -3 dB under it for one frame. Voice always wins.
- Silence is an SFX: cut the music 0.1 s before the biggest line, let the riser end hard, then the boom.
- Max one boom per 10 s, max one glitch per reel. Whooshes vary (3 seeded variants) so repeats never sound copied.
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
RNG = np.random.default_rng(7)


def _t(sec):
    return np.arange(int(SR * sec)) / SR


def _lp(x, hz):
    a = np.exp(-2 * np.pi * hz / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):  # one-pole; fine for <3 s clips
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def _lp_fast(x, hz):
    # FFT brick-ish lowpass with a soft knee: fast for long buffers
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / hz) ** 4)
    return np.fft.irfft(X, len(x))


def _hp_fast(x, hz):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 - 1 / (1 + (f / max(hz, 1)) ** 4)
    return np.fft.irfft(X, len(x))


def _bp_sweep(n, f0, f1, q=3.0, seed=0):
    """Noise through a band that sweeps f0 -> f1 (log), done in short overlapping FFT blocks."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 2048
    hop = blk // 2
    win = np.hanning(blk)
    for s in range(0, n, hop):
        seg = x[s:s + blk]
        if len(seg) < blk:
            seg = np.pad(seg, (0, blk - len(seg)))
        c = f0 * (f1 / f0) ** min(1, s / max(1, n - 1))
        X = np.fft.rfft(seg * win)
        f = np.fft.rfftfreq(blk, 1 / SR)
        bw = c / q
        X *= np.exp(-0.5 * ((f - c) / bw) ** 2)
        y = np.fft.irfft(X, blk)
        e = min(n, s + blk)
        out[s:e] += y[: e - s]
    return out


def _env(n, attack, decay):
    i = np.arange(n)
    a = np.minimum(1, i / max(1, int(SR * attack)))
    return a * np.exp(-i / (SR * decay))


def _reverb(x, seconds=1.2, wet=0.25, tone=5000, seed=1):
    """Small-room / hall reverb: exponentially decaying filtered noise IR, convolved via FFT."""
    rng = np.random.default_rng(seed)
    n = int(SR * seconds)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * seconds / 6.9))
    ir = _lp_fast(ir, tone)
    ir[: int(SR * 0.012)] = 0  # pre-delay
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)
    dry = np.pad(x, (0, n))
    return dry * (1 - wet) + y * wet * 3.0


def _stereo(l, r=None, width=0.0, pan=0.0):
    r = l if r is None else r
    if width:
        d = int(SR * 0.004 * width)
        r = np.concatenate([np.zeros(d), r])[: len(l)]
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([l * gl * 1.414, r * gr * 1.414], axis=1)


def _norm(x, peak_db):
    p = np.max(np.abs(x)) + 1e-9
    return x / p * 10 ** (peak_db / 20)


def _fade_out(x, sec):
    n = min(len(x), int(SR * sec))
    x[-n:] *= np.linspace(1, 0, n)[:, None] if x.ndim == 2 else np.linspace(1, 0, n)
    return x


def save(path, x):
    x = np.asarray(x)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ the library

def hit():
    n = int(SR * 0.9)
    i = np.arange(n) / SR
    crack = _hp_fast(RNG.standard_normal(n), 1800) * _env(n, 0.0005, 0.012)
    body = np.sin(2 * np.pi * np.cumsum(180 * np.exp(-i * 30) + 70) / SR) * _env(n, 0.001, 0.07)
    sub = np.sin(2 * np.pi * np.cumsum(60 * np.exp(-i * 6) + 40) / SR) * _env(n, 0.003, 0.12)
    slap = _lp_fast(RNG.standard_normal(n), 2500) * _env(n, 0.0008, 0.035)
    x = 0.55 * crack + 1.0 * body + 0.9 * sub + 0.6 * slap
    x = np.tanh(1.6 * x)
    x = _reverb(x, 0.6, 0.18, 4000)[: int(SR * 1.1)]
    return _norm(_stereo(x, width=0.5), -1.0)


def boom():
    n = int(SR * 2.6)
    i = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(95 * np.exp(-i * 2.2) + 30) / SR) * _env(n, 0.004, 0.9)
    burst = _lp_fast(RNG.standard_normal(n), 1200) * _env(n, 0.001, 0.12)
    crack = _hp_fast(RNG.standard_normal(n), 2500) * _env(n, 0.0005, 0.01)
    x = np.tanh(1.3 * (1.2 * sub + 0.7 * burst + 0.35 * crack))
    x = _reverb(x, 2.4, 0.35, 2500, seed=3)[: int(SR * 3.2)]
    return _fade_out(_norm(_stereo(x, width=1.0), -0.8), 0.6)


def _whoosh(dur, peak, seed, f0=300, f1=4500):
    n = int(SR * dur)
    x = _bp_sweep(n, f0, f1, q=1.6, seed=seed) + 0.5 * _bp_sweep(n, f0 * 0.6, f1 * 0.5, q=2.5, seed=seed + 11)
    i = np.arange(n) / SR
    e = np.exp(-((i - peak) / (peak * 0.55)) ** 2)
    e[i > peak] = np.exp(-((i[i > peak] - peak) / ((dur - peak) * 0.45)) ** 2)
    x *= e
    pan = np.linspace(-0.7, 0.7, n)
    l, r = x * np.cos((pan + 1) * np.pi / 4), x * np.sin((pan + 1) * np.pi / 4)
    return _norm(np.stack([l, r], axis=1), -2.0)


def whoosh(seed=21):
    return _whoosh(0.38, 0.18, seed)


def whoosh_l():
    return _whoosh(0.85, 0.55, 33, 150, 3800)


def riser():
    n = int(SR * 2.0)
    i = np.arange(n) / SR
    noise = _bp_sweep(n, 250, 7000, q=2.2, seed=41)
    tone = np.sin(2 * np.pi * np.cumsum(110 * (2 ** (i / 2.0 * 2.5))) / SR) * 0.35
    tone += np.sin(2 * np.pi * np.cumsum(110.7 * (2 ** (i / 2.0 * 2.5))) / SR) * 0.25  # beating = tension
    x = (noise * 0.9 + tone) * (i / 2.0) ** 2.2
    x[-int(SR * 0.01):] *= np.linspace(1, 0, int(SR * 0.01))  # ends hard
    return _norm(_stereo(x, width=1.0), -2.5)


def rev():
    b = boom()[: int(SR * 0.9)]
    x = b[::-1].copy()
    x *= np.linspace(0, 1, len(x))[:, None] ** 1.5
    return _norm(x, -3.0)


def bell():
    n = int(SR * 2.4)
    i = np.arange(n) / SR
    partials = [(1.0, 1.0), (2.76, 0.55), (5.40, 0.35), (8.93, 0.2), (1.51, 0.3)]
    f0 = 820.0

    def strike():
        s = sum(a * np.sin(2 * np.pi * f0 * p * i) * np.exp(-i * (1.2 + p * 0.9)) for p, a in partials)
        s += 0.4 * _hp_fast(RNG.standard_normal(n), 3000) * _env(n, 0.0003, 0.006)  # hammer
        return s
    one = strike()
    x = one.copy()
    d = int(SR * 0.42)
    x[d:] += 0.9 * one[: n - d]
    x = _reverb(x, 1.6, 0.25, 6000, seed=5)[: n]
    return _fade_out(_norm(_stereo(x, width=0.6), -3.0), 0.5)


def heart():
    n = int(SR * 1.4)
    x = np.zeros(n)
    i = np.arange(int(SR * 0.25)) / SR

    def beat(f):
        return np.sin(2 * np.pi * np.cumsum(f * np.exp(-i * 9) + 38) / SR) * _env(len(i), 0.004, 0.06)
    for t0, f, a in ((0.0, 70, 1.0), (0.18, 62, 0.7), (0.75, 70, 1.0), (0.93, 62, 0.7)):
        s = int(SR * t0)
        x[s:s + len(i)] += a * beat(f)
    x = _lp_fast(np.tanh(2 * x), 400)
    return _norm(_stereo(x), -2.0)


def shutter():
    n = int(SR * 0.9)
    x = np.zeros(n)
    for t0, a in ((0.0, 1.0), (0.055, 0.7)):
        s = int(SR * t0)
        m = int(SR * 0.02)
        x[s:s + m] += a * _hp_fast(RNG.standard_normal(m), 2000) * _env(m, 0.0002, 0.004)
    i = np.arange(n) / SR
    ring = (np.sin(2 * np.pi * 2093 * i) + 0.5 * np.sin(2 * np.pi * 3136 * i)) * np.exp(-i * 4) * 0.12
    ring[: int(SR * 0.06)] = 0
    x += ring
    return _norm(_stereo(x, width=0.3), -4.0)


def thud():
    n = int(SR * 0.3)
    i = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-i * 25) + 55) / SR) * _env(n, 0.001, 0.05)
    x += 0.2 * _lp_fast(RNG.standard_normal(n), 1500) * _env(n, 0.0005, 0.01)
    return _norm(_stereo(np.tanh(1.5 * x)), -3.0)


def glitch():
    n = int(SR * 0.18)
    rng = np.random.default_rng(9)
    x = np.zeros(n)
    s = 0
    while s < n:
        m = int(SR * rng.uniform(0.008, 0.025))
        f = rng.choice([220, 440, 880, 1760, 3520])
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(m) / SR)) * rng.uniform(0.3, 1)
        x[s:s + m] = seg[: max(0, min(m, n - s))]
        s += m
    return _norm(_stereo(_lp_fast(x, 6000)), -8.0)


LIB = {"hit": hit, "boom": boom, "whoosh": whoosh, "whoosh_b": lambda: whoosh(22), "whoosh_c": lambda: whoosh(23),
       "whoosh_l": whoosh_l, "riser": riser, "rev": rev, "bell": bell, "heart": heart, "shutter": shutter,
       "thud": thud, "glitch": glitch}


def make_all(outdir):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in LIB.items():
        save(out / f"{name}.wav", fn())
    return sorted(p.name for p in out.glob("*.wav"))


def dur(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def tags(cues, sfx_dir="assets/sfx/sd", track0=40, total=None, ntracks=6):
    """cues: [(name, start_s, volume 0-1)] -> HyperFrames <audio> tags. Whooshes rotate through 3 variants."""
    rot = ["whoosh", "whoosh_b", "whoosh_c"]
    k = 0
    out = []
    for n, (name, t, v) in enumerate(sorted(cues, key=lambda c: c[1])):
        if name == "whoosh":
            name = rot[k % 3]
            k += 1
        d = dur(Path(sfx_dir) / f"{name}.wav")
        t = max(0.0, t)
        if total is not None:
            d = min(d, max(0.05, total - t))
        out.append(f'<audio id="sd{n}" src="{sfx_dir}/{name}.wav" data-start="{t:.3f}" data-duration="{d:.3f}" '
                   f'data-track-index="{track0 + n % ntracks}" data-volume="{v:.2f}"></audio>')
    return "\n      ".join(out)


def auto_cues(d, ed_plan, broll=None, hook_end=None, slam=()):
    """The default retention layer every editorial build gets (Matteo 2026-11-01: every edit uses it).
    d = EDL, ed_plan = plan.build(...)["plan"] (json str or dict), broll = work/broll.json dict.
    Adds: whoosh on every b-roll whip-in and every jump cut between takes on the face, whoosh out of the hook,
    boom on the slam keyword (drop the kit's sub for it with strip_kit_sub), hit on impact/jab keywords,
    thud on count keywords, shutter on held (frozen) b-roll. Reel-specific cues (bell, heart, riser) go on top."""
    import json as _j
    p = _j.loads(ed_plan) if isinstance(ed_plan, str) else ed_plan
    broll = broll or {}
    cues = []
    covered = [(v["start"], v["start"] + v["dur"]) for v in broll.values()] + [(c["t0"], c["t1"]) for c in p.get("cards", [])]
    inside = lambda t: any(a - 0.05 <= t <= b + 0.05 for a, b in covered)  # noqa: E731
    for k, v in broll.items():
        if not v.get("full"):
            cues.append(("whoosh", v["start"] - 0.18, 0.42))
        if v.get("hold") or k.startswith("freeze"):
            cues.append(("shutter", v["start"] + 0.3, 0.55))
    if hook_end:
        cues.append(("whoosh", hook_end - 0.2, 0.42))
    for t in d.get("joins", []):
        if not inside(t) and (not hook_end or abs(t - hook_end) > 0.3):
            cues.append(("whoosh", t - 0.18, 0.25))
    for c in p.get("cards", []):
        for w in c["words"]:
            if w.get("slam"):
                cues.append(("boom", w["s"] - 0.02, 0.7))
    for ph in p.get("phrases", []):
        for w in ph["words"]:
            if w.get("key") and w.get("fx") in ("impact", "jab"):
                cues.append(("hit", w["s"] - 0.02, 0.55))
            elif w.get("key") and w.get("fx") == "count":
                cues.append(("thud", w["s"], 0.4))
    end = d["duration"] - 0.45
    return [c for c in cues if 0 <= c[1] < end]


def strip_kit_sub(audio_html):
    """Remove the editorial kit's slam 'sub' tags when auto_cues puts a boom there."""
    import re as _re
    return _re.sub(r'\s*<audio id="ed-sfx\d+" src="[^"]*/sub.wav"[^>]*></audio>', "", audio_html)


if __name__ == "__main__":
    print(make_all(sys.argv[1] if len(sys.argv) > 1 else "sfx_sd"))
