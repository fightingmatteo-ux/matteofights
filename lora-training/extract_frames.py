"""
Extract evenly-spaced frames from a video file.
Usage: python extract_frames.py <video_path> <output_dir> [--every N]
"""
import argparse
import cv2
import os
from pathlib import Path


def extract_frames(video_path: str, output_dir: str, every: int = 15) -> list[str]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    saved = []
    frame_idx = 0
    saved_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % every == 0:
            filename = f"frame_{saved_idx:04d}.jpg"
            out_path = os.path.join(output_dir, filename)
            cv2.imwrite(out_path, frame)
            saved.append(out_path)
            saved_idx += 1
        frame_idx += 1

    cap.release()
    print(f"Extracted {len(saved)} frames to {output_dir}")
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("output_dir")
    parser.add_argument("--every", type=int, default=15, help="Extract every Nth frame")
    args = parser.parse_args()
    extract_frames(args.video_path, args.output_dir, args.every)
