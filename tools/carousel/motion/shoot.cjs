// Record every .slide of an animated-UI carousel page as its own 10 s 1080x1350 mp4 (+ a frame-0 jpg, the thumbnail).
//   node tools/carousel/motion/shoot.cjs PAGE.html OUTDIR [SECONDS] [SPEED]
// SPEED > 1 plays the page's timeline faster (sparring.html is laid out on 10 s; 6 s at speed 1.6 keeps ~1 s of hold).
// Deterministic like ../shoot.cjs: each frame pauses every animation at t and screenshots, no real-time capture.
const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { pathToFileURL } = require("node:url");
const path = require("node:path");
const fs = require("node:fs");

const [page_, outdir, secs = "6", speed = "1.6"] = process.argv.slice(2);
const FPS = 30;

(async () => {
  fs.mkdirSync(outdir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.resolve(page_)).href);
  await page.evaluate(() => document.fonts.ready);
  const count = await page.$$eval(".slide", (s) => s.length);
  for (let s = 0; s < count; s++) {
    await page.evaluate((s) => document.querySelectorAll(".slide").forEach((el, i) => el.classList.toggle("on", i === s)), s);
    const name = path.join(outdir, `slide-${String(s + 1).padStart(2, "0")}`);
    const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", name + ".mp4"],
      { stdio: ["pipe", "inherit", "inherit"] });
    const n = Math.round(FPS * Number(secs));
    for (let i = 0; i < n; i++) {
      await page.evaluate((t) => document.getAnimations().forEach((a) => { a.pause(); a.currentTime = t; }), (i / FPS) * 1000 * Number(speed));
      const buf = await page.screenshot({ type: "jpeg", quality: 95 });
      if (i === 0) fs.writeFileSync(name + ".jpg", buf);
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    }
    ff.stdin.end();
    await new Promise((ok, no) => ff.on("close", (c) => (c ? no(new Error("ffmpeg " + c)) : ok())));
    console.log("slide", s + 1, "done");
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
