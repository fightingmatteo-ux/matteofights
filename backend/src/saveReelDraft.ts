import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { DRAFTS_DIR } from "./config";
import { renderReelMarkdown, slugify, type ReelInput } from "./reelDraft";

/** Writes reel.md and returns its absolute path. `baseDir` overridable for tests. */
export function writeReelDraft(input: ReelInput, baseDir: string = DRAFTS_DIR): string {
  const folder = join(baseDir, `${input.date}-${slugify(input.thumbnail)}`);
  mkdirSync(folder, { recursive: true });
  const path = join(folder, "reel.md");
  writeFileSync(path, renderReelMarkdown(input), "utf8");
  return path;
}
