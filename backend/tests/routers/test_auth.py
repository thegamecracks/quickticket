import hashlib
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient, Response as HTTPResponse
from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.dependencies.auth.provider import get_openid_provider
from quickticket.dependencies.auth.tokens import AccessToken, IdToken, TokenValidator
from quickticket.dependencies.auth.users import get_user
from quickticket.dependencies.state import get_settings
from quickticket.models import OpenIDIdentity, User
from quickticket.oauth import OAuth2Client, OpenIDProvider, TokenExchangeResponse
from quickticket.settings import FrontendSettings, OpenIDSettings, Settings
from tests.conftest import AuthController

DISCOVERY = {
    "issuer": "https://idp.example",
    "authorization_endpoint": "https://idp.example/authorize",
    "token_endpoint": "https://idp.example/token",
    "jwks_uri": "https://idp.example/jwks",
    "end_session_endpoint": "https://idp.example/logout",
    "response_types_supported": ["code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": ["openid", "email", "profile", "offline_access"],
    "grant_types_supported": ["authorization_code"],
    "code_challenge_methods_supported": ["S256"],
}
"""Discovery document for a provider that never needs to be contacted."""


@pytest.fixture
def openid_provider(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> OpenIDProvider:
    """Fake only the network boundary, leaving the OAuth2 client real."""
    provider = OpenIDProvider(
        client_id="test-client",
        client_secret="test-secret",  # noqa: S106
        discovery=DISCOVERY,
    )
    monkeypatch.setitem(app.dependency_overrides, get_openid_provider, lambda: provider)
    return provider


def code_challenge(code_verifier: str) -> str:
    """Return the S256 PKCE challenge for a code verifier."""
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode()


async def test_login_redirects_to_provider(
    client: AsyncClient,
    app: FastAPI,
    auth: AuthController,
    openid_provider: OpenIDProvider,
) -> None:
    auth.user = None

    response = await client.post("/api/auth/login")
    assert response.status_code == 303

    url = urlparse(response.headers["location"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == "https://idp.example/authorize"
    query = parse_qs(url.query)
    assert query["client_id"] == ["test-client"]
    assert query["redirect_uri"] == ["https://test/api/auth/post-login"]
    assert query["code_challenge_method"] == ["S256"]

    # The cached verifier must be the one the challenge commits to.
    state = query["state"][0]
    verifier = await app.state.cache.get(f"oauth-state-{state}")
    assert verifier is not None
    assert code_challenge(verifier) == query["code_challenge"][0]

    # /post-login compares the state and nonce against these cookies.
    assert set(response.cookies) == {
        "oauth-nonce",
        "oauth-state",
        "oauth-post-redirect",
    }


async def test_login_does_not_skip_provider_for_authenticated_user(
    client: AsyncClient,
    auth: AuthController,
) -> None:
    """An authenticated login must still fail when the provider is unreachable.

    These are the expected facts of the underlying dependencies:
    1. OptionalUserDep cannot return a user unless it has a valid access token
    2. TokenValidator cannot return an access token without the provider's JWKs
    3. OpenIDProviderJWKsDep cannot return JWKs unless fetched from the provider (or cached)
    4. OpenIDProviderDep cannot return unless it responds to discovery URL (or cached)

    It is highly improbable to produce an authenticated user with JWKs while the provider is down
    unless the cached responses were poisoned, in which case we have bigger issues.
    """
    assert auth.user is not None

    response = await client.post("/api/auth/login")
    assert response.status_code == 500
    assert response.json() == {"detail": "OpenID is not configured (.env)"}
    assert set(response.cookies) == set()


@dataclass
class FakeTokenValidator:
    """Return canned tokens for the raw strings the fake provider issues."""

    nonce: str

    def parse_access_token(self, raw: str) -> AccessToken:
        return AccessToken.model_validate(
            {
                "header": {"alg": "RS256", "typ": "JWT", "kid": "test"},
                "claims": {
                    "exp": 4102444800,
                    "iat": 1700000000,
                    "iss": "https://idp.example",
                    "sub": "test-sub",
                    "typ": "Bearer",
                    "azp": "test-client",
                    "scope": "openid email profile",
                },
                "raw": raw,
            },
        )

    def parse_id_token(self, raw: str) -> IdToken:
        return IdToken.model_validate(
            {
                "header": {"alg": "RS256", "typ": "JWT", "kid": "test"},
                "claims": {
                    "exp": 4102444800,
                    "iat": 1700000000,
                    "iss": "https://idp.example",
                    "sub": "test-sub",
                    "typ": "ID",
                    "azp": "test-client",
                    "jti": "test-jti",
                    "sid": "test-sid",
                    "auth_time": 1700000000,
                    "aud": "test-client",
                    "at_hash": "test-at-hash",
                    "acr": "1",
                    "email_verified": True,
                    "name": "Test User",
                    "groups": [],
                    "preferred_username": "testuser",
                    "given_name": "Test",
                    "family_name": "User",
                    "email": "new.user@example.com",
                    "nonce": self.nonce,
                },
                "raw": raw,
            },
        )


@pytest.fixture
def auth_settings(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Add the OpenID and frontend settings the login flow requires."""
    base: Settings = app.dependency_overrides[get_settings]()
    settings = base.model_copy(
        update={
            "openid": OpenIDSettings(
                client_id="test-client",
                client_secret="test-secret",  # noqa: S106
                discovery_url="https://idp.example/.well-known/openid-configuration",
            ),
            "frontend": FrontendSettings(
                builtin=False,
                default_redirect_uri="https://test/",
                redirect_uris=[HttpUrl("https://test/*")],
            ),
        },
    )
    monkeypatch.setitem(app.dependency_overrides, get_settings, lambda: settings)
    return settings


async def complete_login(
    client: AsyncClient,
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    auth: AuthController,
) -> HTTPResponse:
    """Run the login redirect and the post-login callback, returning the callback."""
    auth.user = None

    login = await client.post("/api/auth/login")
    assert login.status_code == 303
    query = parse_qs(urlparse(login.headers["location"]).query)

    validator = FakeTokenValidator(nonce=query["nonce"][0])
    monkeypatch.setitem(app.dependency_overrides, TokenValidator, lambda: validator)

    async def fetch_token(self: OAuth2Client, **kwargs: Any) -> TokenExchangeResponse:
        return TokenExchangeResponse(
            access_token="access-token",  # noqa: S106
            expires_in=300,
            refresh_expires_in=1800,
            refresh_token="refresh-token",  # noqa: S106
            token_type="Bearer",  # noqa: S106
            id_token="id-token",  # noqa: S106
            scope="openid email profile",
            expires_at=4102444800,
        )

    monkeypatch.setattr(OAuth2Client, "fetch_token", fetch_token)

    return await client.get("/api/auth/post-login", params={"state": query["state"][0]})


def set_cookie_names(response: HTTPResponse) -> dict[str, str]:
    """Map each Set-Cookie header's name to its Max-Age attribute."""
    return {
        name: morsel["max-age"]
        for header in response.headers.get_list("set-cookie")
        for name, morsel in SimpleCookie(header).items()
    }


async def test_post_login_registers_user(
    client: AsyncClient,
    app: FastAPI,
    auth: AuthController,
    openid_provider: OpenIDProvider,
    auth_settings: Settings,
    make_session: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = await complete_login(client, app, monkeypatch, auth)

    assert response.status_code == 303
    assert response.headers["location"] == "https://test/"

    cookies = set_cookie_names(response)
    assert {"oauth-access-token", "oauth-refresh-token"} <= set(cookies)
    # The flow cookies must not outlive the flow.
    for name in ("oauth-nonce", "oauth-state", "oauth-post-redirect"):
        assert cookies.get(name) == "0", name

    async with make_session.begin() as session:
        user = await session.scalar(select(User).where(User.email == "new.user@example.com"))
        assert user is not None
        assert user.display_name == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"

        identity = await session.scalar(
            select(OpenIDIdentity).where(OpenIDIdentity.user_id == user.id),
        )
        assert identity is not None
        assert identity.issuer == "https://idp.example"
        assert identity.sub == "test-sub"


async def test_profile_returns_registered_user(
    client: AsyncClient,
    app: FastAPI,
    auth: AuthController,
    openid_provider: OpenIDProvider,
    auth_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    login = await complete_login(client, app, monkeypatch, auth)
    assert login.status_code == 303

    # Exercise the real access token -> user resolution.
    monkeypatch.delitem(app.dependency_overrides, get_user, raising=False)

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "testuser"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["email"] == "new.user@example.com"

    client.cookies.clear()
    response = await client.get("/api/profile/@me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
