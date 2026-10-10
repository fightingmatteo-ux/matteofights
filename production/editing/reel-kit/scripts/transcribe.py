"""Word-level Whisper transcription -> JSON [{text,start,end}] + readable segment dump.

Usage: python -I transcribe.py <media> <out.json> [model]
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "small.en"

# Decode with ffmpeg (16 kHz mono float32) instead of PyAV.
pcm = subprocess.run(
    ["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
    capture_output=True, check=True,
).stdout
audio = np.frombuffer(pcm, dtype=np.float32)

model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(audio, word_timestamps=True, vad_filter=False, beam_size=5)

words, lines = [], []
for seg in segments:
    lines.append(f"[{seg.start:6.2f}-{seg.end:6.2f}] {seg.text.strip()}")
    for w in seg.words:
        words.append({"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})

with open(out, "w", encoding="utf-8") as f:
    json.dump(words, f, indent=1, ensure_ascii=False)
print("\n".join(lines))
