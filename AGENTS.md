# QuickTicket

QuickTicket is a web application for creating and discovering physical/virtual
events and purchasing tickets. This repository is a monorepo:

- `backend/` — a Python HTTP API serving JSON to the frontend.
- `frontend/` — the user-facing frontend, built with React.js.

## Git conventions

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):

- Backend-only changes use the `backend` scope, e.g. `feat(backend): …`.
- Frontend-only changes use the `frontend` scope, e.g. `feat(frontend): …`.
- Do not mix backend and frontend changes in the same commit. Commit them separately.
- Branch names use the pattern `username/my-feature`.
