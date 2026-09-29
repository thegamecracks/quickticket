from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs

from authlib.common.security import generate_token
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from quickticket.dependencies import CacheDep, OAuth2ClientDep, TokenDep
from quickticket.oauth import TokenExchangeResponse

router = APIRouter()


@dataclass(kw_only=True)
class LoginAttempt:
    expires_at: datetime
    code_verifier: str
    state: str


# TODO: use actual cache, requires list or key prefix match?
_login_cache: dict[str, LoginAttempt] = {}


# https://docs.authlib.org/en/latest/oauth2/client/http/index.html#oidc-session
@router.get("/login")
async def oauth_login(cache: CacheDep, client: OAuth2ClientDep) -> RedirectResponse:
    code_verifier = generate_token(48)  # assumes PKCE
    url, state = client.create_authorization_url(code_verifier)
    _store_login_attempt(code_verifier=code_verifier, state=state)
    return RedirectResponse(url, 302)


@router.get("/callback")
async def oauth_callback(request: Request, cache: CacheDep, client: OAuth2ClientDep) -> TokenExchangeResponse:
    query = parse_qs(request.url.query)
    state = query["state"][0]

    _prune_login_cache()
    attempt = _login_cache.get(state)

    if attempt is None:
        raise HTTPException(400, "Invalid state")

    tokens = await client.fetch_token(
        str(request.url),
        code_verifier=attempt.code_verifier,
    )
    _login_cache.pop(state, None)
    return tokens


@router.get("/logout")
async def oauth_logout(token: TokenDep, cache: CacheDep, client: OAuth2ClientDep):
    # client.create_logout_url()
    return token


def _store_login_attempt(*, code_verifier: str, state: str) -> None:
    _prune_login_cache()
    _login_cache[state] = LoginAttempt(
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        code_verifier=code_verifier,
        state=state,
    )


def _prune_login_cache() -> None:
    now = datetime.now(UTC)
    states_to_remove: list[str] = []

    for state, attempt in _login_cache.items():
        if now >= attempt.expires_at:
            states_to_remove.append(state)

    for state in states_to_remove:
        del _login_cache[state]
