# frontend/

Next.js 16 App Router, `output: "export"` + `trailingSlash: true` (pages build to
`out/<route>/index.html`, served by Caddy; no Node server at runtime). Read `AGENTS.md`: this Next version
differs from older docs; bundled docs are in `node_modules/next/dist/docs/`.

- Every page is a client component; data via TanStack Query hooks in `src/lib/queries.ts`
  (`api()` in `src/lib/api.ts`, base `/api` in prod, `http://localhost:8000/api` in dev).
  `useStatus` polls fast while jobs run and invalidates everything when they finish.
- No dynamic route segments: stock pages are `/stock/?s=SYMBOL` (or `?isin=`), read with
  `useSearchParams` inside `<Suspense>`.
- shadcn components are the Base UI flavour (`render` prop, not `asChild`); links styled as
  buttons use `buttonVariants`.
- Design: Rams functionalism via Kite/Console. Tokens in `src/app/globals.css` (light + `.dark`);
  colour only for gain/loss and broker identity; IBM Plex Sans; `.num` for tabular figures; panels
  are bordered (`components/panel.tsx`), no shadows.
- Charts: `lightweight-charts` (`components/charts/time-series-chart.tsx`), SVG sparkline/donut/range
  bar, `d3-hierarchy` treemap. Indian number formatting in `src/lib/format.ts`.
- Mobile first: bottom tab bar under `md`, tables become lists under `lg`.
- Check with `npx tsc --noEmit && npx eslint src && npm run build`.
