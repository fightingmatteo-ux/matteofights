# @matteofights Dashboard

Fight-intelligence terminal for @matteofights — reel performance, reach/views trend, and the
content-bank, read from the latest Windsor analytics snapshot.

Stack: Vite + React + TypeScript + Tailwind + Recharts. Dark fight-poster aesthetic
(Bebas Neue / Archivo / JetBrains Mono, combat red + gold).

## Run

```bash
cd dashboard
npm install        # see CA note below if this hangs/errors
npm run dev        # local dev server
npm run build      # production build -> dist/
npm run preview    # preview the production build
```

`predev` / `prebuild` run `scripts/sync-data.mjs`, which copies the newest
`../analytics/snapshots/*.json` into `public/data/latest.json`. New Windsor pulls show up
automatically — no code changes needed. Run `npm run sync-data` manually to refresh.

## ⚠️ npm cert note (this machine)

This machine sits behind TLS inspection, so plain `npm install` fails with
`UNABLE_TO_VERIFY_LEAF_SIGNATURE`. Install with the system CA:

```bash
NODE_OPTIONS=--use-system-ca npm install
```

(Same flag the Remotion pipeline uses. Node 24 here supports it.)

## Deploy (Student Pack)

Static build — deploy `dist/` to Vercel or Netlify. Set the project root to `dashboard/`; the
prebuild step reads `../analytics/snapshots`, which is present in the repo at build time.
`base: "./"` in `vite.config.ts` keeps it path-portable.

## Data shape

Reads `Snapshot` (see `src/types.ts`): `profile`, `daily_last_30d`, `top_media_by_views`.
