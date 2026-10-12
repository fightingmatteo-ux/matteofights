import "dotenv/config";
import express from "express";
import { createReadStream, existsSync, statSync } from "node:fs";
import { PORT } from "./config";
import { makeChatHandler } from "./chatHandler";
import { runJarvisTurn } from "./agent";
import { getStatus, noteClientActivity, refreshNow, startRefreshLoop } from "./refresher";
import { confirmAndPublish, discard, listAll, listPending } from "./publishQueue";

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, hasKey: Boolean(process.env.ANTHROPIC_API_KEY) });
});

app.post("/api/chat", makeChatHandler(runJarvisTurn));

// The dashboard polls this while its tab is visible. Two jobs: report the freshness of
// what's on screen, and act as the "someone is watching" signal that arms the pull loop.
app.get("/api/status", (_req, res) => {
  noteClientActivity();
  res.json({ ...getStatus(), pendingPublishes: listPending().length });
});

// The header's refresh control. Previously "refresh" only re-read the file already on
// disk, so it could never change the number it was next to — this makes it pull.
app.post("/api/refresh", async (_req, res) => {
  noteClientActivity();
  const outcome = await refreshNow("manual");
  res.status(outcome.ok ? 200 : 502).json({ outcome, status: getStatus() });
});

// ---------------------------------------------------------------- publish queue
// Jarvis stages reels here; only the confirm route below reaches Instagram, and it is
// only ever called by a click in the dashboard.

app.get("/api/publish/queue", (_req, res) => {
  res.json({ items: listAll() });
});

/** Streams a staged video so it can be watched before it goes out. Range-aware so the */
/** browser's scrubber works instead of forcing a full download first. */
app.get("/api/publish/:id/video", (req, res) => {
  const item = listAll().find((r) => r.id === req.params.id);
  if (!item || !existsSync(item.videoPath)) {
    res.status(404).json({ error: "no staged video with that id" });
    return;
  }
  const size = statSync(item.videoPath).size;
  const range = req.headers.range;
  if (range) {
    const [startRaw, endRaw] = range.replace(/bytes=/, "").split("-");
    const start = Number(startRaw) || 0;
    const end = endRaw ? Number(endRaw) : size - 1;
    res.writeHead(206, {
      "Content-Range": `bytes ${start}-${end}/${size}`,
      "Accept-Ranges": "bytes",
      "Content-Length": end - start + 1,
      "Content-Type": "video/mp4",
    });
    createReadStream(item.videoPath, { start, end }).pipe(res);
    return;
  }
  res.writeHead(200, { "Content-Length": size, "Content-Type": "video/mp4", "Accept-Ranges": "bytes" });
  createReadStream(item.videoPath).pipe(res);
});

/**
 * The publish button. This is the single place in the system that posts to Instagram,
 * and it exists behind a human click on purpose — an agent has no route to it.
 */
app.post("/api/publish/:id/confirm", async (req, res) => {
  try {
    const item = await confirmAndPublish(req.params.id);
    res.status(item.status === "published" ? 200 : 502).json({ item });
  } catch (e) {
    res.status(400).json({ error: e instanceof Error ? e.message : "publish failed" });
  }
});

app.post("/api/publish/:id/discard", (req, res) => {
  const item = discard(req.params.id);
  if (!item) {
    res.status(404).json({ error: "no staged reel with that id" });
    return;
  }
  res.json({ item });
});

app.listen(PORT, () => {
  console.log(`Jarvis backend listening on http://localhost:${PORT}`);
  startRefreshLoop();
  // One pull at boot so a dashboard opened straight after launch shows today's figures
  // rather than whatever was last on disk.
  void refreshNow("startup");
});
