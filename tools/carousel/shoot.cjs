// Screenshot every .slide of a carousel page to JPEG, and optionally record the cover as a looping MP4.
//   node tools/carousel/shoot.cjs PAGE.html OUTDIR PREFIX [--animate SECONDS]
// Recording is deterministic: every frame, CSS animations are paused at t and every <video> is seeked to t (mod its
// length), then the cover is screenshotted and piped to ffmpeg. No real-time capture, so no dropped frames.
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { pathToFileURL } = require("node:url");
const path = require("node:path");

const [page_, outdir, prefix, flag, secs] = process.argv.slice(2);
const FPS = 30;

const seekAll = (page, t) => page.evaluate(async (t) => {
  document.getAnimations().forEach((a) => { a.pause(); a.currentTime = t * 1000; });
  await Promise.all([...document.querySelectorAll("video")].map((v) => new Promise((ok) => {
    const target = v.duration ? t % v.duration : 0;
    if (Math.abs(v.currentTime - target) < 1e-3 && v.readyState >= 2) return ok();
    v.addEventListener("seeked", ok, { once: true });
    v.currentTime = target;
  })));
}, t);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.resolve(page_)).href);
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.querySelectorAll("video")].map((v) =>
      v.readyState >= 2 ? null : new Promise((ok, no) => { v.onloadeddata = ok; v.onerror = () => no(new Error("video failed: " + v.src)); })));
  });
  await seekAll(page, 0);
  const slides = await page.$$(".slide");
  for (let i = 0; i < slides.length; i++) {
    await slides[i].screenshot({ path: path.join(outdir, `${prefix}-${String(i + 1).padStart(2, "0")}.jpg`), type: "jpeg", quality: 92 });
  }
  if (flag === "--animate") {
    const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", path.join(outdir, `${prefix}-01.mp4`)],
      { stdio: ["pipe", "inherit", "inherit"] });
    const n = Math.round(FPS * Number(secs || 4));
    for (let i = 0; i < n; i++) {
      await seekAll(page, i / FPS);
      const buf = await slides[0].screenshot({ type: "jpeg", quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((ok, no) => ff.on("close", (c) => (c ? no(new Error("ffmpeg " + c)) : ok())));
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
