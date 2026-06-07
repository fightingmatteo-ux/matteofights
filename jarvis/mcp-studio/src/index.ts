import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerGenerateAsset } from "./tools/generate_asset.js";
import { registerBrowseAssets } from "./tools/browse_assets.js";
import { registerCompileReel } from "./tools/compile_reel.js";

const server = new McpServer({ name: "studio", version: "1.0.0" });

registerGenerateAsset(server);
registerBrowseAssets(server);
registerCompileReel(server);

const transport = new StdioServerTransport();
await server.connect(transport);
