# AI Content System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted AI video generation pipeline that produces cinematic B-roll clips matching Matteo's likeness, stores them in a structured asset library, and lets Claude compile them into reels via Remotion — integrated into Jarvis as a Studio panel.

**Architecture:** RunPod Serverless runs a ComfyUI Docker worker (FLUX.1-dev + Matteo LoRA for stills, Wan2.1 for video). Generated clips land in `content-bank/ai-assets/` cataloged in `catalog.json`. Claude writes Remotion compositions that sequence clips with text overlays and renders MP4s. A TypeScript MCP server exposes three tools to Jarvis: generate_asset, browse_assets, compile_reel.

**Tech Stack:** Python 3.11 (scripts), ComfyUI (generation), Docker + RunPod Serverless (hosting), Replicate API (LoRA training), Remotion + React/TypeScript (compilation), Node.js + @modelcontextprotocol/sdk (Jarvis MCP)

---

## File Map

```
content-bank/
  ai-assets/arrivals/            cinematic gym entrances
  ai-assets/training/            bag work, conditioning
  ai-assets/atmosphere/          gym environment, equipment
  ai-assets/outdoor/             sunny outdoor shots
  ai-assets/lifestyle/           laptop, cafe, focus, planning shots
  ai-assets/hero-shots/          dramatic singles
  ai-assets/stills/              FLUX images pre-animation
  real-footage/training/
  real-footage/talking-head/
  real-footage/events/
  brand/brand_style.json         canonical style presets
  brand/reference-photos/        curated LoRA training images
  catalog.json                   index of all assets

lora-training/
  extract_frames.py              extract frames from video files
  train_lora.py                  kick off Replicate LoRA training job
  requirements.txt

generation/
  Dockerfile                     RunPod worker image
  handler.py                     RunPod serverless entry point
  start.sh                       ComfyUI startup script
  requirements.txt
  workflows/
    generate_still.json          FLUX + LoRA → still
    generate_clip.json           Wan2.1 image-to-video
    generate_video.json          Wan2.1 text-to-video (atmosphere mode)

content-generation/
  catalog.py                     add / query catalog.json
  generate.py                    CLI: call RunPod → download → catalog
  requirements.txt

production/remotion/
  package.json
  remotion.config.ts
  src/Root.tsx
  src/compositions/ReelComposition.tsx
  src/components/VideoClip.tsx
  src/components/TextOverlay.tsx
  src/lib/catalog.ts             reads catalog.json

jarvis/mcp-studio/
  package.json
  src/index.ts                   MCP server entry
  src/tools/generate_asset.ts
  src/tools/browse_assets.ts
  src/tools/compile_reel.ts
```

---

## Phase 1 — Foundation

### Task 1: Folder Structure + Brand Style

**Files:**
- Create: `content-bank/brand/brand_style.json`
- Create: `content-bank/catalog.json`
- Create: all `.gitkeep` files for empty folders

- [ ] **Step 1: Create folder tree**

```bash
cd "c:\Users\matte\Documents\Claude\Projects\@matteofights"
mkdir -p content-bank/ai-assets/arrivals
mkdir -p content-bank/ai-assets/training
mkdir -p content-bank/ai-assets/atmosphere
mkdir -p content-bank/ai-assets/outdoor
mkdir -p content-bank/ai-assets/lifestyle
mkdir -p content-bank/ai-assets/hero-shots
mkdir -p content-bank/ai-assets/stills
mkdir -p content-bank/real-footage/training
mkdir -p content-bank/real-footage/talking-head
mkdir -p content-bank/real-footage/events
mkdir -p content-bank/brand/reference-photos
mkdir -p lora-training
mkdir -p generation/workflows
mkdir -p content-generation
```

- [ ] **Step 2: Create brand_style.json**

`content-bank/brand/brand_style.json`:
```json
{
  "gym": "dark moody gym, red boxing hand wraps, red heavy bag background, dramatic shadows, cinematic low-key lighting, fighter atmosphere",
  "outdoor": "natural sunlight, warm golden tones, outdoor environment, fighter lifestyle, candid energy, sun-lit skin",
  "lifestyle": "natural ambient light, laptop or coffee visible, focused energy, fighter mindset, candid indoor or outdoor setting"
}
```

- [ ] **Step 3: Initialize catalog.json**

`content-bank/catalog.json`:
```json
[]
```

- [ ] **Step 4: Add .gitkeep files to empty asset folders**

```bash
touch content-bank/ai-assets/arrivals/.gitkeep
touch content-bank/ai-assets/training/.gitkeep
touch content-bank/ai-assets/atmosphere/.gitkeep
touch content-bank/ai-assets/outdoor/.gitkeep
touch content-bank/ai-assets/lifestyle/.gitkeep
touch content-bank/ai-assets/hero-shots/.gitkeep
touch content-bank/ai-assets/stills/.gitkeep
touch content-bank/real-footage/training/.gitkeep
touch content-bank/real-footage/talking-head/.gitkeep
touch content-bank/real-footage/events/.gitkeep
touch content-bank/brand/reference-photos/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add content-bank/ lora-training/ generation/ content-generation/
git commit -m "feat: scaffold AI content system folder structure"
```

---

## Phase 2 — Reference Data & LoRA Training

### Task 2: Frame Extraction Script

**Files:**
- Create: `lora-training/extract_frames.py`
- Create: `lora-training/requirements.txt`

- [ ] **Step 1: Create requirements.txt**

`lora-training/requirements.txt`:
```
opencv-python-headless==4.9.0.80
```

- [ ] **Step 2: Write extract_frames.py**

`lora-training/extract_frames.py`:
```python
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
```

- [ ] **Step 3: Install + verify**

```bash
cd lora-training
pip install -r requirements.txt
python extract_frames.py --help
```

Expected output: argparse help text printed, no errors.

- [ ] **Step 4: Commit**

```bash
git add lora-training/
git commit -m "feat: add frame extraction script for LoRA training data"
```

---

### Task 3: LoRA Training on Replicate

**Files:**
- Create: `lora-training/train_lora.py`

Prerequisites:
- Replicate account at replicate.com
- API token: set `REPLICATE_API_TOKEN` env var
- 20–35 reference frames placed in `content-bank/brand/reference-photos/`
- Install: `pip install replicate`

- [ ] **Step 1: Write train_lora.py**

`lora-training/train_lora.py`:
```python
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
```

- [ ] **Step 2: Run training**

```bash
cd lora-training
pip install replicate
REPLICATE_API_TOKEN=<your_token> python train_lora.py \
  --name matteo-lora \
  --photos_dir ../content-bank/brand/reference-photos \
  --trigger_word MATTEO
```

Expected: Training job ID printed. Training takes 20–40 minutes on Replicate. Monitor at the printed URL.

- [ ] **Step 3: Save the model version ID**

When training completes at replicate.com, copy the version ID (format: `matteofights/matteo-lora:<version_hash>`). You will need this in Task 5.

- [ ] **Step 4: Commit**

```bash
git add lora-training/train_lora.py
git commit -m "feat: add LoRA training script for Matteo likeness"
```

---

## Phase 3 — RunPod Generation Worker

### Task 4: ComfyUI Workflows

**Files:**
- Create: `generation/workflows/generate_still.json`
- Create: `generation/workflows/generate_clip.json`
- Create: `generation/workflows/generate_video.json`

These are ComfyUI workflow API-format JSONs. The key nodes are shown; full node IDs are assigned during ComfyUI setup.

- [ ] **Step 1: Create generate_still.json (FLUX + LoRA)**

`generation/workflows/generate_still.json`:
```json
{
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "clip": ["11", 0],
      "text": "PLACEHOLDER_PROMPT"
    }
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "clip": ["11", 0],
      "text": "blurry, low quality, deformed face, extra limbs"
    }
  },
  "8": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["13", 0],
      "vae": ["10", 0]
    }
  },
  "9": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "still",
      "images": ["8", 0]
    }
  },
  "10": {
    "class_type": "VAELoader",
    "inputs": { "vae_name": "ae.safetensors" }
  },
  "11": {
    "class_type": "DualCLIPLoader",
    "inputs": {
      "clip_name1": "t5xxl_fp16.safetensors",
      "clip_name2": "clip_l.safetensors",
      "type": "flux"
    }
  },
  "12": {
    "class_type": "UnetLoader",
    "inputs": { "unet_name": "flux1-dev.safetensors", "weight_dtype": "fp8_e4m3fn" }
  },
  "13": {
    "class_type": "KSampler",
    "inputs": {
      "model": ["16", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["15", 0],
      "seed": 42,
      "steps": 25,
      "cfg": 3.5,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1.0
    }
  },
  "14": {
    "class_type": "EmptyLatentImage",
    "inputs": { "width": 768, "height": 1344, "batch_size": 1 }
  },
  "15": {
    "class_type": "EmptySD3LatentImage",
    "inputs": { "width": 768, "height": 1344, "batch_size": 1 }
  },
  "16": {
    "class_type": "LoraLoader",
    "inputs": {
      "model": ["12", 0],
      "clip": ["11", 0],
      "lora_name": "matteo-lora.safetensors",
      "strength_model": 0.9,
      "strength_clip": 0.9
    }
  }
}
```

- [ ] **Step 2: Create generate_clip.json (Wan2.1 image-to-video)**

`generation/workflows/generate_clip.json`:
```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": { "image": "PLACEHOLDER_IMAGE_PATH" }
  },
  "2": {
    "class_type": "WanImageToVideo",
    "inputs": {
      "model": ["3", 0],
      "image": ["1", 0],
      "positive_prompt": "PLACEHOLDER_PROMPT cinematic motion, smooth camera movement",
      "negative_prompt": "static, blurry, low quality",
      "num_frames": 81,
      "fps": 16,
      "steps": 20,
      "cfg": 6.0,
      "seed": 42
    }
  },
  "3": {
    "class_type": "WanModelLoader",
    "inputs": { "model_name": "wan2.1-i2v-14b-480p.safetensors" }
  },
  "4": {
    "class_type": "SaveAnimatedWEBP",
    "inputs": {
      "images": ["2", 0],
      "filename_prefix": "clip",
      "fps": 16,
      "lossless": false,
      "quality": 85
    }
  }
}
```

- [ ] **Step 3: Create generate_video.json (Wan2.1 text-to-video, atmosphere mode)**

`generation/workflows/generate_video.json`:
```json
{
  "1": {
    "class_type": "WanTextToVideo",
    "inputs": {
      "model": ["2", 0],
      "positive_prompt": "PLACEHOLDER_PROMPT",
      "negative_prompt": "static, blurry, low quality, amateur footage",
      "num_frames": 81,
      "fps": 16,
      "width": 480,
      "height": 832,
      "steps": 20,
      "cfg": 6.0,
      "seed": 42
    }
  },
  "2": {
    "class_type": "WanModelLoader",
    "inputs": { "model_name": "wan2.1-t2v-14b-480p.safetensors" }
  },
  "3": {
    "class_type": "SaveAnimatedWEBP",
    "inputs": {
      "images": ["1", 0],
      "filename_prefix": "video",
      "fps": 16,
      "lossless": false,
      "quality": 85
    }
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add generation/workflows/
git commit -m "feat: add ComfyUI workflow templates for still + video generation"
```

---

### Task 5: RunPod Serverless Worker

**Files:**
- Create: `generation/handler.py`
- Create: `generation/start.sh`
- Create: `generation/Dockerfile`
- Create: `generation/requirements.txt`

Prerequisites:
- RunPod account at runpod.io
- RunPod network volume created (50GB minimum) with models downloaded to it (see Step 1 notes)
- Docker installed locally for building

- [ ] **Step 1: Create requirements.txt**

`generation/requirements.txt`:
```
runpod==1.7.0
requests==2.31.0
Pillow==10.2.0
```

**Note on network volume:** Before deploying, SSH into a RunPod GPU pod with the network volume mounted and download models:
```bash
# Run once on a RunPod pod with network volume at /workspace
cd /workspace/ComfyUI/models
# FLUX models
wget https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors -P unet/
wget https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors -P clip/
wget https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors -P clip/
wget https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/ae.safetensors -P vae/
# Wan2.1 models
wget https://huggingface.co/Wan-AI/Wan2.1-I2V-14B-480P/resolve/main/wan2.1-i2v-14b-480p.safetensors -P checkpoints/
wget https://huggingface.co/Wan-AI/Wan2.1-T2V-14B-480P/resolve/main/wan2.1-t2v-14b-480p.safetensors -P checkpoints/
# LoRA (upload your trained .safetensors from Replicate)
# Place at /workspace/ComfyUI/models/loras/matteo-lora.safetensors
```

- [ ] **Step 2: Write handler.py**

`generation/handler.py`:
```python
"""RunPod serverless handler for ComfyUI generation jobs."""
import json
import os
import time
import urllib.request
import urllib.parse
import runpod

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_DIR = "/workspace/workflows"


def load_workflow(workflow_name: str) -> dict:
    path = os.path.join(WORKFLOW_DIR, f"{workflow_name}.json")
    with open(path) as f:
        return json.load(f)


def inject_prompt(workflow: dict, prompt: str, image_path: str | None = None) -> dict:
    """Replace PLACEHOLDER values in workflow with actual prompt."""
    workflow_str = json.dumps(workflow)
    workflow_str = workflow_str.replace("PLACEHOLDER_PROMPT", prompt)
    if image_path:
        workflow_str = workflow_str.replace("PLACEHOLDER_IMAGE_PATH", image_path)
    return json.loads(workflow_str)


def queue_prompt(workflow: dict) -> str:
    data = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["prompt_id"]


def wait_for_output(prompt_id: str, timeout: int = 300) -> list[str]:
    """Poll ComfyUI history until job completes. Returns list of output file paths."""
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
            history = json.loads(resp.read())
        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            files = []
            for node_outputs in outputs.values():
                for key in ("images", "gifs", "videos"):
                    if key in node_outputs:
                        for item in node_outputs[key]:
                            files.append(
                                f"/workspace/ComfyUI/output/{item['filename']}"
                            )
            return files
        time.sleep(2)
    raise TimeoutError(f"ComfyUI job {prompt_id} timed out after {timeout}s")


def handler(job: dict) -> dict:
    """
    Expected job input:
    {
        "workflow": "generate_still" | "generate_clip" | "generate_video",
        "prompt": "your prompt here",
        "image_path": "/path/to/still.jpg"  # required for generate_clip
    }
    Returns: {"output_files": ["/workspace/ComfyUI/output/filename.ext"]}
    """
    inp = job["input"]
    workflow_name = inp["workflow"]
    prompt = inp["prompt"]
    image_path = inp.get("image_path")

    workflow = load_workflow(workflow_name)
    workflow = inject_prompt(workflow, prompt, image_path)
    prompt_id = queue_prompt(workflow)
    output_files = wait_for_output(prompt_id)

    return {"output_files": output_files}


runpod.serverless.start({"handler": handler})
```

- [ ] **Step 3: Write start.sh**

`generation/start.sh`:
```bash
#!/bin/bash
# Start ComfyUI in background, then start RunPod handler
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch &

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to start..."
until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
  sleep 2
done
echo "ComfyUI ready."

# Copy workflow files
cp /app/workflows/*.json /workspace/workflows/

# Start RunPod handler
cd /app
python handler.py
```

- [ ] **Step 4: Write Dockerfile**

`generation/Dockerfile`:
```dockerfile
FROM runpod/pytorch:2.2.1-py3.11-cuda12.1.1-devel-ubuntu22.04

WORKDIR /workspace

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install -r requirements.txt

# Install ComfyUI custom nodes for Wan2.1
RUN cd /workspace/ComfyUI/custom_nodes && \
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

# Create output and workflow dirs
RUN mkdir -p /workspace/ComfyUI/output /workspace/workflows

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY handler.py .
COPY start.sh .
COPY workflows/ ./workflows/

RUN chmod +x start.sh

CMD ["/app/start.sh"]
```

- [ ] **Step 5: Build and push Docker image**

```bash
cd generation
# Replace YOUR_DOCKERHUB_USERNAME
docker build -t YOUR_DOCKERHUB_USERNAME/matteofights-comfyui:latest .
docker push YOUR_DOCKERHUB_USERNAME/matteofights-comfyui:latest
```

Expected: image pushed to Docker Hub. Takes 5–15 minutes on first build.

- [ ] **Step 6: Deploy to RunPod Serverless**

1. Go to runpod.io → Serverless → New Endpoint
2. Container image: `YOUR_DOCKERHUB_USERNAME/matteofights-comfyui:latest`
3. Container disk: 10 GB
4. Network volume: attach the volume with models (50 GB), mount path `/workspace`
5. Min workers: 0 (cold start, saves cost)
6. Max workers: 1
7. Save endpoint — copy the **Endpoint ID** and **API Key**

- [ ] **Step 7: Test the endpoint**

```bash
curl -X POST https://api.runpod.io/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "workflow": "generate_video",
      "prompt": "dark moody gym, red boxing hand wraps, red heavy bag background, dramatic shadows, cinematic low-key lighting, fighter atmosphere, empty boxing gym"
    }
  }'
```

Expected: JSON response with `output_files` array within 60–120 seconds.

- [ ] **Step 8: Commit**

```bash
git add generation/
git commit -m "feat: add RunPod ComfyUI serverless worker"
```

---

## Phase 4 — Catalog + Generation CLI

### Task 6: Catalog Module

**Files:**
- Create: `content-generation/catalog.py`
- Create: `content-generation/requirements.txt`
- Create: `content-generation/test_catalog.py`

- [ ] **Step 1: Create requirements.txt**

`content-generation/requirements.txt`:
```
pytest==8.1.1
```

- [ ] **Step 2: Write test_catalog.py first (TDD)**

`content-generation/test_catalog.py`:
```python
import json
import os
import tempfile
import pytest
from catalog import Catalog, AssetEntry


def make_catalog(entries=None):
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(entries or [], tmp)
    tmp.close()
    return tmp.name


def test_load_empty_catalog():
    path = make_catalog([])
    cat = Catalog(path)
    assert cat.all() == []


def test_add_entry():
    path = make_catalog([])
    cat = Catalog(path)
    entry = AssetEntry(
        id="clip_001",
        file="ai-assets/arrivals/test.mp4",
        source="ai",
        shot_type="arrival",
        style_preset="gym",
        mood="cinematic",
        likeness=True,
        tags=["gym", "entrance"],
        duration_sec=5.0,
        prompt="dark moody gym entrance",
        generated_at="2026-06-07",
    )
    cat.add(entry)
    assert len(cat.all()) == 1
    assert cat.all()[0]["id"] == "clip_001"


def test_query_by_shot_type():
    path = make_catalog([
        {"id": "a", "shot_type": "arrival", "tags": [], "source": "ai",
         "file": "x.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
        {"id": "b", "shot_type": "outdoor", "tags": [], "source": "ai",
         "file": "y.mp4", "style_preset": "outdoor", "mood": "sunny",
         "likeness": False, "duration_sec": 4.0, "prompt": "", "generated_at": ""},
    ])
    cat = Catalog(path)
    arrivals = cat.query(shot_type="arrival")
    assert len(arrivals) == 1
    assert arrivals[0]["id"] == "a"


def test_query_by_tags():
    path = make_catalog([
        {"id": "a", "shot_type": "arrival", "tags": ["gym", "red-wraps"], "source": "ai",
         "file": "x.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
        {"id": "b", "shot_type": "arrival", "tags": ["gym"], "source": "ai",
         "file": "y.mp4", "style_preset": "gym", "mood": "cinematic",
         "likeness": True, "duration_sec": 5.0, "prompt": "", "generated_at": ""},
    ])
    cat = Catalog(path)
    results = cat.query(tags=["red-wraps"])
    assert len(results) == 1
    assert results[0]["id"] == "a"


def test_persist_to_disk():
    path = make_catalog([])
    cat = Catalog(path)
    entry = AssetEntry(
        id="clip_002", file="ai-assets/training/test.mp4", source="ai",
        shot_type="training", style_preset="gym", mood="intense",
        likeness=True, tags=["training"], duration_sec=6.0,
        prompt="boxing training", generated_at="2026-06-07",
    )
    cat.add(entry)
    # Re-load from disk
    cat2 = Catalog(path)
    assert len(cat2.all()) == 1
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd content-generation
pip install -r requirements.txt
pytest test_catalog.py -v
```

Expected: ImportError — `catalog` module not found.

- [ ] **Step 4: Write catalog.py**

`content-generation/catalog.py`:
```python
import json
import os
import uuid
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class AssetEntry:
    file: str
    source: str          # "ai" or "real"
    shot_type: str       # "arrival" | "training" | "atmosphere" | "outdoor" | "hero"
    style_preset: str    # "gym" | "outdoor"
    mood: str
    likeness: bool
    tags: list[str]
    duration_sec: float
    prompt: Optional[str] = None
    generated_at: Optional[str] = None
    id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]


class Catalog:
    def __init__(self, path: str):
        self.path = path
        self._entries: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return json.load(f)

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._entries, f, indent=2)

    def all(self) -> list[dict]:
        return list(self._entries)

    def add(self, entry: AssetEntry):
        self._entries.append(asdict(entry))
        self._save()

    def query(
        self,
        shot_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        likeness: Optional[bool] = None,
        source: Optional[str] = None,
    ) -> list[dict]:
        results = self._entries
        if shot_type:
            results = [e for e in results if e["shot_type"] == shot_type]
        if tags:
            results = [e for e in results if all(t in e["tags"] for t in tags)]
        if likeness is not None:
            results = [e for e in results if e["likeness"] == likeness]
        if source:
            results = [e for e in results if e["source"] == source]
        return results
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest test_catalog.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add content-generation/
git commit -m "feat: add catalog module with query support"
```

---

### Task 7: Generation CLI

**Files:**
- Create: `content-generation/generate.py`

Prerequisites: RunPod endpoint ID and API key from Task 5.

- [ ] **Step 1: Write generate.py**

`content-generation/generate.py`:
```python
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
import urllib.parse
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


def load_brand_style() -> dict:
    with open(BRAND_STYLE_PATH) as f:
        return json.load(f)


def build_prompt(base_prompt: str, shot_type: str) -> str:
    style = load_brand_style()
    preset = SHOT_TYPE_TO_PRESET[shot_type]
    return f"{base_prompt}, {style[preset]}"


def call_runpod(workflow: str, prompt: str, image_path: str | None = None) -> list[str]:
    if not RUNPOD_ENDPOINT or not RUNPOD_API_KEY:
        raise EnvironmentError("Set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY env vars")

    payload = {"input": {"workflow": workflow, "prompt": prompt}}
    if image_path:
        payload["input"]["image_path"] = image_path

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.runpod.io/v2/{RUNPOD_ENDPOINT}/runsync",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())

    return result["output"]["output_files"]


def download_file(remote_path: str, local_path: str):
    """Copy output file from RunPod worker to local path via RunPod Files API."""
    filename = os.path.basename(remote_path)
    url = f"https://api.runpod.io/v2/{RUNPOD_ENDPOINT}/files/{filename}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    )
    with urllib.request.urlopen(req) as resp, open(local_path, "wb") as out:
        out.write(resp.read())


def generate_atmosphere(args):
    prompt = build_prompt(args.prompt, args.shot_type)
    print(f"Generating atmosphere clip: {prompt}")
    output_files = call_runpod("generate_video", prompt)
    return output_files, None


def generate_likeness(args):
    # Step 1: generate still
    still_prompt = build_prompt(args.prompt, args.shot_type)
    print(f"Generating still: {still_prompt}")
    still_files = call_runpod("generate_still", still_prompt)
    still_path = still_files[0]

    # Step 2: animate still
    clip_prompt = f"cinematic motion, smooth camera movement, {still_prompt}"
    print(f"Animating still to clip...")
    clip_files = call_runpod("generate_clip", clip_prompt, still_path)
    return clip_files, still_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["atmosphere", "likeness"])
    parser.add_argument("--shot_type", required=True,
                        choices=["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"])
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--tags", nargs="+", default=[])
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--mood", default="cinematic")
    args = parser.parse_args()

    if args.mode == "atmosphere":
        output_files, _ = generate_atmosphere(args)
        likeness = False
    else:
        output_files, _ = generate_likeness(args)
        likeness = True

    folder = SHOT_TYPE_TO_FOLDER[args.shot_type]
    for remote_path in output_files:
        ext = os.path.splitext(remote_path)[1]
        filename = f"{args.shot_type}_{int(time.time())}{ext}"
        local_rel = f"ai-assets/{folder}/{filename}"
        local_abs = os.path.join(ASSETS_DIR, folder, filename)

        print(f"Downloading {remote_path} → {local_abs}")
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
        print(f"Added to catalog: {entry.id} → {local_rel}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test a real atmosphere generation**

```bash
cd content-generation
export RUNPOD_ENDPOINT_ID=<your_endpoint_id>
export RUNPOD_API_KEY=<your_api_key>
python generate.py atmosphere \
  --shot_type atmosphere \
  --prompt "empty boxing gym, red heavy bag, dramatic shadows" \
  --tags gym atmosphere red-bag \
  --duration 5
```

Expected: clip downloaded to `content-bank/ai-assets/atmosphere/`, entry added to `catalog.json`.

- [ ] **Step 3: Verify catalog entry**

```bash
python -c "from catalog import Catalog; c = Catalog('../content-bank/catalog.json'); print(c.all())"
```

Expected: one entry printed with correct shot_type, tags, file path.

- [ ] **Step 4: Commit**

```bash
git add content-generation/generate.py
git commit -m "feat: add generation CLI with catalog integration"
```

---

### Task 8: Initial Content Bank Batch

This task is a guided generation session — no new code. Run this after Task 7 is working.

- [ ] **Step 1: Run the batch**

Run each command and wait for completion before the next. Generates ~15 clips across all shot types.

```bash
cd content-generation
export RUNPOD_ENDPOINT_ID=<id>
export RUNPOD_API_KEY=<key>

# Arrivals (3 clips — likeness mode)
python generate.py likeness --shot_type arrival --prompt "MATTEO walking through gym door, red boxing hand wraps" --tags gym entrance red-wraps --mood cinematic
python generate.py likeness --shot_type arrival --prompt "MATTEO entering dark locker room, fighter energy" --tags locker-room arrival moody --mood cinematic
python generate.py likeness --shot_type arrival --prompt "MATTEO walking up steps toward boxing ring, low angle" --tags ring arrival dramatic --mood cinematic

# Training (3 clips — likeness mode)
python generate.py likeness --shot_type training --prompt "MATTEO hitting red heavy bag, red boxing hand wraps, cinematic sweat" --tags training bag red-bag --mood intense
python generate.py likeness --shot_type training --prompt "MATTEO shadowboxing in empty gym, dramatic back lighting" --tags training shadowboxing --mood intense
python generate.py likeness --shot_type training --prompt "MATTEO wrapping hands with red boxing wraps, close shot" --tags training wrapping red-wraps --mood focused

# Atmosphere (3 clips — atmosphere mode, no likeness)
python generate.py atmosphere --shot_type atmosphere --prompt "empty boxing gym at night, red heavy bag, dramatic shadows, cinematic" --tags gym atmosphere empty night --mood moody
python generate.py atmosphere --shot_type atmosphere --prompt "close up red boxing gloves on rope, dark gym, dramatic lighting" --tags equipment gloves atmosphere --mood moody
python generate.py atmosphere --shot_type atmosphere --prompt "sweat drops on heavy bag, extreme close up, dark moody gym" --tags detail bag sweat --mood intense

# Outdoor (2 clips — atmosphere mode)
python generate.py atmosphere --shot_type outdoor --prompt "fighter walking down sunny city street, warm golden light, candid energy" --tags outdoor city sunny --mood warm
python generate.py atmosphere --shot_type outdoor --prompt "fighter sitting on steps in warm afternoon sun, relaxed post-training energy" --tags outdoor relaxed sunny post-training --mood warm

# Lifestyle (2 clips — likeness mode)
python generate.py likeness --shot_type lifestyle --prompt "MATTEO working on laptop at cafe table, focused energy, natural ambient light" --tags lifestyle laptop cafe focus --mood focused
python generate.py likeness --shot_type lifestyle --prompt "MATTEO writing in notebook at table, coffee nearby, natural window light, fighter mindset" --tags lifestyle notebook coffee focus --mood focused

# Hero shots (3 clips — likeness mode)
python generate.py likeness --shot_type hero --prompt "MATTEO intense close up face, dark gym background, dramatic lighting" --tags hero intense portrait --mood dramatic
python generate.py likeness --shot_type hero --prompt "MATTEO standing in gym doorway backlit, silhouette energy" --tags hero silhouette backlit --mood cinematic
python generate.py likeness --shot_type hero --prompt "MATTEO looking at camera in dark gym, confident fighter energy" --tags hero confidence portrait --mood cinematic
```

- [ ] **Step 2: Verify library**

```bash
python -c "
from catalog import Catalog
c = Catalog('../content-bank/catalog.json')
entries = c.all()
print(f'Total assets: {len(entries)}')
for e in entries:
    print(f\"  [{e['shot_type']}] {e['file']} (likeness={e['likeness']})\")
"
```

Expected: 15 entries, files exist on disk.

---

## Phase 5 — Remotion Compilation

### Task 9: Remotion Project Setup

**Files:**
- Create: `production/remotion/package.json`
- Create: `production/remotion/remotion.config.ts`
- Create: `production/remotion/src/Root.tsx`

- [ ] **Step 1: Initialize Remotion project**

```bash
mkdir -p production/remotion/src/compositions production/remotion/src/components production/remotion/src/lib
cd production/remotion
npm init -y
npm install remotion @remotion/cli react react-dom @types/react @types/react-dom typescript
```

- [ ] **Step 2: Create remotion.config.ts**

`production/remotion/remotion.config.ts`:
```typescript
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setCodec("h264");
Config.setOverwriteOutput(true);
```

- [ ] **Step 3: Create src/Root.tsx**

`production/remotion/src/Root.tsx`:
```tsx
import { Composition } from "remotion";
import { ReelComposition } from "./compositions/ReelComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Reel"
      component={ReelComposition}
      durationInFrames={450}  // 15s at 30fps — override per reel
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        clips: [],
        overlayItems: [],
        hookText: "",
      }}
    />
  );
};
```

- [ ] **Step 4: Update package.json scripts**

Add to `production/remotion/package.json`:
```json
{
  "scripts": {
    "preview": "remotion preview src/Root.tsx",
    "render": "remotion render src/Root.tsx Reel out/reel.mp4",
    "studio": "remotion studio src/Root.tsx"
  }
}
```

- [ ] **Step 5: Commit**

```bash
cd ../..
git add production/remotion/
git commit -m "feat: initialize Remotion project for reel compilation"
```

---

### Task 10: Remotion Components

**Files:**
- Create: `production/remotion/src/lib/catalog.ts`
- Create: `production/remotion/src/components/VideoClip.tsx`
- Create: `production/remotion/src/components/TextOverlay.tsx`
- Create: `production/remotion/src/compositions/ReelComposition.tsx`

- [ ] **Step 1: Create catalog.ts (reads catalog.json)**

`production/remotion/src/lib/catalog.ts`:
```typescript
import catalogData from "../../../content-bank/catalog.json";

export interface AssetEntry {
  id: string;
  file: string;
  source: "ai" | "real";
  shot_type: "arrival" | "training" | "atmosphere" | "outdoor" | "lifestyle" | "hero";
  style_preset: "gym" | "outdoor";
  mood: string;
  likeness: boolean;
  tags: string[];
  duration_sec: number;
  prompt?: string;
  generated_at?: string;
}

export const catalog: AssetEntry[] = catalogData as AssetEntry[];

export function queryByType(shot_type: string): AssetEntry[] {
  return catalog.filter((e) => e.shot_type === shot_type);
}

export function queryByTags(tags: string[]): AssetEntry[] {
  return catalog.filter((e) => tags.every((t) => e.tags.includes(t)));
}

export function assetPath(entry: AssetEntry): string {
  // Resolves relative path from catalog to absolute path for Remotion
  return `../../../content-bank/${entry.file}`;
}
```

- [ ] **Step 2: Create VideoClip.tsx**

`production/remotion/src/components/VideoClip.tsx`:
```tsx
import { Video, staticFile } from "remotion";
import type { AssetEntry } from "../lib/catalog";

interface VideoClipProps {
  entry: AssetEntry;
  startFrom?: number;
}

export const VideoClip: React.FC<VideoClipProps> = ({ entry, startFrom = 0 }) => {
  return (
    <Video
      src={staticFile(entry.file)}
      startFrom={startFrom}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  );
};
```

- [ ] **Step 3: Create TextOverlay.tsx**

`production/remotion/src/components/TextOverlay.tsx`:
```tsx
import { interpolate, useCurrentFrame } from "remotion";

interface TextOverlayProps {
  text: string;
  position?: "top" | "center" | "bottom";
  isHook?: boolean;
}

export const TextOverlay: React.FC<TextOverlayProps> = ({
  text,
  position = "center",
  isHook = false,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  const positionStyle: React.CSSProperties = {
    top: position === "top" ? 80 : position === "center" ? "40%" : undefined,
    bottom: position === "bottom" ? 120 : undefined,
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        padding: "0 40px",
        textAlign: "center",
        opacity,
        ...positionStyle,
      }}
    >
      <span
        style={{
          fontFamily: "Arial Black, sans-serif",
          fontWeight: 900,
          fontSize: isHook ? 72 : 52,
          color: "#FFFFFF",
          textTransform: "uppercase",
          letterSpacing: 2,
          textShadow: "0 4px 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)",
          lineHeight: 1.1,
          display: "block",
        }}
      >
        {text}
      </span>
    </div>
  );
};
```

- [ ] **Step 4: Create ReelComposition.tsx**

`production/remotion/src/compositions/ReelComposition.tsx`:
```tsx
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { VideoClip } from "../components/VideoClip";
import { TextOverlay } from "../components/TextOverlay";
import type { AssetEntry } from "../lib/catalog";

export interface OverlayItem {
  text: string;
  position: "top" | "center" | "bottom";
  isHook?: boolean;
}

export interface ReelProps {
  // Each clip entry paired with its start frame and duration
  clips: Array<{
    entry: AssetEntry;
    durationInFrames: number;
  }>;
  overlayItems: Array<{
    text: string;
    startFrame: number;
    durationInFrames: number;
    position: "top" | "center" | "bottom";
    isHook?: boolean;
  }>;
  hookText: string;
}

export const ReelComposition: React.FC<ReelProps> = ({
  clips,
  overlayItems,
  hookText,
}) => {
  const { fps } = useVideoConfig();

  // Build clip sequence with cumulative start frames
  let cursor = 0;
  const sequencedClips = clips.map((c) => {
    const start = cursor;
    cursor += c.durationInFrames;
    return { ...c, startFrame: start };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Video clips */}
      {sequencedClips.map((c, i) => (
        <Sequence
          key={i}
          from={c.startFrame}
          durationInFrames={c.durationInFrames}
        >
          <AbsoluteFill>
            <VideoClip entry={c.entry} />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Text overlays */}
      {overlayItems.map((item, i) => (
        <Sequence
          key={`overlay-${i}`}
          from={item.startFrame}
          durationInFrames={item.durationInFrames}
        >
          <AbsoluteFill>
            <TextOverlay
              text={item.text}
              position={item.position}
              isHook={item.isHook}
            />
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 5: Test render**

```bash
cd production/remotion
npm run preview
```

Expected: Remotion Studio opens in browser at localhost:3000. No TypeScript errors.

- [ ] **Step 6: Commit**

```bash
cd ../..
git add production/remotion/src/
git commit -m "feat: add Remotion components for reel compilation"
```

---

### Task 11: First Reel Composition (proof of concept)

This task builds the first real reel using the content bank from Task 8. The composition uses the "training-partner" hook from `content-bank/captions/drafts/2026-06-06-8-ways-to-get-dangerous-without-a-training-partner/`.

**Files:**
- Create: `production/remotion/src/compositions/reels/TrainingPartnerReel.tsx`

- [ ] **Step 1: Create TrainingPartnerReel.tsx**

Claude should read `content-bank/captions/drafts/2026-06-06-8-ways-to-get-dangerous-without-a-training-partner/` and `content-bank/catalog.json`, then write this file selecting real clips with explicit comments. Template:

`production/remotion/src/compositions/reels/TrainingPartnerReel.tsx`:
```tsx
import { ReelComposition } from "../ReelComposition";
import { catalog } from "../../lib/catalog";

// CLIP SELECTION REASONING:
// Opening hook (0-5s): need cinematic arrival to establish gym context
//   → using arrivals/ clip — sets moody gym world before the list
// Items 1-8 (5s each): alternate training and atmosphere clips
//   → training clips for active items, atmosphere for passive/mindset items
// Closing (last 3s): hero shot — end on Matteo's face for identity anchor
// Total: ~45s at 30fps = 1350 frames

const arrivalClips = catalog.filter((e) => e.shot_type === "arrival");
const trainingClips = catalog.filter((e) => e.shot_type === "training");
const atmosphereClips = catalog.filter((e) => e.shot_type === "atmosphere");
const heroClips = catalog.filter((e) => e.shot_type === "hero");

const FRAMES_PER_CLIP = 150; // 5s at 30fps

export const TrainingPartnerReel: React.FC = () => (
  <ReelComposition
    clips={[
      { entry: arrivalClips[0], durationInFrames: FRAMES_PER_CLIP },      // hook clip
      { entry: trainingClips[0], durationInFrames: FRAMES_PER_CLIP },     // item 1-2
      { entry: atmosphereClips[0], durationInFrames: FRAMES_PER_CLIP },   // item 3-4
      { entry: trainingClips[1], durationInFrames: FRAMES_PER_CLIP },     // item 5-6
      { entry: atmosphereClips[1], durationInFrames: FRAMES_PER_CLIP },   // item 7-8
      { entry: heroClips[0], durationInFrames: 90 },                      // closing
    ]}
    hookText="8 WAYS TO GET DANGEROUS WITHOUT A TRAINING PARTNER"
    overlayItems={[
      { text: "8 WAYS TO GET DANGEROUS WITHOUT A TRAINING PARTNER", startFrame: 10, durationInFrames: 140, position: "top", isHook: true },
      { text: "1. SHADOWBOX LIKE IT'S REAL", startFrame: 160, durationInFrames: 140, position: "center" },
      { text: "2. DRILL UNTIL IT'S AUTOMATIC", startFrame: 310, durationInFrames: 140, position: "center" },
      { text: "3. FILM YOURSELF. BE YOUR OWN COACH", startFrame: 460, durationInFrames: 140, position: "center" },
      { text: "4. THE BAG NEVER TAKES A DAY OFF", startFrame: 610, durationInFrames: 140, position: "center" },
      { text: "5. STUDY FIGHTS LIKE OPPONENTS STUDY YOU", startFrame: 760, durationInFrames: 140, position: "center" },
      { text: "6. CONDITION WITHOUT MERCY", startFrame: 910, durationInFrames: 140, position: "center" },
      { text: "7. BUILD REFLEXES WITH SOLO DRILLS", startFrame: 1060, durationInFrames: 140, position: "center" },
      { text: "8. MENTAL REPS COUNT TOO", startFrame: 1210, durationInFrames: 90, position: "center" },
      { text: "READ DESCRIPTION ⬇️", startFrame: 1160, durationInFrames: 100, position: "bottom" },
    ]}
  />
);
```

- [ ] **Step 2: Register in Root.tsx**

Add `TrainingPartnerReel` as a composition in `production/remotion/src/Root.tsx`:
```tsx
import { Composition } from "remotion";
import { ReelComposition } from "./compositions/ReelComposition";
import { TrainingPartnerReel } from "./compositions/reels/TrainingPartnerReel";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Reel"
      component={ReelComposition}
      durationInFrames={450}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ clips: [], overlayItems: [], hookText: "" }}
    />
    <Composition
      id="TrainingPartnerReel"
      component={TrainingPartnerReel}
      durationInFrames={1350}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{}}
    />
  </>
);
```

- [ ] **Step 3: Preview and render**

```bash
cd production/remotion
npm run preview
# Open localhost:3000, select TrainingPartnerReel, scrub through to verify clips appear
npm run render -- --composition TrainingPartnerReel --output out/training-partner-reel.mp4
```

Expected: `out/training-partner-reel.mp4` created, clips sequence correctly with text overlays.

- [ ] **Step 4: Commit**

```bash
cd ../..
git add production/remotion/src/compositions/reels/
git commit -m "feat: first Remotion reel composition (training-partner hook)"
```

---

## Phase 6 — Jarvis MCP Studio

### Task 12: MCP Server Setup

**Files:**
- Create: `jarvis/mcp-studio/package.json`
- Create: `jarvis/mcp-studio/src/index.ts`
- Create: `jarvis/mcp-studio/tsconfig.json`

- [ ] **Step 1: Create package.json**

`jarvis/mcp-studio/package.json`:
```json
{
  "name": "mcp-studio",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "tsx": "^4.0.0",
    "@types/node": "^20.0.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

`jarvis/mcp-studio/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create src/index.ts**

`jarvis/mcp-studio/src/index.ts`:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerGenerateAsset } from "./tools/generate_asset.js";
import { registerBrowseAssets } from "./tools/browse_assets.js";
import { registerCompileReel } from "./tools/compile_reel.js";

const server = new McpServer({ name: "studio", version: "1.0.0" });

registerGenerateAsset(server);
registerBrowseAssets(server);
registerCompileReel(server);

const transport = new StdioServerTransport();
await server.connect(transport);
```

- [ ] **Step 4: Install and verify build**

```bash
cd jarvis/mcp-studio
npm install
npm run build
```

Expected: `dist/index.js` created, no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
cd ../..
git add jarvis/mcp-studio/
git commit -m "feat: scaffold Jarvis Studio MCP server"
```

---

### Task 13: MCP Tools

**Files:**
- Create: `jarvis/mcp-studio/src/tools/generate_asset.ts`
- Create: `jarvis/mcp-studio/src/tools/browse_assets.ts`
- Create: `jarvis/mcp-studio/src/tools/compile_reel.ts`

- [ ] **Step 1: Create generate_asset.ts**

`jarvis/mcp-studio/src/tools/generate_asset.ts`:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { execSync } from "child_process";
import path from "path";

const REPO_ROOT = path.resolve("../../..");
const GENERATE_SCRIPT = path.join(REPO_ROOT, "content-generation/generate.py");

export function registerGenerateAsset(server: McpServer) {
  server.tool(
    "generate_asset",
    "Generate an AI video clip and add it to the content bank catalog.",
    {
      mode: z.enum(["atmosphere", "likeness"]).describe(
        "atmosphere: text-to-video, no face needed. likeness: generates Matteo's face via LoRA."
      ),
      shot_type: z.enum(["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"]),
      prompt: z.string().describe(
        "Base prompt. For likeness mode, start with MATTEO. Brand style preset is appended automatically."
      ),
      tags: z.array(z.string()).default([]),
      duration: z.number().default(5.0),
      mood: z.string().default("cinematic"),
    },
    async ({ mode, shot_type, prompt, tags, duration, mood }) => {
      const tagStr = tags.join(" ");
      const cmd = [
        `python "${GENERATE_SCRIPT}"`,
        mode,
        `--shot_type ${shot_type}`,
        `--prompt "${prompt}"`,
        `--tags ${tagStr}`,
        `--duration ${duration}`,
        `--mood ${mood}`,
      ].join(" ");

      try {
        const output = execSync(cmd, {
          env: { ...process.env },
          encoding: "utf-8",
          timeout: 300_000,
        });
        return { content: [{ type: "text", text: output }] };
      } catch (err: any) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
  );
}
```

- [ ] **Step 2: Create browse_assets.ts**

`jarvis/mcp-studio/src/tools/browse_assets.ts`:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readFileSync } from "fs";
import path from "path";

const CATALOG_PATH = path.resolve("../../../content-bank/catalog.json");

export function registerBrowseAssets(server: McpServer) {
  server.tool(
    "browse_assets",
    "Query the content bank catalog to find available clips.",
    {
      shot_type: z.enum(["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"]).optional(),
      tags: z.array(z.string()).optional(),
      likeness: z.boolean().optional(),
      source: z.enum(["ai", "real"]).optional(),
    },
    async ({ shot_type, tags, likeness, source }) => {
      const catalog: any[] = JSON.parse(readFileSync(CATALOG_PATH, "utf-8"));

      let results = catalog;
      if (shot_type) results = results.filter((e) => e.shot_type === shot_type);
      if (tags?.length) results = results.filter((e) => tags.every((t) => e.tags.includes(t)));
      if (likeness !== undefined) results = results.filter((e) => e.likeness === likeness);
      if (source) results = results.filter((e) => e.source === source);

      const summary = results.map((e) =>
        `${e.id} | ${e.shot_type} | ${e.file} | tags: ${e.tags.join(", ")} | likeness: ${e.likeness}`
      ).join("\n");

      return {
        content: [{ type: "text", text: `Found ${results.length} assets:\n\n${summary}` }],
      };
    }
  );
}
```

- [ ] **Step 3: Create compile_reel.ts**

`jarvis/mcp-studio/src/tools/compile_reel.ts`:
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readFileSync, writeFileSync } from "fs";
import path from "path";
import { execSync } from "child_process";

const CATALOG_PATH = path.resolve("../../../content-bank/catalog.json");
const REMOTION_DIR = path.resolve("../../../production/remotion");
const COMPOSITIONS_DIR = path.join(REMOTION_DIR, "src/compositions/reels");

export function registerCompileReel(server: McpServer) {
  server.tool(
    "compile_reel",
    "Generate a Remotion composition file for a reel. Claude picks clips with visible reasoning in code comments, then renders to MP4.",
    {
      reel_name: z.string().describe("Slug for the reel file, e.g. training-partner-v2"),
      hook_text: z.string().describe("ALL CAPS hook text shown at start of reel"),
      list_items: z.array(z.string()).describe("The numbered list items as ALL CAPS text"),
      render: z.boolean().default(false).describe("If true, runs npm run render after writing composition"),
    },
    async ({ reel_name, hook_text, list_items, render }) => {
      const catalog: any[] = JSON.parse(readFileSync(CATALOG_PATH, "utf-8"));

      const arrivals = catalog.filter((e) => e.shot_type === "arrival");
      const training = catalog.filter((e) => e.shot_type === "training");
      const atmosphere = catalog.filter((e) => e.shot_type === "atmosphere");
      const hero = catalog.filter((e) => e.shot_type === "hero");

      if (!arrivals.length || !training.length) {
        return {
          content: [{ type: "text", text: "Not enough clips in catalog. Run generate_asset first." }],
          isError: true,
        };
      }

      const FRAMES = 150; // 5s at 30fps
      const itemCount = list_items.length;
      const totalFrames = FRAMES + (itemCount * FRAMES) + 90; // hook + items + outro

      // Build clip sequence: arrival → alternate training/atmosphere → hero
      const clipPool = [...training, ...atmosphere];
      const selectedClips = [arrivals[0], ...clipPool.slice(0, itemCount), hero[0] || arrivals[0]];

      // Build clip entries string
      const clipEntries = selectedClips.map((c, i) => {
        const reason = i === 0
          ? "opening hook — cinematic arrival sets gym world"
          : i === selectedClips.length - 1
          ? "closing hero shot — ends on face for identity anchor"
          : `item ${i} visual — ${c.shot_type} clip`;
        return `      // ${reason}\n      { entry: catalog.find(e => e.id === "${c.id}")!, durationInFrames: ${i === selectedClips.length - 1 ? 90 : FRAMES} },`;
      }).join("\n");

      // Build overlay entries string
      let cursor = 10;
      const overlayEntries = [
        `      { text: "${hook_text}", startFrame: 10, durationInFrames: ${FRAMES - 10}, position: "top", isHook: true },`,
        ...list_items.map((item, i) => {
          const start = FRAMES + (i * FRAMES) + 10;
          return `      { text: "${item}", startFrame: ${start}, durationInFrames: ${FRAMES - 10}, position: "center" },`;
        }),
        `      { text: "READ DESCRIPTION ⬇️", startFrame: ${totalFrames - 100}, durationInFrames: 90, position: "bottom" },`,
      ].join("\n");

      const componentName = reel_name
        .split("-")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join("");

      const composition = `import { ReelComposition } from "../ReelComposition";
import { catalog } from "../../lib/catalog";

// REEL: ${hook_text}
// Generated by Jarvis Studio MCP
// Total duration: ${totalFrames} frames (${(totalFrames / 30).toFixed(1)}s at 30fps)

export const ${componentName}: React.FC = () => (
  <ReelComposition
    clips={[
${clipEntries}
    ]}
    hookText={"${hook_text}"}
    overlayItems={[
${overlayEntries}
    ]}
  />
);
`;

      const outPath = path.join(COMPOSITIONS_DIR, `${reel_name}.tsx`);
      writeFileSync(outPath, composition, "utf-8");

      let renderOutput = "";
      if (render) {
        renderOutput = execSync(
          `npm run render -- --composition ${componentName} --output out/${reel_name}.mp4`,
          { cwd: REMOTION_DIR, encoding: "utf-8", timeout: 300_000 }
        );
      }

      return {
        content: [{
          type: "text",
          text: `Composition written to ${outPath}\n\nRun: cd production/remotion && npm run render -- --composition ${componentName} --output out/${reel_name}.mp4\n\n${renderOutput}`,
        }],
      };
    }
  );
}
```

- [ ] **Step 4: Rebuild and verify**

```bash
cd jarvis/mcp-studio
npm run build
```

Expected: `dist/` built with no TypeScript errors.

- [ ] **Step 5: Register MCP server in Claude settings**

Add to `.claude/settings.json` under `mcpServers`:
```json
{
  "mcpServers": {
    "studio": {
      "command": "node",
      "args": ["jarvis/mcp-studio/dist/index.js"],
      "cwd": "/absolute/path/to/@matteofights"
    }
  }
}
```

- [ ] **Step 6: Test tools in Claude**

In a new Claude session, verify the MCP tools are available:
- `browse_assets({})` → should return all catalog entries
- `generate_asset({ mode: "atmosphere", shot_type: "atmosphere", prompt: "dark gym test" })` → should generate one clip
- `compile_reel({ reel_name: "test-reel", hook_text: "TEST HOOK", list_items: ["ITEM ONE", "ITEM TWO"] })` → should write a .tsx file

- [ ] **Step 7: Commit**

```bash
cd ../..
git add jarvis/mcp-studio/src/tools/ jarvis/mcp-studio/src/index.ts
git commit -m "feat: add Jarvis Studio MCP tools (generate_asset, browse_assets, compile_reel)"
```

---

## Post-Build Notes

- **LoRA retraining:** Run `train_lora.py` again if Matteo's appearance changes significantly (haircut, weight change). ~$1–2 per retrain on Replicate.
- **Budget monitoring:** Check RunPod dashboard weekly. 22.5 CHF/month target. Cold-start workers don't charge idle time.
- **Content bank maintenance:** Run batch generation monthly or when a new shot type is needed. Each session adds to the permanent library.
- **Remotion upgrades:** Each new reel gets its own `.tsx` in `src/compositions/reels/`. Old ones stay — they're reusable.
