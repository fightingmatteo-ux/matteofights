"""Footage agent: Claude looks at the training clips and picks / checks the background for each reel.

Three jobs, all with vision on small contact sheets (never full videos):
  catalog()  every clip in the Drive folder gets a description once (what's happening, framing, orientation,
             quality), cached in production/listicles/clips.json. New clips Matteo drops in are picked up on
             the next run; clips removed from Drive drop out of the candidate list.
  match()    for a hook + caption, rank the best-fitting clips out of the WHOLE catalog.
  review()   after rendering, look at the finished reel (cover frame + mid + end) and pass/fail it.

The factory renders the top match, reviews it, and moves to the next candidate if the review fails.
Needs ANTHROPIC_API_KEY (repo secret). Without it the factory falls back to least-used-clip picking.
"""
import base64, json, os, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "production" / "listicles" / "clips.json"
MODEL = "claude-opus-5-5"
TILE_W, TILE_H = 320, 568            # 9:16 tiles, 3x2 sheet = 960x1136


def enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _client():
    import anthropic
    return anthropic.Anthropic()


def ask(content, schema, effort="medium"):
    """One structured-output call. Fallbacks on: a safety decline re-runs on Anthropic's recommended model."""
    import anthropic
    try:
        r = _client().beta.messages.create(
            model=MODEL, max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": content}])
    except anthropic.RateLimitError as e:
        raise RuntimeError(f"rate limited, retry after {e.response.headers.get('retry-after', '?')}s") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Claude API {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError("Claude API unreachable") from e
    if r.stop_reason == "refusal":
        raise RuntimeError(f"declined: {getattr(r.stop_details, 'category', None)}")
    if r.stop_reason == "max_tokens":
        raise RuntimeError("ran out of tokens")
    return json.loads(next(b.text for b in r.content if b.type == "text"))


def _img(path):
    data = base64.standard_b64encode(Path(path).read_bytes()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}}


def _duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def sheet(video, times, out, label=True):
    """Frames at `times` (s), each fitted into a 9:16 tile on black, 3 per row, numbered."""
    from PIL import ImageDraw
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for k, t in enumerate(times):
            f = Path(tmp, f"{k}.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale={TILE_W}:{TILE_H}:force_original_aspect_ratio=decrease,"
                                   f"pad={TILE_W}:{TILE_H}:(ow-iw)/2:(oh-ih)/2", "-q:v", "4", str(f)], check=True)
            im = Image.open(f).convert("RGB")
            if label:
                ImageDraw.Draw(im).text((8, 6), f"{k + 1} @ {t:.1f}s", fill=(255, 255, 0))
            tiles.append(im)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    o = Image.new("RGB", (TILE_W * cols, TILE_H * rows))
    for k, im in enumerate(tiles):
        o.paste(im, (TILE_W * (k % cols), TILE_H * (k // cols)))
    o.save(out, quality=82)
    return out


# ---------------------------------------------------------------- catalog
CLIP_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["description", "activity", "setting", "fighter_visible", "face_visible", "rotate_fix",
                 "quality", "energy", "mood", "usable", "problems"],
    "properties": {
        "description": {"type": "string", "description": "One or two plain sentences: who is doing what, where."},
        "activity": {"type": "string", "enum": ["bag work", "pad work", "sparring", "shadowboxing", "footwork drills",
                                                 "skipping", "running", "strength", "fight", "walking/resting",
                                                 "no training", "other"]},
        "setting": {"type": "string", "description": "e.g. commercial gym, Muay Thai ring, rooftop at sunset"},
        "fighter_visible": {"type": "string", "enum": ["full body", "most of body", "partial", "not visible"]},
        "face_visible": {"type": "boolean"},
        "rotate_fix": {"type": "integer", "enum": [0, 90, -90, 180],
                       "description": "Clockwise degrees needed to make the frames upright (0 if already upright)."},
        "quality": {"type": "integer",
                    "description": "1-5: how good this looks as background for a viral reel (light, framing, stability)."},
        "energy": {"type": "integer", "description": "1-5: how intense the training looks"},
        "mood": {"type": "string", "description": "a few words, e.g. gritty, calm, cinematic sunset, intense"},
        "usable": {"type": "boolean", "description": "False if mostly floor/feet, empty frame, phone handling, "
                                                     "blurry, or no training."},
        "problems": {"type": "array", "items": {"type": "string"}},
    },
}


def describe_clip(path):
    d = _duration(path)
    lo, hi = min(1.0, d * 0.1), max(d - 1.0, d * 0.9)
    times = [lo + (hi - lo) * k / 5 for k in range(6)]
    with tempfile.TemporaryDirectory() as tmp:
        s = sheet(path, times, Path(tmp, "s.jpg"))
        info = ask([_img(s), {"type": "text", "text":
            "These 6 frames come from one phone clip of a fighter (Matteo) training, in time order. "
            "It may become the silent background of an Instagram reel with a text hook on top. "
            "Describe the clip for a footage library."}], CLIP_SCHEMA, effort="low")
    info["duration"] = round(d, 1)
    return info


def catalog(clips, fetch):
    """clips: Drive listing [{ID, Name, ...}]; fetch(clip) -> local path (deleted afterwards if it's a temp copy)."""
    cat = json.loads(CATALOG.read_text(encoding="utf-8")) if CATALOG.exists() else {}
    for c in clips:
        if c["ID"] in cat:
            continue
        path, temp = fetch(c)
        try:
            info = describe_clip(path)
        except Exception as e:  # one bad clip must not stop the batch
            print(f"catalog: {c['Name']}: {e}", flush=True)
            continue
        finally:
            if temp:
                Path(path).unlink(missing_ok=True)
        cat[c["ID"]] = {"name": c["Name"], **info}
        CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"catalog: {c['Name']}: {info['activity']}, {info['fighter_visible']}, q{info['quality']}"
              f"{'' if info['usable'] else ' (unusable)'}", flush=True)
    return cat


# ---------------------------------------------------------------- match
MATCH_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["ranked"],
    "properties": {"ranked": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "why"],
        "properties": {"id": {"type": "string"}, "why": {"type": "string"}}}}},
}


def match(hook, caption, cat, live_ids, uses, avoid=(), n=4):
    """Best-fitting clips for this hook out of every usable clip currently in the Drive folder."""
    pool = {k: v for k, v in cat.items() if k in live_ids and v.get("usable") and k not in avoid}
    if not pool:
        return []
    lines = [f'{k} | {v["name"]} | {v["activity"]} | {v["setting"]} | fighter {v["fighter_visible"]}, '
             f'face {"yes" if v["face_visible"] else "no"} | quality {v["quality"]}/5, energy {v["energy"]}/5 | '
             f'{v["mood"]} | used {uses.get(k, 0)}x | {v["description"]}' for k, v in pool.items()]
    out = ask([{"type": "text", "text":
        f"Pick background footage for an Instagram reel by a fighter.\n\n"
        f"On-screen hook: {hook}\n\nCaption:\n{caption}\n\n"
        f"Clip library (id | file | activity | setting | framing | scores | mood | times already used | "
        f"description):\n" + "\n".join(lines) + "\n\n"
        f"Rank the {n} clips that best match what the hook says, best first. The footage should show the thing "
        f"the hook is about (sparring for a sparring hook, a lone run or rooftop session for discipline / "
        f"starting late, pads or bag for power), with the fighter clearly in frame. Prefer higher quality and "
        f"clips used less often; never pick a clip just because it's pretty if it doesn't fit the words. "
        f"Use ids exactly as given."}], MATCH_SCHEMA, effort="medium")
    return [r for r in out["ranked"] if r["id"] in pool][:n]


# ---------------------------------------------------------------- review
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["passed", "score", "fit", "issues"],
    "properties": {
        "passed": {"type": "boolean"},
        "score": {"type": "integer", "description": "1-10"},
        "fit": {"type": "string", "description": "One sentence: how well the footage matches the hook."},
        "issues": {"type": "array", "items": {"type": "string"}},
    },
}


def review(video, hook):
    d = _duration(video)
    times = [0.5, d * 0.3, d * 0.5, d * 0.7, max(0.5, d - 0.6)]
    with tempfile.TemporaryDirectory() as tmp:
        s = sheet(video, times, Path(tmp, "r.jpg"))
        return ask([_img(s), {"type": "text", "text":
            f"These are frames from a finished Instagram reel (frame 1 at 0.5 s is the cover). The red text is "
            f"the hook: \"{hook}\". Review the background footage. Fail it if any of these is true: the fighter "
            f"isn't clearly visible in the cover frame; the hook text covers the fighter's face or upper body; "
            f"the footage is sideways or upside down; frames show the floor, an empty space, or someone handling "
            f"the phone; the footage doesn't fit what the hook is about. Score 1-10 for how well it would work "
            f"as this reel's background."}], REVIEW_SCHEMA, effort="medium")
