import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";
import { validateReelInput, type ReelInput } from "./reelDraft";
import { writeReelDraft } from "./saveReelDraft";

const saveReelDraft = tool(
  "save_reel_draft",
  "Persist a finished reel (thumbnail hook, subhook, full caption, hashtags) as a draft markdown file. Use only after composing the reel from the brain. dm_trigger is always HELP. This does NOT post anything.",
  {
    date: z.string().describe("YYYY-MM-DD, usually today"),
    archetype: z.enum(["TACTICAL", "IDENTITY"]),
    thumbnail: z.string().describe("On-screen hook, ALL CAPS"),
    subhook: z
      .string()
      .describe(
        "2-line caption opener; line 2 points at a numbered item, e.g. 'And almost everyone skips #5.'",
      ),
    caption: z.string().describe("Full caption body in Matteo's voice"),
    hashtags: z.array(z.string()).describe("2-4 niche combat hashtags, each starting with #"),
  },
  async (args) => {
    const input = args as ReelInput;
    const errors = validateReelInput(input);
    if (errors.length > 0) {
      return {
        content: [{ type: "text", text: `Draft rejected. Fix and retry:\n- ${errors.join("\n- ")}` }],
        isError: true,
      };
    }
    const path = writeReelDraft(input);
    return { content: [{ type: "text", text: `Draft saved to ${path}` }] };
  },
);

export const captionServer = createSdkMcpServer({
  name: "jarvis",
  version: "0.1.0",
  tools: [saveReelDraft],
});
