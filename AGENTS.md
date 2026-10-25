# Instructions for non-Claude coding agents (Gemini / Antigravity, Copilot, others)

The full rules are in [CLAUDE.md](CLAUDE.md); read it first. The ones that bite other agents:

- **Drafting is free; publishing is not.** Never post, schedule or send anything outward. Never set `approved: true`
  (only Matteo does). Do not run `tools/instagram/approve.py`.
- **Live state only through `tools/state.py`.** Never hand-edit `production/schedule/*.json`.
- **Git:** other sessions and bots push to master all day. Work on a branch (`gemini/<topic>`), `git pull --rebase
  --autostash` before pushing, `git add <your paths>` (never `-a`). Never commit `secrets/`, `media/`, `data.json`,
  `covers/`, renders. Open a PR; do not push to master.
- **Renders run in the cloud** (tools/render/README.md), not on this machine.
- Copy: no em dashes in user-facing text. Voice: context/voice.md.
- Never print or paste keys. If a task needs a secret you do not have, stop and ask.
