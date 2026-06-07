import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { execSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../../../..");
const GENERATE_SCRIPT = path.join(REPO_ROOT, "content-generation/generate.py");

export function registerGenerateAsset(server: McpServer) {
  server.tool(
    "generate_asset",
    "Generate an AI video clip and add it to the content bank catalog.",
    {
      mode: z.enum(["atmosphere", "likeness"]).describe(
        "atmosphere: text-to-video, no face needed. likeness: generates Matteo via LoRA then animates."
      ),
      shot_type: z.enum(["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"]),
      prompt: z.string().describe(
        "Base prompt. For likeness mode, start with MATTEO. Brand style preset is appended automatically."
      ),
      tags: z.array(z.string()).default([]),
      duration: z.number().default(5.0),
      mood: z.string().default("cinematic"),
    },
    async ({ mode, shot_type, prompt, tags, duration, mood }) => {
      const tagStr = tags.join(" ");
      const cmd = [
        `python "${GENERATE_SCRIPT}"`,
        mode,
        `--shot_type ${shot_type}`,
        `--prompt "${prompt}"`,
        `--tags ${tagStr}`,
        `--duration ${duration}`,
        `--mood ${mood}`,
      ].join(" ");

      try {
        const output = execSync(cmd, {
          env: { ...process.env },
          encoding: "utf-8",
          timeout: 300_000,
        });
        return { content: [{ type: "text" as const, text: output }] };
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        return { content: [{ type: "text" as const, text: `Error: ${message}` }], isError: true };
      }
    }
  );
}
