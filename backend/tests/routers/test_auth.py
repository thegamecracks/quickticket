import hashlib
from base64 import urlsafe_b64encode
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient

from quickticket.dependencies.auth.provider import get_openid_provider
from quickticket.oauth import OpenIDProvider
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


async def test_login_skips_provider_for_authenticated_user(
    client: AsyncClient,
    auth: AuthController,
    openid_provider: OpenIDProvider,
) -> None:
    assert auth.user is not None

    response = await client.post("/api/auth/login")
    assert response.status_code == 303
    assert response.headers["location"] == "https://test/"
    assert set(response.cookies) == set()
