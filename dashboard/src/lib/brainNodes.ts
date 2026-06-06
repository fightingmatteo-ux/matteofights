export type NodeId =
  | "founder"
  | "brand"
  | "voice"
  | "audience"
  | "strategy"
  | "content"
  | "social"
  | "viral-format"
  | "apps"
  | "analytics"
  | "draft";

export interface BrainNode {
  id: NodeId;
  label: string;
}

/** The brain, as nodes around the CORE. Order = clockwise placement. */
export const BRAIN_NODES: BrainNode[] = [
  { id: "founder", label: "founder" },
  { id: "brand", label: "brand" },
  { id: "voice", label: "voice" },
  { id: "audience", label: "audience" },
  { id: "strategy", label: "strategy" },
  { id: "content", label: "content" },
  { id: "social", label: "social" },
  { id: "viral-format", label: "viral" },
  { id: "apps", label: "apps" },
  { id: "analytics", label: "analytics" },
  { id: "draft", label: "draft" },
];

/** Map a tool name + target path to the brain node that should flare. */
export function targetToNode(toolName: string, target?: string): NodeId | null {
  if (toolName.includes("save_reel_draft")) return "draft";
  const t = (target ?? "").toLowerCase().replace(/\\/g, "/");
  if (!t) return null;
  if (t.includes("analytics")) return "analytics";
  if (t.includes("caption-engine") || t.includes("viral-format")) return "viral-format";
  // Prefer an explicit context/<name>.md match.
  for (const node of BRAIN_NODES) {
    if (t.includes(`context/${node.id}`)) return node.id;
  }
  // Looser fallback: filename contains a node id.
  for (const node of BRAIN_NODES) {
    if (node.id !== "draft" && node.id !== "analytics" && t.includes(node.id)) return node.id;
  }
  return null;
}

export type Phase = "idle" | "listening" | "reading" | "thinking" | "drafting" | "speaking";

/** Single source of truth for which state the CORE is in. Precedence matters. */
export function derivePhase(opts: {
  busy: boolean;
  speaking: boolean;
  reading: boolean;
  drafting: boolean;
  listening: boolean;
}): Phase {
  if (opts.speaking) return "speaking";
  if (opts.drafting) return "drafting";
  if (opts.reading) return "reading";
  if (opts.busy) return "thinking";
  if (opts.listening) return "listening";
  return "idle";
}
