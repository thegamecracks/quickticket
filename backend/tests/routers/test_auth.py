from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from pydantic import HttpUrl

from quickticket.dependencies.auth.provider import get_openid_provider
from quickticket.dependencies.auth.tokens import AccessToken
from quickticket.dependencies.state import get_settings
from quickticket.oauth import OpenIDProvider
from quickticket.settings import FrontendSettings, OpenIDSettings, Settings

DISCOVERY = {
    "issuer": "https://idp.example",
    "authorization_endpoint": "https://idp.example/authorize",
    "token_endpoint": "https://idp.example/token",
    "userinfo_endpoint": "https://idp.example/userinfo",
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
    """Fake only the network boundary."""
    provider = OpenIDProvider(
        client_id="test-client",
        client_secret="test-secret",  # noqa: S106
        discovery=DISCOVERY,
    )
    monkeypatch.setitem(app.dependency_overrides, get_openid_provider, lambda: provider)
    return provider


@dataclass
class FakeTokenValidator:
    """Return canned tokens for the raw strings the fake provider issues."""

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


# TODO: test access token registers user
# TODO: test profile returns registered user
