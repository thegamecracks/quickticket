# QuickTicket frontend

This is the QuickTicket web frontend written with React 19 + TypeScript,
built with Vite, and styled with Tailwind 4 + daisyUI.

## Prerequisites

This project is managed with [Bun](https://bun.sh/).

```sh
# Linux
curl -fsSL https://bun.sh/install | bash
# Windows
powershell -c "irm bun.sh/install.ps1|iex"
```

## Getting started

```sh
cd frontend
bun install  # install dependencies from bun.lock
bun run dev  # start the dev server at http://localhost:5173
```

For the backend, make sure to set a `.env` file to reach the backend:

```ini
VITE_API_URL=http://127.0.0.1:8000/api
```

If you also want Google Maps support, you'll need to set
`VITE_GOOGLE_MAPS_API_KEY` and `VITE_GOOGLE_MAPS_MAP_ID`.

## Commands

| Command           | What it does                       |
| ----------------- | ---------------------------------- |
| `bun run dev`     | Development server                 |
| `bun run lint`    | Run oxlint                         |
| `bun run build`   | Type-check and build to `dist/`    |
| `bun run preview` | Serve the production build locally |

## Before you commit

```sh
bun run lint
bun run build
```

`lint` must exit 0 with no new warnings, and `build` must pass.
There is no test runner yet so you should manually test in your browser.
