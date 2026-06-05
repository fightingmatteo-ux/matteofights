// Scaffolds a new reel draft from a hook.
//   node production/captions/new-reel.mjs "8 WAYS TO GET DANGEROUS TRAINING 3X A WEEK"
// Creates content-bank/captions/drafts/<date>-<slug>/reel.md for the agent to fill
// following production/captions/CAPTION-ENGINE.md. It scaffolds structure only — the
// copy is written by Claude/Jarvis per the engine.
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const hook = process.argv.slice(2).join(" ").trim();
if (!hook) {
  console.error('Usage: node new-reel.mjs "YOUR HOOK IN CAPS"');
  process.exit(1);
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, "..", "..");
const date = new Date().toISOString().slice(0, 10);
const slug = hook
  .toLowerCase()
  .replace(/[^a-z0-9\s-]/g, "")
  .trim()
  .replace(/\s+/g, "-")
  .slice(0, 48);

const dir = join(repoRoot, "content-bank", "captions", "drafts", `${date}-${slug}`);
if (existsSync(dir)) {
  console.error(`[new-reel] already exists: ${dir}`);
  process.exit(1);
}
mkdirSync(dir, { recursive: true });

const template = `---
date: ${date}
status: draft
archetype: TBD        # TACTICAL (saves) | IDENTITY (shares)
dm_trigger: HELP
---

# ${hook}

## Thumbnail text (on-screen, ALL CAPS, red-on-black)
${hook}

## Subhook (caption opener, 2 lines)
<!-- fill per CAPTION-ENGINE.md -->

## Caption
<!-- full viral-format caption per CAPTION-ENGINE.md -->

## Hashtags
<!-- 2-4 combat-niche -->
`;

writeFileSync(join(dir, "reel.md"), template);
console.log(`[new-reel] created ${join(dir, "reel.md")}`);
console.log("[new-reel] now fill it per production/captions/CAPTION-ENGINE.md");
