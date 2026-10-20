"""Cut Matteo out of the A-roll so a big hook word can sit BEHIND his head (the kaixerb "HEY" look).

  python cutout.py <aroll.mp4> <out_fg.webm> [--from S] [--to S] [--model rvm_mobilenetv3_fp32.onnx]

Runs Robust Video Matting (video model: recurrent, so hair edges stay stable frame to frame) on CPU with
onnxruntime and writes a VP9 WebM with alpha: the person only, same size/fps/timing as the A-roll range.
The template stacks: A-roll -> behind-text -> this WebM (data-start = --from). Works in a cloud session:
  python3 -m venv .venv && .venv/bin/pip install onnxruntime numpy
  curl -L -o rvm_mobilenetv3_fp32.onnx \
    https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
~0.2-0.4 s per 1080x1920 frame on 4 CPUs, so cut only the seconds that carry behind-text (--from/--to).
"""
import argparse
import json
import subprocess

import numpy as np
import onnxruntime as ort

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--from", dest="t0", type=float, default=0.0)
ap.add_argument("--to", dest="t1", type=float, default=None)
ap.add_argument("--model", default="rvm_mobilenetv3_fp32.onnx")
ap.add_argument("--ratio", type=float, default=0.25, help="RVM downsample_ratio (0.25 suits 1080p)")
a = ap.parse_args()

info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=width,height,r_frame_rate:format=duration", "-of", "json", a.src],
                                 capture_output=True, text=True).stdout)
W, H = info["streams"][0]["width"], info["streams"][0]["height"]
fps = info["streams"][0]["r_frame_rate"]
t1 = a.t1 if a.t1 is not None else float(info["format"]["duration"])
dur = t1 - a.t0

rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a.t0}", "-t", f"{dur}", "-i", a.src, "-an",
                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                       "-r", fps, "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "6M",
                       "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", a.out], stdin=subprocess.PIPE)

so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
ratio = np.array([a.ratio], np.float32)
n = 0
while True:
    buf = rd.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    src = (rgb.astype(np.float32) / 255).transpose(2, 0, 1)[None]
    fgr, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                     "downsample_ratio": ratio})
    alpha = (np.clip(pha[0, 0], 0, 1) * 255).astype(np.uint8)
    wr.stdin.write(np.dstack([rgb, alpha]).tobytes())
    n += 1
    if n % 30 == 0:
        print(f"{n} frames", flush=True)
wr.stdin.close(); wr.wait(); rd.wait()
print(f"cutout: {n} frames {a.t0:.2f}-{t1:.2f}s -> {a.out}")
