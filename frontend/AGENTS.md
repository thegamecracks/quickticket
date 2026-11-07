# QuickTicket Frontend

React 19 + TypeScript SPA (Vite, Tailwind 4 + daisyUI), package manager `bun`.

## Verify before you finish

```sh
bun run lint    # oxlint — exits 0 with warnings only
bun run build   # tsc -b && vite build
```

`lint` must stay clean. `build` must add no errors: it is already red on `src/lib/markdown.ts`
(implicit-`any` on markdown-it renderer callbacks), so compare against that baseline rather
than expecting green.

No test runner is configured; `build` is the type check, and behaviour is verified in the
browser (`bun run dev`).

## Layout

- `src/features/<domain>/` — a domain's pages with their private components and types
  (`events`, `checkout`, `host`, `account`, `tickets`, `organizations`, `notifications`).
- `src/components/` — components shared across features; `src/pages/` — standalone pages;
  `src/layouts/`, `src/lib/` (API client, auth, types, formatting helpers), `src/styles/`.
- `src/App.tsx` registers every route — a new page is not reachable until it is added there.

## Conventions

- API calls go through the `api` axios instance in `src/lib/api.ts` (`VITE_API_URL`); auth
  rides on cookies, so no token handling at call sites.
- Request paths mirror the backend routes (`/events`, `/events/:id`, `/organizations/:id`,
  `/venues/:id`, `/profile/@me`).
- Keep a component in its feature folder until a second feature needs it, then promote it to
  `src/components/`.
- `VITE_GOOGLE_MAPS_API_KEY` / `VITE_GOOGLE_MAPS_MAP_ID` configure maps.
