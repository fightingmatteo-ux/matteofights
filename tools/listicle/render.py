"""Render one listicle reel in the proven old format: training clip + red ALL-CAPS hook + subhook,
"READ CAPTION" near the end. No talking, no edit decisions: headless, so the daily factory can run it.

    python -P tools/listicle/render.py <clip> <hook id> <out.mp4> [--cover cover.jpg] [--seconds 8]

Smoothness rules (from Matteo's feedback on earlier reels):
- Frame 0 already shows the hook (it is the thumbnail); the hook never animates.
- The clip window is picked by motion: the busiest steady stretch, never the walk to/from the phone.
- Seamless loop: the end crossfades into the window's own start, and the slow push-in returns to 1.0x
  with zero velocity at both ends, so the replay has no jump.
- Push-in uses the perspective filter (sub-pixel, cubic) - zoompan/scale zooms snap to whole pixels and jitter.
- READ CAPTION eases in (rise + fade) and fades out before the loop point; no hard pops.
Colour handling matches production/editing/reel-kit/scripts/prep_footage.sh (HDR -> SDR, full -> tv range, neutral).
"""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
BEBAS = Path(__file__).parent / "fonts" / "BebasNeue-Regular.ttf"
SERIF = Path(__file__).parent / "fonts" / "LiberationSerif-Bold.ttf"  # Times-metric, like IG's Classic
EMOJI = Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
INTER = Path(__file__).parent / "fonts" / "Inter-Bold.otf"  # the typewriter tease, like IG's own white text
ANTON = ROOT / "production/reels/five-signs-real-fighter/assets/fonts/Anton-Regular.ttf"
# Hook text looks (hooks.json "style" per hook, else production/listicles/look.json "hook_style", else "native"):
#   native  the 331k / 161k look: Instagram's own text style, red bold serif on black highlights
#   poster  brand: Bebas Neue, white caps on a red block per line (fight-poster)
#   anton   brand-heavy: Anton, red caps on black highlights (the native layout in a condensed display face)
#   split   Bebas Neue on black highlights, white, with the last line in red
HOOK_STYLES = {
    "native": {"font": SERIF, "fg": "RED", "bg": "BLACK", "start": 112, "width": 900},
    "poster": {"font": BEBAS, "fg": "WHITE", "bg": "RED", "start": 132, "width": 820},
    "anton": {"font": ANTON, "fg": "RED", "bg": "BLACK", "start": 108, "width": 820},
    "split": {"font": BEBAS, "fg": "WHITE", "bg": "BLACK", "start": 132, "width": 820, "last": "RED"},
}
LOOK = ROOT / "production" / "listicles" / "look.json"


def hook_style(h):
    if h.get("style") in HOOK_STYLES:
        return h["style"]
    look = json.loads(LOOK.read_text(encoding="utf-8")) if LOOK.exists() else {}
    return look.get("hook_style", "native") if look.get("hook_style") in HOOK_STYLES else "native"


def protocol_cta(h):
    """True when this reel ends on the COMMENT PROTOCOL pill (comment-to-DM, signup-site/functions/api/ig-webhook.js).
    hooks.json "cta" ("protocol" | "read") wins, else look.json "protocol_cta" = share of reels (0-1), picked
    stably per hook id so a re-render keeps its pill. iykyk reels have no pill at all."""
    if h.get("format") in ("iykyk", "builder"):  # nothing to send people to / not the Protocol's audience
        return False
    if h.get("cta") in ("protocol", "read"):
        return h["cta"] == "protocol"
    look = json.loads(LOOK.read_text(encoding="utf-8")) if LOOK.exists() else {}
    share = float(look.get("protocol_cta", 0))
    return int(hashlib.md5(h["id"].encode()).hexdigest(), 16) % 100 < share * 100
# Music library: production/listicles/music/ (tracks.json = title, artist, vibe, license) once it has tracks,
# else the original 4 tracks. Each reel uses the track's strongest stretch (its drop), cut on a beat.
MUSIC_DIR = ROOT / "production" / "listicles" / "music"
MUSIC = sorted(MUSIC_DIR.glob("*.mp3")) or sorted((ROOT / "production/reels/five-signs-real-fighter/assets/music").glob("*.mp3"))
# Coach-graded moments per clip (Claude's daily check grades the moment sheets the factory makes):
# {clip_id: {"good": [start s, best first], "bad": [start s], "graded": iso}}
MOMENTS = ROOT / "production" / "listicles" / "moments.json"
GYM_LEVEL = 0.18   # gym sound (bag, breathing) under the music
W, H, FPS = 1080, 1920, 30
RED, WHITE, BLACK = (227, 27, 35), (255, 255, 255), (8, 8, 10)
# Instagram's grid crop keeps y 285-1635; the UI covers the bottom ~320 px. Text stays inside both.
TOP, BOTTOM, TEXT_W, PAD = 300, 1600, 940, 40
LOOP_X = 0.5      # seconds of end -> start crossfade
LAYOUT = {}       # where the last render() put the hook plate: {"top", "bottom"} (offsite() fits the cards around it)
ZOOM = 0.045      # peak push-in (4.5%), mid-reel


# ---------------------------------------------------------------- probing + clip window
def ff(args):
    return subprocess.run(["ffprobe", "-v", "error", *args], capture_output=True, text=True).stdout.strip()


def probe(clip, entry):
    out = ff(["-select_streams", "v:0", "-show_entries", entry, "-of", "csv=p=0", str(clip)])
    return out.split(",")[0] if out else ""


def has_audio(clip):
    return bool(ff(["-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(clip)]))


def _motion(clip, turn, w=36, h=64, rate=5):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-vf",
                          f"{turn}fps={rate},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    n = w * h
    frames = [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]
    return [[abs(a - b) for a, b in zip(f1, f2)] for f1, f2 in zip(frames, frames[1:])]


def candidate_windows(clip, dur, length, turn="", k=6):
    """Up to k non-overlapping `length`-second stretches with real movement, busiest first. Movement alone can't
    tell skill from messing around; the moment sheet lets Claude grade these like a coach (moments.json)."""
    rate = 5
    pix = _motion(clip, turn, rate=rate)
    if len(pix) < 3 or dur <= length + 2:
        return [max(0.0, (dur - length) / 2)]
    diff = [sum(p) / len(p) for p in pix]
    cap = sorted(diff)[int(len(diff) * 0.9)]
    diff = [min(d, cap) - (d - cap) * 2 if d > cap else d for d in diff]
    win = max(1, int(length * rate))
    lo, hi = int(1.0 * rate), len(diff) - win - int(1.0 * rate)
    if hi <= lo:
        return [max(0.0, (dur - length) / 2)]
    score = {i: sum(diff[i:i + win]) for i in range(lo, hi + 1, max(1, rate // 2))}
    picked = []
    for i in sorted(score, key=score.get, reverse=True):
        if all(abs(i - j) >= win for j in picked):
            picked.append(i)
        if len(picked) == k:
            break
    return [round(i / rate, 1) for i in picked]


def graded_start(clip, dur, length):
    """The best coach-graded moment of this clip that fits, or None (then the busiest stretch is used)."""
    cid = Path(clip).stem
    g = (json.loads(MOMENTS.read_text(encoding="utf-8")) if MOMENTS.exists() else {}).get(cid) or {}
    for t in g.get("good") or []:
        if 0 <= t <= max(0.0, dur - length):
            return float(t)
    # not graded yet: the best moment that passed the pose check (moment-sheets/pose.json), if any
    idx, pose = (ROOT / "production/listicles/moment-sheets" / n for n in ("index.json", "pose.json"))
    if idx.exists() and pose.exists():
        starts = json.loads(idx.read_text(encoding="utf-8")).get(cid) or {}
        scores = json.loads(pose.read_text(encoding="utf-8")).get(cid) or {}
        bad = set(g.get("bad") or [])
        ok = [(p.get("score") or 0, starts[k]) for k, p in scores.items()
              if k in starts and not p.get("veto") and starts[k] not in bad and 0 <= starts[k] <= max(0.0, dur - length)]
        if ok:
            return float(max(ok)[1])
    return None


def best_window(clip, dur, length, turn=""):
    """(start time, row motion) of the most active, steady `length`-second stretch.

    Row motion = how much movement each of 64 horizontal bands of the OUTPUT frame has in that window;
    the layout uses it to keep the text off the fighter.

    Motion = mean frame difference on a tiny greyscale copy at 5 fps. Whole-frame jolts (phone picked up,
    someone walking past the lens) are clipped so they can't win; the first/last second is avoided."""
    w, h, rate = 36, 64, 5
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-vf",
                          f"{turn}fps={rate},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    n = w * h
    frames = [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]
    if len(frames) < 3:
        return max(0.0, (dur - length) / 2), [1.0] * h
    pix = [[abs(a - b) for a, b in zip(f1, f2)] for f1, f2 in zip(frames, frames[1:])]
    diff = [sum(p) / n for p in pix]

    def rows(i0, i1):
        return [sum(sum(p[r * w:(r + 1) * w]) for p in pix[i0:i1]) for r in range(h)]

    if dur <= length + 2:
        return max(0.0, (dur - length) / 2), rows(0, len(pix))
    cap = sorted(diff)[int(len(diff) * 0.9)]           # 90th percentile = ceiling for "normal" action
    diff = [min(d, cap) - (d - cap) * 2 if d > cap else d for d in diff]  # punish jolts above it
    win = max(1, int(length * rate))
    lo, hi = int(1.0 * rate), len(diff) - win - int(1.0 * rate)
    if hi <= lo:
        return max(0.0, (dur - length) / 2), rows(0, len(pix))
    best = max(range(lo, hi + 1), key=lambda i: sum(diff[i:i + win]))
    return best / rate, rows(best, best + win)


def music_start(track, length):
    """Start of the track's strongest `length`-second stretch (the drop / hook, not the intro), snapped to the
    loudest onset near it so the loop starts on a beat. Energy = RMS per 50 ms of a mono 8 kHz decode."""
    sr, hop = 8000, 400
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(track), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True).stdout
    import array
    a = array.array("h", raw)
    rms = [(sum(x * x for x in a[i:i + hop]) / hop) ** 0.5 for i in range(0, len(a) - hop, hop)]
    if len(rms) * hop / sr <= length + 4:
        return 0.0
    win = int(length * sr / hop)
    lo = int(4 * sr / hop)                                   # never the first 4 s (intro)
    hi = len(rms) - win - int(2 * sr / hop)
    if hi <= lo:
        return 0.0
    run = sum(rms[lo:lo + win])
    best, best_i = run, lo
    for i in range(lo + 1, hi):
        run += rms[i + win - 1] - rms[i - 1]
        if run > best:
            best, best_i = run, i
    onset = [max(0.0, rms[i] - rms[i - 1]) for i in range(1, len(rms))]
    near = range(max(1, best_i - 10), min(len(onset), best_i + 10))  # +-0.5 s
    j = max(near, key=lambda i: onset[i - 1])
    return round(j * hop / sr, 3)


def place_plate(row_motion, height):
    """Top of the hook plate: the upper slot unless the fighter's movement sits there and the lower slot is
    clearly quieter. Both slots stay inside Instagram's grid crop (y 285-1635) and above its UI."""
    def load(y0):
        r0, r1 = int(y0 / H * len(row_motion)), int((y0 + height) / H * len(row_motion)) + 1
        return sum(row_motion[r0:r1])
    top, low = TOP, BOTTOM - height
    return low if load(low) < 0.7 * load(top) else top


PROTOCOL_LINE = "Comment PROTOCOL and I'll DM you my free training plan for fighters."


def protocol_caption(h, caption):
    """Every listicle caption (not iykyk/builder) gets the PROTOCOL comment line, above the hashtags."""
    if h.get("format") in ("iykyk", "builder") or "PROTOCOL" in caption:
        return caption
    lines = caption.rstrip().split("\n")
    i = len(lines)
    while i > 0 and (lines[i - 1].startswith("#") or not lines[i - 1].strip()):
        i -= 1
    return "\n".join(lines[:i] + ["", PROTOCOL_LINE] + lines[i:])


# ---------------------------------------------------------------- text layers
def wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


def fit(draw, text, max_lines, size, width=TEXT_W):
    while True:
        f = ImageFont.truetype(str(BEBAS), size)
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= width for l in lines):
            break
        size -= 4
    # Balance: narrow the box while the line count holds, so no word sits alone on the last line.
    w = width
    while w > 300 and len(wrap(draw, text, f, w - 10)) == len(lines):
        w -= 10
    return f, wrap(draw, text, f, w)


def cap_h(font):
    b = font.getbbox("H")
    return b[3] - b[1]


def hook_layer(hook, top=TOP, style="native"):
    """Each line on its own rounded highlight hugging the text, centred (HOOK_STYLES picks font + colours;
    "native" = Instagram's own text style, the 331k / 161k look). Only the hook is on screen; the subhook
    lives in the caption."""
    st = HOOK_STYLES.get(style, HOOK_STYLES["native"])
    col = {"RED": RED, "WHITE": WHITE, "BLACK": BLACK}
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    words = hook.upper()
    size = st["start"]
    while True:  # biggest size that fits in 3 lines (4 for long hooks) inside ~84% of the width
        f = ImageFont.truetype(str(st["font"]), size)
        lines = fit_lines(d, words, f, st["width"])
        if len(lines) <= (3 if len(words) < 44 else 4):
            break
        size -= 4
    c = cap_h(f)
    step, px, py, r = round(c * 1.5), 28, round(c * 0.36), 18  # highlights overlap into one shape
    y = top + py + c
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        b = y + i * step
        d.rounded_rectangle([(W - tw) / 2 - px, b - c - py, (W + tw) / 2 + px, b + py + 6], r, fill=col[st["bg"]])
    for i, l in enumerate(lines):
        fg = col[st["last"]] if st.get("last") and i == len(lines) - 1 else col[st["fg"]]
        d.text((W / 2, y + i * step), l, font=f, fill=fg, anchor="ms")
    return img, y + (len(lines) - 1) * step + py + 6


def fit_lines(draw, text, font, width):
    """Wrap, then narrow the box while the line count holds, so lines come out balanced."""
    lines = wrap(draw, text, font, width)
    w = width
    while w > 300 and len(wrap(draw, text, font, w - 10)) == len(lines):
        w -= 10
    return wrap(draw, text, font, w)


def cta_layer(base=1440, label="READ DESCRIPTION", red="", emoji="⬇️"):
    """CTA pill: white `label`, then `red` in brand red, then `emoji`. Default READ DESCRIPTION ⬇️; the protocol
    version is COMMENT + red PROTOCOL + 🥊. `base` = text baseline (low by default, high when the hook plate sits low)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(BEBAS), 88)
    sp = d.textlength(" ", font=f) if red else 0
    lw, rw = d.textlength(label, font=f), d.textlength(red, font=f) if red else 0
    tw, em, gap = lw + sp + rw, 76, 18
    c = cap_h(f)
    x0 = (W - tw - gap - em) / 2
    d.rounded_rectangle([x0 - 30, base - c - 28, x0 + tw + gap + em + 30, base + 28], 18, fill=BLACK)
    d.text((x0, base), label, font=f, fill=WHITE, anchor="ls")
    if red:
        d.text((x0 + lw + sp, base), red, font=f, fill=RED, anchor="ls")
    ey = base - c + (c - em) // 2
    try:  # Noto Color Emoji only renders at its bitmap size (109); scale it down
        e = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), emoji, font=ImageFont.truetype(str(EMOJI), 109), embedded_color=True)
        e = e.crop(e.getbbox()).resize((em, em), Image.LANCZOS)
        img.alpha_composite(e, (int(x0 + tw + gap), int(ey)))
    except OSError:  # no emoji font: plain red arrow
        cx = x0 + tw + gap + em / 2
        d.polygon([(cx - 34, ey + 36), (cx + 34, ey + 36), (cx, ey + em)], fill=RED)
        d.rectangle([cx - 12, ey, cx + 12, ey + 38], fill=RED)
    return img


def tease_track(text, baseline, tmp, start, end, S, cps=20):
    """The 331k's typewriter subhook ("Every fighter has #6"): white bold text with a soft shadow under the hook
    plate, typed letter by letter from `start`, gone at `end`. Returns an ffconcat file (an RGBA video track)."""
    tmp = Path(tmp)
    blank = tmp / "t_blank.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    if not text:
        return blank, None
    lines = ["ffconcat version 1.0"]
    f = ImageFont.truetype(str(INTER), 62)

    x0 = (W - ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(text, font=f)) / 2  # typing grows rightwards

    def frame(s, i):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x0, baseline + 3), s, font=f, fill=(0, 0, 0, 170), anchor="ls")
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
        ImageDraw.Draw(img).text((x0, baseline), s, font=f, fill=WHITE, anchor="ls")
        out = tmp / f"t_{i:03d}.png"
        img.save(out)
        return out

    step = 1 / cps
    lines += [f"file '{blank}'", f"duration {start:.3f}"]
    for i in range(1, len(text) + 1):
        lines += [f"file '{frame(text[:i], i)}'", f"duration {step:.3f}"]
    hold = max(0.1, end - start - len(text) * step)
    full = tmp / f"t_{len(text):03d}.png"
    lines += [f"file '{full}'", f"duration {hold:.3f}", f"file '{blank}'", f"duration {max(0.1, S - end):.3f}",
              f"file '{blank}'"]
    lst = tmp / "tease.ffconcat"
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return blank, lst


# ---------------------------------------------------------------- render
TURN = {0: "", 90: "transpose=1,", -90: "transpose=2,", 180: "hflip,vflip,"}


def render(clip, hook_id, out, seconds=8.0, cover=None, music_i=0, rotate=0, cta=True):
    """rotate: extra clockwise turn for phone clips saved sideways without rotation metadata (90, -90, 180).
    cta=False: no READ DESCRIPTION pill (offsite() puts the list on screen instead)."""
    hooks = {h["id"]: h for h in json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]}
    h = hooks[hook_id]
    dur = float(ff(["-show_entries", "format=duration", "-of", "csv=p=0", str(clip)]) or 0)
    S = min(seconds, max(1.0, dur - LOOP_X)) if dur else seconds
    X = min(LOOP_X, S / 4)
    turn = TURN[rotate]
    start, row_motion = best_window(clip, dur, S + X, turn)
    graded = h["moment"] if h.get("moment") is not None else graded_start(clip, dur, S + X)  # hook "moment" = manual pick
    if graded is not None:
        start = graded
        pix = _motion(clip, turn)
        i0 = int(start * 5)
        seg = pix[i0:i0 + int((S + X) * 5)] or pix
        row_motion = [sum(sum(p[r * 36:(r + 1) * 36]) for p in seg) for r in range(64)]
        print(f"moment {start:.1f}s (coach-graded)", flush=True)
    # 331k timing: READ pill from ~1 s, the typewriter tease from 1.4 s; protocol reels swap the READ pill for
    # COMMENT PROTOCOL for the last ~2.6 s, after the tease has gone.
    proto = protocol_cta(h) and cta
    cta_in = min(1.0, S / 6)
    cta_out = S - 2.9 if proto else S - 0.35
    p_in, p_out = S - 2.6, S - 0.35
    tz_in, tz_out = min(1.4, S / 5), S - 2.9

    trc, rng = probe(clip, "stream=color_transfer"), probe(clip, "stream=color_range")
    tm = ""
    if trc in ("arib-std-b67", "smpte2084"):
        tm = (f"zscale=t=linear:npl=100:tin={trc}:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,"
              "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,")
    elif rng == "pc":
        tm = "scale=in_range=pc:out_range=tv,"

    N = round(S * FPS)
    a = f"{ZOOM / 2:.4f}*pow(sin(PI*in/{N})\\,2)"   # per-side margin, 0 at both ends -> loop-safe
    zoom = (f"perspective=x0=W*{a}:y0=H*{a}:x1=W-W*{a}:y1=H*{a}:x2=W*{a}:y2=H-H*{a}:x3=W-W*{a}:y3=H-H*{a}"
            f":interpolation=cubic:eval=frame")
    rise = f"if(lt(t\\,{cta_in:.2f})\\,0\\,22*pow(max(0\\,1-(t-{cta_in:.2f})/0.45)\\,3))"
    rise_p = f"if(lt(t\\,{p_in:.2f})\\,0\\,22*pow(max(0\\,1-(t-{p_in:.2f})/0.45)\\,3))"

    with tempfile.TemporaryDirectory() as tmp:
        hp, cp, pp = Path(tmp, "hook.png"), Path(tmp, "cta.png"), Path(tmp, "protocol.png")
        style = hook_style(h)
        _, bottom = hook_layer(h["hook"], style=style)
        top = place_plate(row_motion, bottom - TOP)
        hook_layer(h["hook"], top, style)[0].save(hp)
        print(f"hook style {style}", flush=True)
        LAYOUT.update(top=top, bottom=top + bottom - TOP)
        pill_base = 1300 if top == TOP else top - 60  # low plate: pill sits just above it
        if h.get("format") == "iykyk" or not cta:  # one-line caption / list on screen: nothing to send people to
            Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(cp)
        else:
            cta_layer(pill_base).save(cp)
        (cta_layer(pill_base, "COMMENT", "PROTOCOL", "🥊") if proto else Image.new("RGBA", (W, H), (0, 0, 0, 0))).save(pp)
        # tease under the plate (top slot), or skipped when the plate sits low and there is no room
        tease = (h.get("tease") or "").strip() if cta else ""
        tz_base = top + bottom - TOP + 92
        if top != TOP and tz_base > pill_base - 120 and tz_base > BOTTOM:
            tease = ""
        blank, tz = tease_track(tease, tz_base, tmp, tz_in, tz_out, S)
        print(f"cta {'protocol' if proto else 'read'}, tease {tease!r}", flush=True)
        print(f"plate {'top' if top == TOP else 'low'} (y {top})", flush=True)
        # music_i=None: no music bed - the trending sound gets added in the Instagram app
        music = MUSIC[music_i % len(MUSIC)] if MUSIC and music_i is not None else None
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{S + X:.3f}", "-i", str(clip),
               "-loop", "1", "-framerate", str(FPS), "-i", str(hp),
               "-loop", "1", "-framerate", str(FPS), "-i", str(cp),
               "-loop", "1", "-framerate", str(FPS), "-i", str(pp)]
        cmd += ["-f", "concat", "-safe", "0", "-i", str(tz)] if tz else ["-loop", "1", "-framerate", str(FPS), "-i", str(blank)]
        vf = (
            # footage: colour-correct, fill 9:16, 30 fps, a touch darker so red text reads on it
            f"[0:v]{turn}{tm}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},"
            f"format=yuv420p,setpts=PTS-STARTPTS,split[s1][s2];"
            # seamless loop: body = [X, S+X); its tail crossfades into the window's first X seconds
            f"[s1]trim=start={X:.3f}:duration={S:.3f},setpts=PTS-STARTPTS[body];"
            f"[s2]trim=start=0:duration={X:.3f},setpts=PTS-STARTPTS[head];"
            f"[body][head]xfade=transition=fade:duration={X:.3f}:offset={S - X:.3f},{zoom},format=yuv420p[bg];"
            f"[1:v]format=rgba,trim=duration={S:.3f}[hook];"
            f"[2:v]format=rgba,trim=duration={S:.3f},fade=t=in:st={cta_in:.2f}:d=0.4:alpha=1,"
            f"fade=t=out:st={cta_out:.2f}:d=0.3:alpha=1[cta];"
            f"[3:v]format=rgba,trim=duration={S:.3f},fade=t=in:st={p_in:.2f}:d=0.4:alpha=1,"
            f"fade=t=out:st={p_out:.2f}:d=0.3:alpha=1[pro];"
            f"[4:v]format=rgba,fps={FPS},trim=duration={S:.3f},setpts=PTS-STARTPTS[tz];"
            f"[bg][hook]overlay=0:0[a];"
            f"[a][tz]overlay=0:0[a2];"
            f"[a2][cta]overlay=x=0:y='{rise}':eval=frame[a3];"
            f"[a3][pro]overlay=x=0:y='{rise_p}':eval=frame,format=yuv420p[v]")
        af = None
        if music:
            m0 = music_start(music, S)
            print(f"music {music.name} from {m0:.2f}s", flush=True)
            cmd += ["-ss", f"{m0:.3f}", "-i", str(music)]
            if has_audio(clip):  # music on top, the gym sound (bag, breathing) quietly underneath
                af = (f"[5:a]volume=1.0[m];[0:a]atrim=start={X:.3f},asetpts=PTS-STARTPTS,highpass=f=120,"
                      f"volume={GYM_LEVEL}[g];[m][g]amix=inputs=2:duration=first:normalize=0,")
            else:
                af = "[5:a]"
        elif has_audio(clip):
            af = f"[0:a]atrim=start={X:.3f},asetpts=PTS-STARTPTS,"
        fc, amap = vf, []
        if af:
            fc += ";" + af + (f"atrim=0:{S:.3f},afade=t=in:d=0.03,afade=t=out:st={max(0, S - 0.25):.3f}:d=0.25,"
                              f"loudnorm=I=-15:LRA=9:TP=-1.5,aresample=48000[au]")
            amap = ["-map", "[au]"]
        cmd += ["-filter_complex", fc, "-map", "[v]", *amap, "-t", f"{S:.3f}", "-r", str(FPS),
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-g", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
    if cover:  # frame 0.5 s = the cover Instagram uses (thumb_offset 500)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", str(out), "-frames:v", "1",
                        "-vf", "scale=540:-2", "-q:v", "4", str(cover)], check=True)
    return out


# ---------------------------------------------------------------- offsite version (Facebook)
CARD_BASE, CARD_PER_CHAR, CARD_MAX = 1.2, 0.045, 3.2  # seconds on screen per list card: reading time, capped
HOOK_ALONE = 1.8                                      # the hook plate on its own before the first card


def card_layer(text, tag, zone):
    """One list item (or the closing question) on a black plate, centred in `zone` (y0, y1), with a red
    "3 / 7" tag above it so viewers see how many are left. tag=None: the question, white on red."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f, lines = fit(d, text.upper(), 3, 96, TEXT_W - 140)
    c = cap_h(f)
    step, px, py = round(c * 1.45), 36, round(c * 0.5)
    tf = ImageFont.truetype(str(BEBAS), 64)
    tc = cap_h(tf)
    tag_h = (tc + 36 + 18) if tag else 0
    box_h = (len(lines) - 1) * step + c + 2 * py
    y0 = (zone[0] + zone[1] - box_h - tag_h) / 2
    if tag:
        tw = d.textlength(tag, font=tf)
        d.rounded_rectangle([(W - tw) / 2 - 24, y0, (W + tw) / 2 + 24, y0 + tc + 36], 14, fill=RED)
        d.text((W / 2, y0 + 18 + tc), tag, font=tf, fill=WHITE, anchor="ms")
        y0 += tag_h
    bw = max(d.textlength(l, font=f) for l in lines) + 2 * px
    d.rounded_rectangle([(W - bw) / 2, y0, (W + bw) / 2, y0 + box_h], 20, fill=BLACK if tag else RED)
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + py + c + i * step), l, font=f, fill=WHITE, anchor="ms")
    return img


def offsite(clip, hook_id, out, items, question, music_i=0, rotate=0, seconds=8.0):
    """The Facebook version of a listicle: same clip, hook plate and loop as the Instagram reel, but no READ
    DESCRIPTION (Facebook viewers don't open captions): the list plays on screen one item at a time, then the
    question, over the looping clip, with royalty-free music in the file (Instagram's library sound only exists
    on Instagram). Length = reading time of the cards, about 22-25 s for 7 items."""
    with tempfile.TemporaryDirectory() as tmp:
        bg = Path(tmp, "bg.mp4")
        render(clip, hook_id, bg, seconds, None, None, rotate, cta=False)
        top, bottom = LAYOUT["top"], LAYOUT["bottom"]
        zone = (bottom + 90, BOTTOM) if top == TOP else (TOP, top - 60)  # the half the hook plate leaves free
        cards, t = [], HOOK_ALONE
        texts = [(x, f"{k + 1} / {len(items)}") for k, x in enumerate(items)] + [(question, None)]
        for k, (text, tag) in enumerate(texts):
            dur = min(CARD_MAX, CARD_BASE + CARD_PER_CHAR * len(text))
            png = Path(tmp, f"card{k}.png")
            card_layer(text, tag, zone).save(png)
            cards.append((png, t, t + dur))
            t += dur
        T = t + 0.3
        track = MUSIC[music_i % len(MUSIC)]
        m0 = music_start(track, T)
        print(f"offsite: {len(items)} cards, {T:.1f}s, music {track.name} from {m0:.2f}s", flush=True)
        cmd = ["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", str(bg)]
        for png, _, _ in cards:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{T:.3f}", "-i", str(png)]
        cmd += ["-ss", f"{m0:.3f}", "-i", str(track)]
        fc, last = [f"[0:v]trim=duration={T:.3f},setpts=PTS-STARTPTS[v0]"], "v0"
        for k, (_, a, b) in enumerate(cards, 1):
            fc.append(f"[{k}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.2:alpha=1,fade=t=out:st={b - 0.2:.2f}:d=0.2:alpha=1[c{k}]")
            fc.append(f"[{last}][c{k}]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{k}]")
            last = f"v{k}"
        fc.append(f"[{last}]format=yuv420p[v]")
        fc.append(f"[{len(cards) + 1}:a]atrim=0:{T:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,"
                  f"afade=t=out:st={max(0, T - 1.0):.3f}:d=1.0,loudnorm=I=-15:LRA=9:TP=-1.5,aresample=48000[au]")
        cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[au]", "-t", f"{T:.3f}", "-r", str(FPS),
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-g", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("clip"); p.add_argument("hook_id"); p.add_argument("out")
    p.add_argument("--cover"); p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--music", type=int, default=0, help="index into the music tracks")
    p.add_argument("--rotate", type=int, default=0, choices=sorted(TURN), help="clockwise fix for sideways clips")
    a = p.parse_args()
    print(render(a.clip, a.hook_id, a.out, a.seconds, a.cover, a.music, a.rotate))
