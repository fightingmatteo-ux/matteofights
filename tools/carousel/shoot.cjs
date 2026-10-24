// Screenshot every .slide of a carousel page to JPEG, and optionally record the cover as a looping MP4.
//   node tools/carousel/shoot.cjs PAGE.html OUTDIR PREFIX [--animate SECONDS]
// The cover video: slide 1 next to slide 2 on one track; CSS animations are paused and stepped frame by frame
// (deterministic, no dropped frames), the track eases left twice to peek at slide 2, frames piped to ffmpeg.
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { pathToFileURL } = require("node:url");
const path = require("node:path");

(async () => {

const [page_, outdir, prefix, flag, secs] = process.argv.slice(2);
const FPS = 30, W = 1080, H = 1350, PEEKS = [1.4, 3.0], PEEK_PX = 150;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(page_)).href);
await page.evaluate(() => document.fonts.ready);
const slides = await page.$$(".slide:not(.peek-copy)");
for (let i = 0; i < slides.length; i++) {
  await page.evaluate(() => document.getAnimations().forEach((a) => { a.pause(); a.currentTime = 0; }));
  await slides[i].screenshot({ path: path.join(outdir, `${prefix}-${String(i + 1).padStart(2, "0")}.jpg`), type: "jpeg", quality: 92 });
}

if (flag === "--animate") {
  const seconds = Number(secs || 4.5);
  await page.evaluate(() => document.body.classList.add("recording"));
  const track = await page.$("#track");
  const ease = (t) => 0.5 - 0.5 * Math.cos(Math.PI * Math.max(0, Math.min(1, t)));
  const peek = (t) => Math.max(0, ...PEEKS.map((p) => (t >= p && t <= p + 1.1 ? Math.sin(Math.PI * ease((t - p) / 1.1)) : 0)));
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", path.join(outdir, `${prefix}-01.mp4`)],
    { stdio: ["pipe", "inherit", "inherit"] });
  const n = Math.round(FPS * seconds);
  for (let i = 0; i < n; i++) {
    const t = i / FPS;
    await page.evaluate(([ms, dx]) => {
      document.getAnimations().forEach((a) => { a.pause(); a.currentTime = ms; });
      document.getElementById("track").style.transform = `translateX(${-dx}px)`;
    }, [t * 1000, PEEK_PX * peek(t)]);
    const buf = await page.screenshot({ type: "jpeg", quality: 95, clip: { x: 0, y: 0, width: W, height: H } });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on("close", (c) => (c ? j(new Error("ffmpeg " + c)) : r())));
  void track;
}
await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
