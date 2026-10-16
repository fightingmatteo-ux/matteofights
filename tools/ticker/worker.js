// Reliable timer for the GitHub posting workflows (GitHub's own cron runs hours late).
// Cloudflare runs this every 5 minutes (free). At each New York slot it starts the workflow via workflow_dispatch,
// so posts go out within ~5 min of their time. Slots live in wrangler.toml [vars]; keep them in sync with
// production/schedule (Post queue: the listicle slots; Cross-post: every slot in production/schedule/crosspost.json
// + written Threads posts). Secret GH_TOKEN = fine-grained token, repo matteofights, Actions: read and write.
const nyHM = (d) => new Intl.DateTimeFormat("en-GB", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
const mins = (hm) => { const [h, m] = hm.split(":").map(Number); return h * 60 + m; };

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
    const now = mins(nyHM(new Date(event.scheduledTime)));
    const due = (list) => list.split(",").some((s) => { const d = now - mins(s.trim()); return d >= 0 && d < 5; });
    const out = [];
    if (due(env.POST_SLOTS)) out.push(await dispatch(env, "post-queue.yml"));
    if (due(env.XPOST_SLOTS)) out.push(await dispatch(env, "crosspost.yml"));
    console.log(nyHM(new Date(event.scheduledTime)), out.join(" ") || "no slot");
  },
};
