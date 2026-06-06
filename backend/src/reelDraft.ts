export type Archetype = "TACTICAL" | "IDENTITY";

export interface ReelInput {
  date: string; // YYYY-MM-DD
  archetype: Archetype;
  thumbnail: string; // on-screen hook, ALL CAPS
  subhook: string; // 2 lines; line 2 points at a #number
  caption: string; // full caption body
  hashtags: string[]; // 2-4 niche tags, each starting with #
}

export function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function validateReelInput(input: ReelInput): string[] {
  const errors: string[] = [];
  if (input.archetype !== "TACTICAL" && input.archetype !== "IDENTITY") {
    errors.push("archetype must be TACTICAL or IDENTITY");
  }
  if (input.hashtags.length < 2 || input.hashtags.length > 4) {
    errors.push("hashtags must be 2-4 items");
  }
  if (!input.hashtags.every((h) => h.startsWith("#"))) {
    errors.push("each hashtag must start with #");
  }
  // Subhook style (binary contrast / counterintuitive statement) is enforced by the
  // caption engine + the agent, not by a rigid regex here — kept free-form on purpose.
  if (input.subhook.trim().length === 0) {
    errors.push("subhook is required");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(input.date)) {
    errors.push("date must be YYYY-MM-DD");
  }
  return errors;
}

export function renderReelMarkdown(input: ReelInput): string {
  return `---
date: ${input.date}
status: draft
archetype: ${input.archetype}
dm_trigger: HELP
---

# ${input.thumbnail}

## Thumbnail text (on-screen, ALL CAPS, red-on-black)
${input.thumbnail}

## Subhook (caption opener, 2 lines)
${input.subhook}

## Caption
${input.caption}

## Hashtags
${input.hashtags.join(" ")}
`;
}
