// Telegram webhook. Answers taps instantly, then hands the update to the Control workflow.
// Cloudflare Access must BYPASS this one path (Telegram can't log in); the secret header protects it.
import { dispatch, json, tg } from "../../lib/shared.js";

export async function onRequestPost({ request, env }) {
  if (request.headers.get("x-telegram-bot-api-secret-token") !== env.TELEGRAM_WEBHOOK_SECRET) {
    return json({ error: "not allowed" }, 403);
  }
  const u = await request.json();
  const msg = u.message || (u.callback_query || {}).message || {};
  const chat = String((msg.chat || {}).id || "");

  // Setup helper: until TELEGRAM_CHAT_ID is set, tell the sender their chat id and do nothing else.
  if (!env.TELEGRAM_CHAT_ID) {
    if (chat) await tg(env, "sendMessage", { chat_id: chat, text: `Your chat id is ${chat}. Put it in Cloudflare and GitHub as TELEGRAM_CHAT_ID.` });
    return json({ ok: true });
  }
  if (chat !== String(env.TELEGRAM_CHAT_ID)) return json({ ok: true }); // anyone else: silently ignored

  if (u.callback_query) {
    await tg(env, "answerCallbackQuery", { callback_query_id: u.callback_query.id, text: "⏳ On it…" });
  }
  await dispatch(env, { action: "telegram", update: u }, "Telegram");
  return json({ ok: true });
}
