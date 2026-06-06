import "dotenv/config";
import express from "express";
import { PORT } from "./config";
import { makeChatHandler } from "./chatHandler";
import { runJarvisTurn } from "./agent";

const app = express();
app.use(express.json({ limit: "1mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, hasKey: Boolean(process.env.ANTHROPIC_API_KEY) });
});

app.post("/api/chat", makeChatHandler(runJarvisTurn));

app.listen(PORT, () => {
  console.log(`Jarvis backend listening on http://localhost:${PORT}`);
});
