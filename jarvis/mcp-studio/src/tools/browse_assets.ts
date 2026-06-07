import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CATALOG_PATH = path.resolve(__dirname, "../../../../content-bank/catalog.json");

export function registerBrowseAssets(server: McpServer) {
  server.tool(
    "browse_assets",
    "Query the content bank catalog to find available clips.",
    {
      shot_type: z.enum(["arrival", "training", "atmosphere", "outdoor", "lifestyle", "hero"]).optional(),
      tags: z.array(z.string()).optional(),
      likeness: z.boolean().optional(),
      source: z.enum(["ai", "real"]).optional(),
    },
    async ({ shot_type, tags, likeness, source }) => {
      const catalog: Array<Record<string, unknown>> = JSON.parse(readFileSync(CATALOG_PATH, "utf-8"));

      let results = catalog;
      if (shot_type) results = results.filter((e) => e["shot_type"] === shot_type);
      if (tags?.length) results = results.filter((e) => {
        const entryTags = e["tags"] as string[];
        return tags.every((t) => entryTags.includes(t));
      });
      if (likeness !== undefined) results = results.filter((e) => e["likeness"] === likeness);
      if (source) results = results.filter((e) => e["source"] === source);

      const summary = results.map((e) =>
        `${e["id"]} | ${e["shot_type"]} | ${e["file"]} | tags: ${(e["tags"] as string[]).join(", ")} | likeness: ${e["likeness"]}`
      ).join("\n");

      return {
        content: [{ type: "text" as const, text: `Found ${results.length} assets:\n\n${summary}` }],
      };
    }
  );
}
