"""
CLI to generate a clip via RunPod and add it to the catalog.

Usage:
  # Atmosphere mode (text-to-video, no likeness):
  python generate.py atmosphere \
    --shot_type atmosphere \
    --prompt "dark moody gym, red heavy bag, dramatic lighting" \
    --tags gym red-bag atmosphere \
    --duration 5

  # Likeness mode (still then animate):
  python generate.py likeness \
    --shot_type arrival \
    --prompt "MATTEO dark moody gym entrance, red boxing hand wraps, cinematic" \
    --tags gym entrance red-wraps \
    --duration 5
"""
import argparse
import json
import os
import time
import urllib.request
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, os.path.dirname(__file__))
from catalog import Catalog, AssetEntry

RUNPOD_ENDPOINT = os.getenv("RUNPOD_ENDPOINT_ID")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "../content-bank/catalog.json")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "../content-bank/ai-assets")
BRAND_STYLE_PATH = os.path.join(os.path.dirname(__file__), "../content-bank/brand/brand_style.json")

SHOT_TYPE_TO_FOLDER = {
    "arrival": "arrivals",
    "training": "training",
    "atmosphere": "atmosphere",
    "outdoor": "outdoor",
    "lifestyle": "lifestyle",
    "hero": "hero-shots",
}

SHOT_TYPE_TO_PRESET = {
    "arrival": "gym",
    "training": "gym",
    "atmosphere": "gym",
    "outdoor": "outdoor",
    "lifestyle": "lifestyle",
    "hero": "gym",
}


def load_brand_style():
    # type: () -> dict
    with open(BRAND_STYLE_PATH) as f:
        return json.load(f)


def build_prompt(base_prompt, shot_type):
    # type: (str, str) -> str
    style = load_brand_style()
    preset = SHOT_TYPE_TO_PRESET[shot_type]
    return "{}, {}".format(base_prompt, style[preset])


def call_runpod(workflow, prompt, image_path=None):
    # type: (str, str, str) -> list
    if not RUNPOD_ENDPOINT or not RUNPOD_API_KEY:
        raise EnvironmentError("Set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY env vars")

    payload = {"input": {"workflow": workflow, "prompt": prompt}}
    if image_path:
        payload["input"]["image_path"] = image_path

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.runpod.io/v2/{}/runsync".format(RUNPOD_ENDPOINT),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(RUNPOD_API_KEY),
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())

    return result["output"]["output_files"]


def download_file(remote_path, local_path):
    # type: (str, str) -> None
    filename = os.path.basename(remote_path)
    url = "https://api.runpod.io/v2/{}/files/{}".format(RUNPOD_ENDPOINT, filename)
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer {}".format(RUNPOD_API_KEY)}
    )
    with urllib.request.urlopen(req) as resp:
        with open(local_path, "wb") as out:
            out.write(resp.read())


def generate_atmosphere(args):
    prompt = build_prompt(args.prompt, args.shot_type)
    print("Generating atmosphere clip: {}".format(prompt))
    output_files = call_runpod("generate_video", prompt)
    return output_files


def generate_likeness(args):
    still_prompt = build_prompt(args.prompt, args.shot_type)
    print("Generating still: {}".format(still_prompt))
    still_files = call_runpod("generate_still", still_prompt)
    still_path = still_files[0]

    clip_prompt = "cinematic motion, smooth camera movement, {}".format(still_prompt)
    print("Animating still to clip...")
    clip_files = call_runpod("generate_clip", clip_prompt, still_path)
    return clip_files


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI video clips via RunPod and add them to the content catalog."
    )
    parser.add_argument("mode", choices=["atmosphere", "likeness"],
                        help="atmosphere: text-to-video (no likeness); likeness: FLUX still + Wan2.1 animation")
    parser.add_argument("--shot_type", required=True,
                        choices=["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"],
                        help="Shot type determines folder and brand style preset")
    parser.add_argument("--prompt", required=True,
                        help="Base prompt; brand style is appended automatically")
    parser.add_argument("--tags", nargs="+", default=[],
                        help="Space-separated tags for catalog querying")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Clip duration in seconds (default: 5.0)")
    parser.add_argument("--mood", default="cinematic",
                        help="Mood tag for catalog (default: cinematic)")
    args = parser.parse_args()

    if args.mode == "atmosphere":
        output_files = generate_atmosphere(args)
        likeness = False
    else:
        output_files = generate_likeness(args)
        likeness = True

    folder = SHOT_TYPE_TO_FOLDER[args.shot_type]
    for remote_path in output_files:
        ext = os.path.splitext(remote_path)[1]
        filename = "{}_{}{}" .format(args.shot_type, int(time.time()), ext)
        local_rel = "ai-assets/{}/{}".format(folder, filename)
        local_abs = os.path.join(ASSETS_DIR, folder, filename)

        print("Downloading {} -> {}".format(remote_path, local_abs))
        download_file(remote_path, local_abs)

        cat = Catalog(CATALOG_PATH)
        entry = AssetEntry(
            file=local_rel,
            source="ai",
            shot_type=args.shot_type,
            style_preset=SHOT_TYPE_TO_PRESET[args.shot_type],
            mood=args.mood,
            likeness=likeness,
            tags=args.tags,
            duration_sec=args.duration,
            prompt=args.prompt,
            generated_at=date.today().isoformat(),
        )
        cat.add(entry)
        print("Added to catalog: {} -> {}".format(entry.id, local_rel))


if __name__ == "__main__":
    main()
