"""Synthesise the editorial kit's caption SFX and a soft piano bed (no downloads, no licences).

  python -P make_audio.py <outdir> [bed_seconds]

Writes tick.wav, key.wav, whoom.wav, shimmer.wav, sub.wav and bed.wav (mono 48 kHz). The kit keeps only the
SFX in git; plan.install() writes a bed per reel into its gitignored assets/media/.
Modelled on the kaixerb reference (content-bank/references/2026-10-20-kaixerb-caption-sfx.md): ~50 ms tonal
ticks at ~1.3 kHz on caption changes, a 0.35 s swell on keywords, a high shimmer on pop-ins, a 40-90 Hz sub on
the black dip, and a quiet felt-piano bed. The bed is a placeholder: a trending sound added in the IG app wins.
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(SR * sec)) / SR


def env(x, attack, decay):
    n = len(x)
    a = np.minimum(1, np.arange(n) / max(1, int(SR * attack)))
    return x * a * np.exp(-np.arange(n) / (SR * decay))


def norm(x, peak_db):
    return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)


def save(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def lowpass(x, hz):
    # one-pole, run twice: soft and cheap
    a = np.exp(-2 * np.pi * hz / SR)
    for _ in range(2):
        y = np.empty_like(x); acc = 0.0
        for i, v in enumerate(x):
            acc = (1 - a) * v + a * acc; y[i] = acc
        x = y
    return x


def tick():
    x = t(0.07)
    s = np.sin(2 * np.pi * 1320 * x) + 0.35 * np.sin(2 * np.pi * 2640 * x)
    return norm(env(s, 0.002, 0.012), -6)


def key():
    x = t(0.45)
    f = 1380 * (1 + 0.02 * np.exp(-x * 30))  # tiny pitch settle = "ding" with body
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(2 * np.pi * 690 * x)
    return norm(env(s, 0.004, 0.11), -5)


def whoom():
    x = t(0.6)
    n = rng.standard_normal(len(x))
    n = lowpass(n, 900)
    shape = np.sin(np.pi * np.minimum(1, x / 0.6)) ** 2
    body = 0.5 * np.sin(2 * np.pi * (180 - 80 * x) * x)
    return norm((n + body) * shape, -6)


def shimmer():
    x = t(0.35)
    s = sum(np.sin(2 * np.pi * f * x + p) for f, p in [(6200, 0), (6750, 1), (7400, 2)])
    s *= 1 + 0.5 * np.sin(2 * np.pi * 28 * x)
    return norm(env(s, 0.01, 0.07), -12)


def sub():
    x = t(1.4)
    f = 62 * np.exp(-x * 0.8) + 34
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = env(rng.standard_normal(len(x)), 0.0005, 0.004) * 0.3
    return norm(env(s, 0.003, 0.45) + click, -3)


def piano_note(midi, dur, vel):
    f = 440 * 2 ** ((midi - 69) / 12)
    x = t(dur)
    s = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * x * (1 + 0.0004 * k)) * np.exp(-x * (1.2 + 1.6 * k))
            for k in range(5))
    hammer = env(rng.standard_normal(len(x)), 0.0005, 0.01) * 0.02
    return env(s, 0.006, 2.2) * vel + hammer


def bed(seconds):
    # Am - F - C - G, 64 bpm, one chord per bar, sparse broken voicing: calm, "editorial"
    bar = 60 / 64 * 4
    chords = [[57, 64, 69, 72], [53, 60, 65, 69], [48, 55, 64, 67], [55, 62, 67, 71]]
    out = np.zeros(int(SR * (seconds + bar + 6)))  # room for the last bar's ringing notes
    i = 0
    while i * bar < seconds:
        ch = chords[i % 4]
        start = int(SR * i * bar)
        bass = piano_note(ch[0] - 12, bar + 1.5, 0.55)
        out[start:start + len(bass)] += bass
        for k, m in enumerate([ch[1], ch[2], ch[3], ch[2]]):
            s = start + int(SR * k * bar / 4)
            n = piano_note(m, bar, 0.32 if k else 0.4)
            out[s:s + len(n)] += n
        i += 1
    # small room: a few decaying echoes
    wet = np.zeros_like(out)
    for d, g in [(0.031, 0.35), (0.047, 0.3), (0.071, 0.25), (0.113, 0.18), (0.167, 0.12)]:
        k = int(SR * d); wet[k:] += out[:-k] * g
    out = lowpass(out + wet, 4200)[: int(SR * seconds)]
    fade = int(SR * 1.5); out[-fade:] *= np.linspace(1, 0, fade)
    return norm(out, -4)


def rewind():
    # tape rewind: a fast rising warble of chirps that speeds up, ending on a hard click (the "snap back")
    x = t(0.55)
    rate = 18 + 60 * (x / 0.55) ** 2
    f = 900 + 2600 * (x / 0.55) ** 1.5
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(rate) / SR)))
    hiss = lowpass(rng.standard_normal(len(x)), 5000) * 0.6
    body = (0.35 * s + hiss) * np.linspace(0.2, 1, len(x)) ** 2
    click = np.zeros(int(SR * 0.08)); click[:int(SR * 0.004)] = rng.standard_normal(int(SR * 0.004))
    click = env(click + 0.6 * np.sin(2 * np.pi * 2200 * t(0.08)), 0.0003, 0.012)
    return norm(np.concatenate([body, click * 3]), -5)


def punch():
    # jab: short air swish into a tight low thump
    sw = lowpass(rng.standard_normal(int(SR * 0.09)), 3000) * np.linspace(0, 1, int(SR * 0.09)) ** 2
    x = t(0.25)
    thump = env(np.sin(2 * np.pi * np.cumsum(150 * np.exp(-x * 25) + 55) / SR), 0.001, 0.06)
    crack = env(rng.standard_normal(len(x)), 0.0003, 0.008) * 0.5
    return norm(np.concatenate([sw * 0.5, thump + crack]), -3)


def impact():
    # caught: heavier hit, crack + sub tail
    x = t(0.9)
    thump = env(np.sin(2 * np.pi * np.cumsum(110 * np.exp(-x * 12) + 42) / SR), 0.001, 0.22)
    crack = env(lowpass(rng.standard_normal(len(x)), 6000), 0.0003, 0.02) * 0.9
    return norm(thump + crack, -2)


def exhale():
    # relax: a soft breath out, band-limited noise swelling and falling
    x = t(1.0)
    n = lowpass(rng.standard_normal(len(x)), 1800) - lowpass(rng.standard_normal(len(x)), 300) * 0.5
    shape = np.sin(np.pi * x / 1.0) ** 1.5 * np.exp(-x * 0.8)
    return norm(n * shape, -10)


def data():
    # decode: fast random computer blips settling on one note
    out = []
    for i in range(14):
        f = rng.choice([1800, 2400, 3100, 3600, 4200, 2700]) if i < 13 else 2400
        d = 0.028 if i < 13 else 0.12
        out.append(env(np.sign(np.sin(2 * np.pi * f * t(d))) * 0.6, 0.001, d / 2.5))
    return norm(np.concatenate(out), -12)


if __name__ == "__main__":
    od = Path(sys.argv[1]); od.mkdir(parents=True, exist_ok=True)
    for name, fn in [("tick", tick), ("key", key), ("whoom", whoom), ("shimmer", shimmer), ("sub", sub),
                     ("rewind", rewind), ("punch", punch), ("impact", impact), ("exhale", exhale), ("data", data)]:
        save(od / f"{name}.wav", fn())
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    if secs:
        save(od / "bed.wav", bed(secs))
    print(f"sfx -> {od}")
