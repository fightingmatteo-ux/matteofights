// POST /api/act {action: "approve_week" | "answer" | "idea" | "platform_set", ...} from the dashboard.
import { accessEmail, dispatch, json } from "../../lib/shared.js";

const ACTIONS = new Set(["approve_week", "approve_threads", "threads_skip", "threads_edit", "answer", "idea", "platform_set"]);

export async function onRequestPost({ request, env }) {
  const email = await accessEmail(request, env);
  if (!email || email !== (env.OWNER_EMAIL || "").toLowerCase()) return json({ error: "not allowed" }, 403);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }
  if (!ACTIONS.has(body.action)) return json({ error: "unknown action" }, 400);
  if (body.action === "idea" && !String(body.text || "").trim()) return json({ error: "empty idea" }, 400);
  await dispatch(env, body, "dashboard");
  return json({ ok: true });
}
