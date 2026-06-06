import { describe, it, expect } from "vitest";
import { slugify, validateReelInput, renderReelMarkdown, type ReelInput } from "../src/reelDraft";

const valid: ReelInput = {
  date: "2026-06-05",
  archetype: "IDENTITY",
  thumbnail: "6 SIGNS YOU'LL MAKE IT AS A FIGHTER",
  subhook: "Some people train for fun.\nSome people were built for this.",
  caption: "Most people quit...\n\n6 signs you'll make it:\n\n1. ...",
  hashtags: ["#boxing", "#fightermindset", "#muaythai", "#fightlife"],
};

describe("slugify", () => {
  it("kebab-cases and strips punctuation", () => {
    expect(slugify("6 SIGNS YOU'LL MAKE IT AS A FIGHTER")).toBe("6-signs-youll-make-it-as-a-fighter");
  });
});

describe("validateReelInput", () => {
  it("accepts a valid identity reel", () => {
    expect(validateReelInput(valid)).toEqual([]);
  });
  it("rejects fewer than 2 or more than 4 hashtags", () => {
    expect(validateReelInput({ ...valid, hashtags: ["#one"] })).toContain("hashtags must be 2-4 items");
    expect(validateReelInput({ ...valid, hashtags: ["#a", "#b", "#c", "#d", "#e"] })).toContain(
      "hashtags must be 2-4 items",
    );
  });
  it("rejects an unknown archetype", () => {
    expect(
      validateReelInput({ ...valid, archetype: "STANCE" as unknown as ReelInput["archetype"] }),
    ).toContain("archetype must be TACTICAL or IDENTITY");
  });
  it("requires a non-empty subhook", () => {
    expect(validateReelInput({ ...valid, subhook: "   " })).toContain("subhook is required");
  });
});

describe("renderReelMarkdown", () => {
  it("renders the canonical reel.md with HELP trigger and all sections", () => {
    const md = renderReelMarkdown(valid);
    expect(md).toContain("date: 2026-06-05");
    expect(md).toContain("archetype: IDENTITY");
    expect(md).toContain("dm_trigger: HELP");
    expect(md).toContain("# 6 SIGNS YOU'LL MAKE IT AS A FIGHTER");
    expect(md).toContain("## Thumbnail text (on-screen, ALL CAPS, red-on-black)");
    expect(md).toContain("## Subhook (caption opener, 2 lines)");
    expect(md).toContain("## Caption");
    expect(md).toContain("## Hashtags");
    expect(md).toContain("#boxing #fightermindset #muaythai #fightlife");
  });
});

import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { writeReelDraft } from "../src/saveReelDraft";

describe("writeReelDraft", () => {
  it("writes reel.md under <draftsDir>/<date>-<slug>/", () => {
    const dir = mkdtempSync(join(tmpdir(), "drafts-"));
    try {
      const path = writeReelDraft(valid, dir);
      expect(path).toBe(join(dir, "2026-06-05-6-signs-youll-make-it-as-a-fighter", "reel.md"));
      expect(readFileSync(path, "utf8")).toContain("dm_trigger: HELP");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
