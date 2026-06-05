# @matteofights — Operating System

_The brain for Matteo's fighter Instagram (@matteofights). Last verified: 2026-06-05._

This repo is a personal operating system for growing @matteofights. Long-term it becomes a
voice-capable, partly-autonomous agent (see `docs/superpowers/specs/`). Today it's the brain +
analytics. Build it in phases; don't try to do everything at once.

---

## OPERATING RULES

- **Drafting is free; publishing is not.** Write captions, hooks, scripts, and reports freely.
  Never post to Instagram, schedule, or send anything outward without explicit confirmation in
  that conversation.
- **The north star is fighter-brand growth.** When a content or analytics call is ambiguous,
  optimize for reach, watch-through, and follower growth on @matteofights itself. Coaching
  lead-gen and the Stance funnel are real but secondary.
- **Read `context/` on demand, not all at once.** Use the routing table below.
- **Analytics files are dated snapshots.** Pull live via Windsor when current numbers matter,
  then write a fresh snapshot — don't trust a stale one.
- **Answer from the brain when you can.** If `context/` already covers a brand/voice/format
  question, answer directly without an API call.
- **Reels win, carousels flop** for this account. Default to reel thinking unless told otherwise.

---

## CONNECTED DATA (Windsor.ai — account: joinstance@gmail.com)

| Connector | Account | ID | Use for |
|---|---|---|---|
| `instagram` | Matteo (matteofights) | 17841465098113052 | Followers, reach, views, per-reel metrics, captions |

Other connected MCPs (see `context/apps.md`): Higgsfield (`virality_predictor`, image/video gen).

---

## CONTEXT FILES (read on demand)

| Topic | File | When to read |
|---|---|---|
| Who Matteo is — story, angles | [context/founder.md](context/founder.md) | Any copy, caption, or narrative work |
| Visual + verbal identity | [context/brand.md](context/brand.md) | Designing posts, thumbnails, the dashboard |
| Caption voice; words to avoid | [context/voice.md](context/voice.md) | Writing any caption or script |
| Who's watching | [context/audience.md](context/audience.md) | Targeting, hook psychology, copy |
| Growth plan & funnel | [context/strategy.md](context/strategy.md) | Strategic decisions, cadence, CTAs |
| Pillars, formats, cadence | [context/content.md](context/content.md) | Planning what to post |
| The proven viral reel format | [context/viral-format.md](context/viral-format.md) | Making a reel / writing a hook + caption |
| Caption engine (hook → caption) | [production/captions/CAPTION-ENGINE.md](production/captions/CAPTION-ENGINE.md) | Generating a reel's subhook + full caption from a hook |
| Analytics snapshots + IDs | [context/social.md](context/social.md) | Performance questions, before pulling live |
| Connected tools/MCPs | [context/apps.md](context/apps.md) | Tooling decisions |

---

## REPO MAP

```
context/        the brain (markdown, read on demand)
content-bank/   reels, captions, scraped posts
analytics/      snapshots/ (raw Windsor JSON) + reports/ (digested)
production/     remotion/ + carousels/ (content engine — Phase 2)
dashboard/      Vite+React "sick UI" (Phase 1+)
docs/superpowers/specs/   design + phase specs
```

## PHASE STATUS

- **Phase 0 — Foundation:** brain + migrated content + repo. _In progress._
- **Phase 1 — Analytics + dashboard:** Windsor pulls → snapshots/reports → read-only UI. _Next._
- **Phase 2 — Content engine + "make a reel":** caption + subhook engine built (text); video rendering deferred. _In progress._
- **Phase 3 — Jarvis + voice:** _Designed._
- **Phase 4 — Posting + 24/7 agents:** _Designed._

Full design: [docs/superpowers/specs/2026-06-05-matteofights-os-design.md](docs/superpowers/specs/2026-06-05-matteofights-os-design.md)
