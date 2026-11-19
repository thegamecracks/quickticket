# Yaak workspace

This directory is the sync directory of the `quickticket` workspace
(`wk_3xuzadZJ9F`). The Yaak desktop app writes one YAML file per resource here;
the `yaak` CLI reads and writes the same local database.

The app only syncs the workspace it currently has open. If another workspace is
open, CLI changes stay in the local database until you switch back to
`quickticket`.

## Run order

| Order | Folder | What it covers |
|---|---|---|
| 1 | `00 Setup` | **Manual, once per fresh database/user.** Bootstrap the cookie jar, then create the test organization. |
| 2 | `10 Profile` | Gets the current profile and anchors the organization ID for the later folders. |
| 3 | `20 Organizations` | List, get, and update the organization. |
| 4 | `30 Venues` | List, create, get, update, and the banner/thumbnail lifecycles. |
| 5 | `40 Events` | List, create, get, update, and the banner/thumbnail lifecycles. |
| 6 | `50 Not Implemented` | Every deprecated `501` route. |
| 7 | `60 Errors` | Curated `400/401/403/404/422` cases. |
| 8 | `80 Auth login` | **Manual only.** OAuth2 login flow; run only when establishing a fresh session. |
| 9 | `90 Logout` | Logout flow. Last, because it clears the token cookies. |

Every request description starts with its expected status, for example
`201. Creates the venue fixture...`.

## Authentication

Protected routes read the encrypted `oauth-access-token` and
`oauth-refresh-token` cookies from Yaak's cookie jar. The backend does not
accept an `Authorization: Bearer` header.

To populate the jar, either:

- Run `00 Setup / Bootstrap session` once. It prompts for the encrypted
  `oauth-refresh-token` cookie from a logged-in browser, sends it manually, and
  lets the backend refresh it so Yaak stores fresh token cookies.
- Or run `80 Auth login / Start login`, open the returned provider URL in a
  browser, and paste the authorization `code` into `Complete login`.

After the cookie jar is populated, `10 Profile` and later folders need no
further authentication work.

## The one-organization rule

`POST /api/organizations` allows one owned organization per user. `00 Setup`
creates it once. On later runs that request returns `400 Already owns an
organization`; skip `00 Setup` after the first successful run.

The routine folders do not depend on the create response. `10 Profile` reads
the organization ID from `organization_members[0].organization_id`, so reruns
still work after the one-time setup.

## Running

In the Yaak app, open the `quickticket` workspace and run the folders in order.
Skip `00 Setup` after the first run and skip `80 Auth login` unless you need a
fresh session. `90 Logout` goes last.

`yaak send <workspace>` and `yaak send <folder>` do **not** honour
`sortPriority`; the CLI sends newest-created first. For a full run, use:

```sh
scripts/run_yaak_workspace.sh
# Include the manual setup/login folders too:
scripts/run_yaak_workspace.sh --include-manual
# When more than one workspace exists:
scripts/run_yaak_workspace.sh wk_3xuzadZJ9F
```

The script exports the workspace, sorts folders and requests by
`sortPriority`, sends them one at a time, and compares each response with the
status at the start of its description. It skips the `00 Setup` and
`80 Auth login` folders unless `--include-manual` is given.

## Image fixture

The multipart requests upload `frontend/public/images/music.jpg` using an
absolute path. A relative path such as `../frontend/public/images/music.jpg`
works when the CLI is run from `backend/`, but the desktop app's working
directory is not the repository, so the saved requests use the absolute path.

## Notes

- `base_url` lives in the shared `Global Variables` environment and points at
  `http://127.0.0.1:8000`. Change it there for another host.
- `GET /api/auth/validate` and the `50 Not Implemented` routes are deprecated
  but are still saved so every documented route is covered.
- `/api/notifications` is a WebSocket route. The Yaak CLI can only create HTTP
  requests, so it is intentionally not in this workspace.
