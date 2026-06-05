// Copies the newest analytics snapshot into public/data/latest.json and writes
// an index of all available snapshots. Runs automatically before dev/build, so
// new Windsor pulls show up in the dashboard without touching code.
import { readdirSync, mkdirSync, copyFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const snapshotsDir = join(root, "..", "analytics", "snapshots");
const outDir = join(root, "public", "data");

mkdirSync(outDir, { recursive: true });

if (!existsSync(snapshotsDir)) {
  console.warn(`[sync-data] no snapshots dir at ${snapshotsDir} — writing empty index.`);
  writeFileSync(join(outDir, "index.json"), JSON.stringify({ snapshots: [] }, null, 2));
  process.exit(0);
}

const files = readdirSync(snapshotsDir)
  .filter((f) => f.endsWith(".json"))
  .sort(); // YYYY-MM-DD.json sorts chronologically

if (files.length === 0) {
  console.warn("[sync-data] no snapshot files found — writing empty index.");
  writeFileSync(join(outDir, "index.json"), JSON.stringify({ snapshots: [] }, null, 2));
  process.exit(0);
}

// Copy every snapshot so the UI can offer a date picker later; mark the newest as latest.
for (const f of files) copyFileSync(join(snapshotsDir, f), join(outDir, f));
const latest = files[files.length - 1];
copyFileSync(join(snapshotsDir, latest), join(outDir, "latest.json"));
writeFileSync(
  join(outDir, "index.json"),
  JSON.stringify({ latest, snapshots: files }, null, 2)
);

console.log(`[sync-data] ${files.length} snapshot(s) synced. latest = ${latest}`);
