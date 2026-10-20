// Reliable timer for the GitHub posting workflows (GitHub's own cron runs hours late).
// Cloudflare runs this every 5 minutes (free). At each New York slot it starts the workflow via workflow_dispatch,
// so posts go out within ~5 min of their time. Slots live in wrangler.toml [vars]; keep them in sync with
// production/schedule (Post queue: the listicle slots; Cross-post: every slot in production/schedule/crosspost.json
// + written Threads posts). Post queue also starts as soon as an approved item in D1 (binding DB) is due.
// Secret GH_TOKEN = fine-grained token, repo matteofights, Actions: read and write.
import { slotDue, queueDue } from "./due.js";

const nyHM = (d) => new Intl.DateTimeFormat("en-GB", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(d);

async function dispatch(env, wf) {
  const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${wf}/dispatches`, {
    method: "POST",
    headers: { authorization: `Bearer ${env.GH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "matteo-ticker" },
    body: JSON.stringify({ ref: "master" }),
  });
  return `${wf}: ${r.status}`;
}

export default {
  async scheduled(event, env) {
    const now = event.scheduledTime;
    const out = [];
    let qdue = false;
    try {
      const { results } = await env.DB.prepare("SELECT data FROM docs WHERE kind = 'queue'").all();
      qdue = queueDue(now, results.map((r) => JSON.parse(r.data)));
    } catch (e) {
      console.log("D1 read failed, slots only:", String(e));
    }
    if (slotDue(now, env.POST_SLOTS) || qdue) out.push(await dispatch(env, "post-queue.yml"));
    if (slotDue(now, env.XPOST_SLOTS)) out.push(await dispatch(env, "crosspost.yml"));
    console.log(nyHM(new Date(now)), out.join(" ") || "no slot");
  },
};
