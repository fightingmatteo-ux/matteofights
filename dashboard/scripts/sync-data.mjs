// Copies the newest *healthy* analytics snapshot into public/data/latest.json and writes
// an index of all available snapshots. Runs automatically before dev/build, and again on
// every change to analytics/snapshots/ while the dev server is up (see vite.config.ts),
// so new Windsor pulls show up in the dashboard without touching code or restarting.
import { readdirSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { checkSnapshot, ageInDays } from "./snapshot-health.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const snapshotsDir = join(root, "..", "analytics", "snapshots");
const outDir = join(root, "public", "data");

mkdirSync(outDir, { recursive: true });

function writeIndex(payload) {
  writeFileSync(join(outDir, "index.json"), JSON.stringify(payload, null, 2));
}

if (!existsSync(snapshotsDir)) {
  console.warn(`[sync-data] no snapshots dir at ${snapshotsDir} — writing empty index.`);
  writeIndex({ snapshots: [] });
  process.exit(0);
}

const files = readdirSync(snapshotsDir)
  .filter((f) => f.endsWith(".json"))
  .sort(); // YYYY-MM-DD.json sorts chronologically

if (files.length === 0) {
  console.warn("[sync-data] no snapshot files found — writing empty index.");
  writeIndex({ snapshots: [] });
  process.exit(0);
}

// Copy every snapshot so the UI can offer a date picker later.
for (const f of files) copyFileSync(join(snapshotsDir, f), join(outDir, f));

// Walk newest -> oldest and promote the first snapshot that passes the health gate.
// A failing snapshot stays on disk (so it can be inspected) but never becomes
// latest.json — a provider error must not overwrite a good number with zeros.
let latest = null;
const rejected = [];
for (const f of [...files].reverse()) {
  let parsed;
  try {
    parsed = JSON.parse(readFileSync(join(snapshotsDir, f), "utf8"));
  } catch (e) {
    rejected.push(`${f}: unparseable JSON (${e.message})`);
    continue;
  }
  const { ok, problems } = checkSnapshot(parsed);
  if (ok) {
    latest = { file: f, snapshot: parsed };
    break;
  }
  rejected.push(`${f}: ${problems.join("; ")}`);
}

for (const r of rejected) console.error(`[sync-data] REJECTED ${r}`);

if (!latest) {
  console.error("[sync-data] no healthy snapshot found — leaving latest.json untouched.");
  writeIndex({ snapshots: files, rejected, healthy: false });
  process.exit(1);
}

copyFileSync(join(snapshotsDir, latest.file), join(outDir, "latest.json"));

const age = ageInDays(latest.snapshot.pulled_at ?? latest.file.replace(/\.json$/, ""));
writeIndex({
  latest: latest.file,
  snapshots: files,
  rejected,
  healthy: true,
  synced_at: new Date().toISOString(),
  age_days: age,
});

console.log(
  `[sync-data] ${files.length} snapshot(s) synced. latest = ${latest.file}` +
    (age !== null ? ` (${age}d old)` : "")
);
if (age !== null && age > 2) {
  console.warn(
    `[sync-data] WARNING: newest healthy snapshot is ${age} days old. The dashboard will ` +
      `label it stale. Write a fresh snapshot to analytics/snapshots/ to update it.`
  );
}
