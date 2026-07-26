# frontend/

Vite + React + `react-router-dom`. **Not Next.js** — it started as Next.js
(`00_OVERVIEW.md`'s original choice) and was migrated once every page ended up
client-side-fetching anyway; see `06_DECISIONS.md` D10 for the full reasoning.
Don't reintroduce SSR/server components — there's no server-side rendering
story here on purpose, and production has *zero* Node.js runtime (Caddy serves
the static `dist/` build directly).

## Conventions

- **One page per file** in `src/pages/` (`Screener.tsx`, `Portfolio.tsx`,
  `StockDetail.tsx`, `Admin.tsx`), routed in `src/App.tsx`. New top-level views
  follow the same pattern: add the file, add a `<Route>`, add a nav `<Link>`.
- **All data fetching is client-side**, `useEffect` + `fetch`, no server
  components, no data-loading route conventions. Every page talks directly to
  the backend via `API_URL` from `src/api.ts` (`import.meta.env.VITE_API_URL`,
  defaults to `http://localhost:8000/api` for local dev).
- **Inline styles, no CSS framework.** Consistent with the rest of the app —
  don't introduce Tailwind/styled-components/etc. for one component.
- **Basic error states are expected**, not optional: every page's `fetch`
  should handle a non-ok response and an unreachable backend (see any existing
  page's `.catch()` pattern) — verified in `06_DECISIONS.md`-era testing by
  actually killing the API and checking the UI didn't just hang.

## Setup

```
npm install
cp .env.local.example .env.local
npm run dev   # localhost:3000 - port is fixed in vite.config.ts to match
              # the backend's CORS allow_origins in backend/main.py
```

## Building for deploy

```
VITE_API_URL=https://investlens.duckdns.org/api npm run build
```

`vite build` bakes `VITE_API_URL` into the JS bundle at build time (it's not
read at runtime) — always rebuild with the right value before rsyncing
`dist/` to the VM. See the root `CLAUDE.md` "Deployment" section for the full
ship-a-change flow.
