import logging

import authlib.oauth2
from authlib.common.security import generate_token
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi.datastructures import URL
from pydantic import AnyUrl, BaseModel, Field, Secret

log = logging.getLogger(__name__)


class OpenIDDiscovery(BaseModel):
    """https://aboutauth.com/docs/learn/oidc/openid-connect-discovery/"""

    # Required
    issuer: AnyUrl
    authorization_endpoint: AnyUrl
    token_endpoint: AnyUrl
    jwks_uri: AnyUrl
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]

    # Recommended
    userinfo_endpoint: AnyUrl | None = None
    registration_endpoint: AnyUrl | None = None
    scopes_supported: list[str] = Field(default_factory=list)
    claims_supported: list[str] = Field(default_factory=list)

    # Optional, scraped from Keycloak configuration
    end_session_endpoint: AnyUrl | None = None
    frontchannel_logout_supported: bool | None = None
    frontchannel_logout_session_supported: bool | None = None

    check_session_iframe: AnyUrl | None = None
    grant_types_supported: list[str] = Field(default_factory=list)
    code_challenge_methods_supported: list[str] = Field(default_factory=list)

    revocation_endpoint: AnyUrl | None = None
    revocation_endpoint_auth_methods_supported: list[str] = Field(default_factory=list)
    revocation_endpoint_auth_signing_alg_values_supported: list[str] = Field(
        default_factory=list
    )
    backchannel_logout_supported: bool | None = None
    backchannel_logout_session_supported: bool | None = None
    backchannel_token_delivery_modes_supported: list[str] = Field(default_factory=list)
    backchannel_authentication_endpoint: AnyUrl | None = None
    backchannel_authentication_request_signing_alg_values_supported: list[str] = Field(
        default_factory=list
    )

    device_authorization_endpoint: AnyUrl | None = None

    require_pushed_authorization_requests: bool | None = None
    pushed_authorization_request_endpoint: AnyUrl | None = None


class OpenIDProvider(BaseModel):
    client_id: Secret[str]
    client_secret: Secret[str]
    discovery: OpenIDDiscovery


# https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.3.2.2.5
# Derived from Keycloak response
class TokenExchangeResponse(BaseModel):
    access_token: str  # Secret[str]
    expires_in: float | int
    refresh_expires_in: float | int
    refresh_token: str  # Secret[str]
    token_type: str
    id_token: str  # Secret[str]
    scope: str
    expires_at: float | int


class OAuth2Client:
    def __init__(
        self,
        provider: OpenIDProvider,
    ) -> None:
        self.provider = provider

        if "S256" not in self.discovery.code_challenge_methods_supported:
            raise ValueError("Provider does not support 'S256' code challenge method")
        if "authorization_code" not in self.discovery.grant_types_supported:
            raise ValueError(
                "Provider does not support 'authorization_code' grant type"
            )
        if "code" not in self.discovery.response_types_supported:
            raise ValueError("Provider does not support 'code' response type")

        self._client = AsyncOAuth2Client(
            client_id=provider.client_id.get_secret_value(),
            client_secret=provider.client_secret.get_secret_value(),
            scope="openid email profile",
            # Passed to underyling OAuth2Client
            code_challenge_method="S256",
            grant_type="authorization_code",
            response_type="code",
            token_endpoint=str(self.discovery.token_endpoint),
        )

    @property
    def client(self) -> authlib.oauth2.OAuth2Client:
        # HACK: workaround for poor typehinting support in authlib
        return self._client

    @property
    def discovery(self) -> OpenIDDiscovery:
        return self.provider.discovery

    def create_authorization_url(
        self,
        *,
        code_verifier: str,
        nonce: str,
        redirect_uri: str | URL,
    ) -> tuple[str, str]:
        """Create the authorization url and state."""
        log.debug("Creating authorization URL")
        return self.client.create_authorization_url(
            str(self.discovery.authorization_endpoint),
            code_verifier=code_verifier,
            nonce=nonce,
            redirect_uri=str(redirect_uri),
        )

    async def fetch_token(
        self,
        *,
        authorization_response: str,
        code_verifier: str,
        redirect_uri: str | URL,
    ) -> TokenExchangeResponse:
        log.debug("Fetching token from provider")
        response = await self.client.fetch_token(
            authorization_response=authorization_response,
            code_verifier=code_verifier,
            redirect_uri=str(redirect_uri),
        )
        return TokenExchangeResponse.model_validate(response)

    def create_logout_url(
        self,
        *,
        id_token_hint: str,
        post_logout_redirect_uri: str | URL,
    ) -> tuple[str, str]:
        """

        https://openid.net/specs/openid-connect-rpinitiated-1_0.html
        https://docs.authlib.org/en/latest/oauth2/client/web/starlette.html#rp-initiated-logout

        """
        log.debug("Creating logout URL")
        if self.discovery.end_session_endpoint is None:
            raise ValueError("Front-channel logout not supported by provider")

        state = generate_token()
        url = URL(self.discovery.end_session_endpoint.encoded_string())
        url = url.include_query_params(
            id_token_hint=id_token_hint,
            client_id=self.provider.client_id.get_secret_value(),
            post_logout_redirect_uri=post_logout_redirect_uri,
            state=state,
        )
        return str(url), state

    async def refresh_token(self, refresh_token: str) -> TokenExchangeResponse:
        response = await self.client.refresh_token(
            refresh_token=refresh_token,
        )
        return TokenExchangeResponse.model_validate(response)
