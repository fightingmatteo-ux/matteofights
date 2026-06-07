"""
Train a FLUX.1-dev LoRA on Replicate using reference photos.
Output: model version ID (save this — needed for generation).

Usage: python train_lora.py --name matteo --photos_dir ../content-bank/brand/reference-photos
"""
import argparse
import os
import replicate
import zipfile
import tempfile
from pathlib import Path


def zip_photos(photos_dir: str) -> str:
    """Zip all JPG/PNG files in photos_dir into a temp zip."""
    photos = list(Path(photos_dir).glob("*.jpg")) + list(Path(photos_dir).glob("*.png"))
    if not photos:
        raise ValueError(f"No JPG/PNG files found in {photos_dir}")
    print(f"Zipping {len(photos)} photos...")
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    with zipfile.ZipFile(tmp.name, "w") as zf:
        for p in photos:
            zf.write(p, p.name)
    return tmp.name


def train(name: str, photos_dir: str, trigger_word: str) -> str:
    zip_path = zip_photos(photos_dir)

    with open(zip_path, "rb") as f:
        training = replicate.trainings.create(
            model="ostris/flux-dev-lora-trainer",
            version="e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
            input={
                "input_images": f,
                "trigger_word": trigger_word,
                "steps": 1000,
                "lora_rank": 16,
                "learning_rate": 0.0004,
            },
            destination=f"matteofights/{name}",
        )

    print(f"Training started: {training.id}")
    print(f"Status URL: https://replicate.com/p/{training.id}")
    print(f"Poll until complete, then save the model version ID.")
    return training.id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="matteo-lora", help="Model name on Replicate")
    parser.add_argument("--photos_dir", default="../content-bank/brand/reference-photos")
    parser.add_argument("--trigger_word", default="MATTEO", help="Trigger word for the LoRA")
    args = parser.parse_args()

    if not os.getenv("REPLICATE_API_TOKEN"):
        raise EnvironmentError("Set REPLICATE_API_TOKEN env var first")

    train(args.name, args.photos_dir, args.trigger_word)
