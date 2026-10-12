import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { execFile } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// package.json is type:module, so Vite loads this config as ESM — no __dirname here.
const here = dirname(fileURLToPath(import.meta.url));
const snapshotsDir = resolve(here, "..", "analytics", "snapshots");
const syncScript = resolve(here, "scripts", "sync-data.mjs");

/**
 * Re-runs sync-data whenever a snapshot lands in analytics/snapshots/ while the dev
 * server is up. Without this, `predev` was the only thing that ever ran the sync, so a
 * fresh Windsor pull didn't reach public/data/latest.json until someone restarted the
 * server. The dashboard polls latest.json, so the new number appears on its own.
 */
function snapshotWatcher(): Plugin {
  let syncing = false;
  let queued = false;

  const sync = () => {
    if (syncing) {
      queued = true;
      return;
    }
    syncing = true;
    execFile(
      process.execPath,
      [syncScript],
      (err, stdout, stderr) => {
        syncing = false;
        if (stdout.trim()) console.log(stdout.trim());
        if (stderr.trim()) console.warn(stderr.trim());
        if (err) console.error(`[snapshot-watcher] sync failed: ${err.message}`);
        if (queued) {
          queued = false;
          sync();
        }
      }
    );
  };

  return {
    name: "matteofights-snapshot-watcher",
    apply: "serve",
    configureServer(server) {
      server.watcher.add(snapshotsDir);
      for (const event of ["add", "change", "unlink"] as const) {
        server.watcher.on(event, (file: string) => {
          if (file.startsWith(snapshotsDir) && file.endsWith(".json")) {
            console.log(`[snapshot-watcher] ${event}: ${file} — re-syncing`);
            sync();
          }
        });
      }
    },
  };
}

// base "./" keeps the build portable — works at any path on Vercel/Netlify/static hosts.
export default defineConfig({
  base: "./",
  plugins: [react(), snapshotWatcher()],
  server: {
    proxy: {
      "/api": "http://localhost:8787",
    },
  },
});
