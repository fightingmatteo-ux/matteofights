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
import argparse, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "production" / "listicles" / "hooks.json"
BEBAS = Path(__file__).parent / "fonts" / "BebasNeue-Regular.ttf"
EMOJI = Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
MUSIC = sorted((ROOT / "production/reels/five-signs-real-fighter/assets/music").glob("*.mp3"))
W, H, FPS = 1080, 1920, 30
RED, WHITE, BLACK = (232, 17, 45), (255, 255, 255), (11, 11, 13)
# Instagram's grid crop keeps y 285-1635; the UI covers the bottom ~320 px. Text stays inside both.
TOP, BOTTOM, TEXT_W, PAD = 300, 1600, 940, 40
LOOP_X = 0.5      # seconds of end -> start crossfade
ZOOM = 0.045      # peak push-in (4.5%), mid-reel


# ---------------------------------------------------------------- probing + clip window
def ff(args):
    return subprocess.run(["ffprobe", "-v", "error", *args], capture_output=True, text=True).stdout.strip()


def probe(clip, entry):
    out = ff(["-select_streams", "v:0", "-show_entries", entry, "-of", "csv=p=0", str(clip)])
    return out.split(",")[0] if out else ""


def has_audio(clip):
    return bool(ff(["-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(clip)]))


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


def place_plate(row_motion, height):
    """Top of the hook plate: the upper slot unless the fighter's movement sits there and the lower slot is
    clearly quieter. Both slots stay inside Instagram's grid crop (y 285-1635) and above its UI."""
    def load(y0):
        r0, r1 = int(y0 / H * len(row_motion)), int((y0 + height) / H * len(row_motion)) + 1
        return sum(row_motion[r0:r1])
    top, low = TOP, BOTTOM - height
    return low if load(low) < 0.7 * load(top) else top


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


def hook_layer(hook, subhook, top=TOP):
    """One black plate: red hook, then the white subhook. Padding measured on cap height, so it's even."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fh, hl = fit(d, hook.upper(), 4, 144)
    size = 62  # one sentence per line when it fits at a readable size, else balanced wrap
    while size > 56 and max(d.textlength(s.upper(), font=ImageFont.truetype(str(BEBAS), size)) for s in subhook) > TEXT_W:
        size -= 2
    fs = ImageFont.truetype(str(BEBAS), size)
    sl = [l for s in subhook for l in fit(d, s.upper(), 2, size, TEXT_W)[1]]

    hc, sc = cap_h(fh), cap_h(fs)
    h_step, s_step = round(hc * 1.22), round(sc * 1.55)
    rule_gap = round(hc * 0.55)
    width = max([d.textlength(l, font=fh) for l in hl] + [d.textlength(l, font=fs) for l in sl]) + 2 * PAD
    y = top + PAD + hc                          # first hook baseline
    h_last = y + h_step * (len(hl) - 1)
    rule_y = h_last + rule_gap
    s_first = rule_y + rule_gap + sc
    bottom = s_first + s_step * (len(sl) - 1) + PAD
    x0, x1 = (W - width) / 2, (W + width) / 2
    d.rectangle([x0, top, x1, bottom], fill=BLACK)
    for i, l in enumerate(hl):
        d.text((W / 2, y + i * h_step), l, font=fh, fill=RED, anchor="ms")
    d.rectangle([W / 2 - 60, rule_y - 2, W / 2 + 60, rule_y + 2], fill=RED)   # thin divider
    for i, l in enumerate(sl):
        d.text((W / 2, s_first + i * s_step), l, font=fs, fill=WHITE, anchor="ms")
    return img, bottom


def cta_layer(base=1440):
    """READ CAPTION pill; `base` = text baseline (low by default, high when the hook plate sits low)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(BEBAS), 88)
    label = "READ CAPTION"
    tw, em, gap = d.textlength(label, font=f), 76, 18
    c = cap_h(f)
    x0 = (W - tw - gap - em) / 2
    d.rectangle([x0 - 34, base - c - 30, x0 + tw + gap + em + 34, base + 30], fill=BLACK)
    d.text((x0, base), label, font=f, fill=WHITE, anchor="ls")
    ey = base - c + (c - em) // 2
    try:  # Noto Color Emoji only renders at its bitmap size (109); scale it down
        e = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), "⬇️", font=ImageFont.truetype(str(EMOJI), 109), embedded_color=True)
        e = e.crop(e.getbbox()).resize((em, em), Image.LANCZOS)
        img.alpha_composite(e, (int(x0 + tw + gap), int(ey)))
    except OSError:  # no emoji font: plain red arrow
        cx = x0 + tw + gap + em / 2
        d.polygon([(cx - 34, ey + 36), (cx + 34, ey + 36), (cx, ey + em)], fill=RED)
        d.rectangle([cx - 12, ey, cx + 12, ey + 38], fill=RED)
    return img


# ---------------------------------------------------------------- render
TURN = {0: "", 90: "transpose=1,", -90: "transpose=2,", 180: "hflip,vflip,"}


def render(clip, hook_id, out, seconds=8.0, cover=None, music_i=0, rotate=0):
    """rotate: extra clockwise turn for phone clips saved sideways without rotation metadata (90, -90, 180)."""
    hooks = {h["id"]: h for h in json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]}
    h = hooks[hook_id]
    dur = float(ff(["-show_entries", "format=duration", "-of", "csv=p=0", str(clip)]) or 0)
    S = min(seconds, max(1.0, dur - LOOP_X)) if dur else seconds
    X = min(LOOP_X, S / 4)
    turn = TURN[rotate]
    start, row_motion = best_window(clip, dur, S + X, turn)
    cta_in, cta_out = max(0.0, S - 3.4), S - 0.35

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

    with tempfile.TemporaryDirectory() as tmp:
        hp, cp = Path(tmp, "hook.png"), Path(tmp, "cta.png")
        _, bottom = hook_layer(h["hook"], h["subhook"])
        top = place_plate(row_motion, bottom - TOP)
        hook_layer(h["hook"], h["subhook"], top)[0].save(hp)
        cta_layer(1440 if top == TOP else top - 60).save(cp)  # low plate: pill sits just above it
        print(f"plate {'top' if top == TOP else 'low'} (y {top})", flush=True)
        # music_i=None: no music bed - the trending sound gets added in the Instagram app
        music = MUSIC[music_i % len(MUSIC)] if MUSIC and music_i is not None else None
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{S + X:.3f}", "-i", str(clip),
               "-loop", "1", "-framerate", str(FPS), "-i", str(hp),
               "-loop", "1", "-framerate", str(FPS), "-i", str(cp)]
        vf = (
            # footage: colour-correct, fill 9:16, 30 fps, a touch darker so red text reads on it
            f"[0:v]{turn}{tm}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS},"
            f"eq=brightness=-0.06:saturation=0.92,format=yuv420p,setpts=PTS-STARTPTS,split[s1][s2];"
            # seamless loop: body = [X, S+X); its tail crossfades into the window's first X seconds
            f"[s1]trim=start={X:.3f}:duration={S:.3f},setpts=PTS-STARTPTS[body];"
            f"[s2]trim=start=0:duration={X:.3f},setpts=PTS-STARTPTS[head];"
            f"[body][head]xfade=transition=fade:duration={X:.3f}:offset={S - X:.3f},{zoom},format=yuv420p[bg];"
            f"[1:v]format=rgba,trim=duration={S:.3f}[hook];"
            f"[2:v]format=rgba,trim=duration={S:.3f},fade=t=in:st={cta_in:.2f}:d=0.4:alpha=1,"
            f"fade=t=out:st={cta_out:.2f}:d=0.3:alpha=1[cta];"
            f"[bg][hook]overlay=0:0[a];"
            f"[a][cta]overlay=x=0:y='{rise}':eval=frame,format=yuv420p[v]")
        af = None
        if music:
            cmd += ["-i", str(music)]
            if has_audio(clip):  # music on top, the gym sound (bag, breathing) underneath
                af = (f"[3:a]volume=0.9[m];[0:a]atrim=start={X:.3f},asetpts=PTS-STARTPTS,volume=0.35[g];"
                      f"[m][g]amix=inputs=2:duration=first:normalize=0,")
            else:
                af = "[3:a]"
        elif has_audio(clip):
            af = f"[0:a]atrim=start={X:.3f},asetpts=PTS-STARTPTS,"
        fc, amap = vf, []
        if af:
            fc += ";" + af + (f"atrim=0:{S:.3f},afade=t=in:d=0.08,afade=t=out:st={max(0, S - 0.5):.3f}:d=0.5,"
                              f"loudnorm=I=-14:TP=-1.5,aresample=48000[au]")
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


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("clip"); p.add_argument("hook_id"); p.add_argument("out")
    p.add_argument("--cover"); p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--music", type=int, default=0, help="index into the music tracks")
    p.add_argument("--rotate", type=int, default=0, choices=sorted(TURN), help="clockwise fix for sideways clips")
    a = p.parse_args()
    print(render(a.clip, a.hook_id, a.out, a.seconds, a.cover, a.music, a.rotate))
