"""
Split a back-to-back SFX audio file into individual clips at silence gaps.
Output: content-bank/sfx/raw/sfx_01.wav, sfx_02.wav, ...

Usage: python split_sfx.py
"""
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pathlib import Path

INPUT = Path(__file__).parent / "creator sound effects.mp3"
OUTPUT_DIR = Path(__file__).parent / "raw"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"Loading {INPUT.name}...")
audio = AudioSegment.from_mp3(INPUT)

print("Splitting on silence...")
chunks = split_on_silence(
    audio,
    min_silence_len=300,   # silence must be at least 300ms
    silence_thresh=-45,    # dBFS threshold for silence
    keep_silence=100,      # keep 100ms of silence on each side
)

print(f"Found {len(chunks)} clips — exporting...")
for i, chunk in enumerate(chunks, start=1):
    out_path = OUTPUT_DIR / f"sfx_{i:02d}.wav"
    chunk.export(out_path, format="wav")
    duration_ms = len(chunk)
    print(f"  sfx_{i:02d}.wav  ({duration_ms}ms)")

print(f"\nDone. Files in: {OUTPUT_DIR}")
print("Listen through and rename each file descriptively (e.g. whoosh-fast.wav).")
