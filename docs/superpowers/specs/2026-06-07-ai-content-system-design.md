# AI Content System — Design Spec

_@matteofights. Written 2026-06-07._

## Overview

A self-hosted AI video generation pipeline that produces cinematic B-roll clips matching Matteo's likeness and brand aesthetic. Budget: 22.5 CHF/month for RunPod Serverless hosting. Clips feed a permanent asset library; Claude compiles them into reels via Remotion with visible reasoning. Integrated into Jarvis as a "Studio" panel.

---

## Architecture (4 layers)

```
[RunPod Serverless + ComfyUI] → [Asset Library] → [Remotion Compilation] → [Jarvis Studio]
```

1. **Generation** — ComfyUI on RunPod Serverless. Two workflows: FLUX.1-dev + Matteo LoRA → still, then Wan2.1 animates still → clip. Non-likeness shots use Wan2.1 text-to-video directly.
2. **Asset Library** — `content-bank/ai-assets/` with `catalog.json` indexing all AI and real footage.
3. **Compilation** — Remotion writes React compositions. Claude picks clips with explicit reasoning, adds text overlays, outputs MP4 via `npm run render`.
4. **Jarvis Integration** — MCP server exposing three tools: `generate_asset`, `browse_assets`, `compile_reel`.

---

## Generation Layer

### LoRA Training (one-time, ~$1–2)
- **Training data**: Extract frames from Matteo's reference videos. Target 25–35 curated images — diverse angles (front, 3/4, side), diverse lighting, no motion blur, no other prominent people. `content-bank/reels/` already contains ~26 usable frame JPGs from viral reels as a starting point; longer reference videos will supplement these.
- **Location**: `content-bank/brand/reference-photos/`
- **Platform**: Replicate (cheapest for one-off FLUX LoRA training jobs)
- **Output**: `.safetensors` file uploaded to ComfyUI worker

### RunPod Serverless Worker
Docker container with: ComfyUI + FLUX.1-dev + Matteo LoRA + Wan2.1

Two endpoints:
- `POST /generate-still` — FLUX + LoRA → photorealistic still (likeness mode)
- `POST /generate-clip` — Wan2.1 → 4–6 second MP4 (from still or from text prompt)

**Cost**: ~$0.0002–0.0004/sec on A100. At 22.5 CHF: ~1,500–2,000 video clips/month.

### Two Generation Modes

| Mode | Pipeline | When to use |
|---|---|---|
| Likeness | FLUX + LoRA → still → Wan2.1 animate | Shots where it's recognisably Matteo |
| Atmosphere | Wan2.1 text-to-video | Gym environment, equipment, outdoor scenes |

### Brand Style Presets (`content-bank/brand/brand_style.json`)

```json
{
  "gym": "dark moody gym, red boxing hand wraps, red heavy bag, dramatic shadows, cinematic lighting",
  "outdoor": "natural sunlight, warm tones, outdoor environment, fighter lifestyle, candid energy",
  "lifestyle": "natural ambient light, laptop or coffee visible, focused energy, fighter mindset, candid indoor or outdoor setting"
}
```

Claude always prepends the correct preset to generation prompts. Gym preset applies to `arrivals/`, `training/`, `atmosphere/`. Outdoor preset applies to `outdoor/`. Lifestyle preset applies to `lifestyle/`. Hero shots use either gym or outdoor based on context.

### Initial Content Bank Sprint
Once the worker is live, Claude runs a batch generation session: ~40–50 clips across all shot categories. This is the permanent reusable library — clips are re-cut and re-combined across many reels.

---

## Asset Library

### Folder Structure

```
content-bank/
  ai-assets/
    arrivals/         gym entrance, locker room, ring walk
    training/         bag work, pad work, conditioning, footwork
    atmosphere/       gym environment, equipment, red bag details, empty gym
    outdoor/          sunny lifestyle — streets, parks, warm light, post-session
    lifestyle/        laptop work, cafe, focus, planning shots — fighter who thinks
    hero-shots/       dramatic singles, poster energy, intense close-ups
    stills/           FLUX images pre-animation (intermediate, not final clips)
  real-footage/
    training/
    talking-head/
    events/
  reels/              (existing — top performers already here, with extracted frames)
  captions/           (existing — caption drafts already here)
  brand/
    brand_style.json
    reference-photos/
  catalog.json
```

### Catalog Schema (`catalog.json`)

```json
[
  {
    "id": "clip_001",
    "file": "ai-assets/arrivals/gym-entrance-001.mp4",
    "source": "ai",
    "shot_type": "arrival",
    "style_preset": "gym",
    "mood": "cinematic",
    "likeness": true,
    "tags": ["gym", "entrance", "red-wraps", "moody"],
    "duration_sec": 5,
    "prompt": "...",
    "generated_at": "2026-06-07"
  }
]
```

Real footage entries use `"source": "real"` and omit `prompt`/`generated_at`.

---

## Remotion Compilation Layer

### How it works
1. Claude receives a reel brief (hook, list items, target duration)
2. Claude queries `catalog.json` for matching clips — reasoning is visible in code comments
3. For missing shot types: Claude generates them before compiling
4. Claude writes a Remotion composition (`production/remotion/src/compositions/[reel-name].tsx`)
5. Composition includes: clip sequence, text overlays matching the proven format, timing
6. User runs `npm run render` → MP4 output

### Composition structure
- Opening hook clip (3–5s)
- List item clips (2–4s each, text overlay per item)
- Closing CTA clip
- `READ DESCRIPTION ⬇️` text overlay near end
- Audio track note in composition (user adds audio in CapCut or final edit)

---

## Jarvis Integration

### Studio Panel (new tab in dashboard)
Three Claude-callable MCP tools:

| Tool | Args | Action |
|---|---|---|
| `generate_asset` | `prompt, shot_type, style_preset, likeness` | Calls RunPod, downloads clip, updates catalog |
| `browse_assets` | `shot_type, tags, likeness` | Queries catalog, returns matching clips |
| `compile_reel` | `brief, hook, format` | Writes Remotion composition, picks clips with visible reasoning |

### Visible reasoning
When compiling, Claude explains clip selection in the composition code comments:
```tsx
// Opening: need cinematic arrival to establish gym context
// catalog has clip_003 (arrivals/gym-entrance-001.mp4, 5s, moody) — using this
// No outdoor lifestyle clip exists for item 4 — generating now before continuing
```

---

## Build Phases

### Phase 1 — Foundation (do first)
- Create folder structure
- Set up `catalog.json` with real footage entries
- Extract + curate reference photos from Matteo's videos

### Phase 2 — Generation
- Train FLUX LoRA on Replicate
- Build + deploy ComfyUI Docker worker to RunPod Serverless
- Run initial content bank batch (40–50 clips)
- Populate catalog

### Phase 3 — Compilation
- Set up Remotion in `production/remotion/`
- Build first reel composition from existing hooks in `content-bank/captions/drafts/`

### Phase 4 — Jarvis Studio
- Build MCP server wrapping RunPod API + catalog
- Add Studio panel to dashboard
- Wire `generate_asset`, `browse_assets`, `compile_reel` tools

---

## Constraints

- Never post to Instagram without explicit confirmation in conversation
- Gym shots always use `gym` style preset — no bright/clean gym aesthetic
- LoRA retrain if Matteo's appearance changes significantly (haircut, weight change, etc.)
- Budget ceiling: 22.5 CHF/month. Track RunPod usage; don't leave worker idle.
