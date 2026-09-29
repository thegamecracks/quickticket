import authlib.oauth2
from authlib.integrations.httpx_client import AsyncOAuth2Client
from pydantic import AnyUrl, BaseModel, Field


class OpenIDDiscoveryProvider(BaseModel):
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
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        provider: OpenIDDiscoveryProvider,
    ) -> None:
        if "S256" not in provider.code_challenge_methods_supported:
            raise ValueError("Provider does not support 'S256' code challenge method")
        if "authorization_code" not in provider.grant_types_supported:
            raise ValueError(
                "Provider does not support 'authorization_code' grant type"
            )
        if "code" not in provider.response_types_supported:
            raise ValueError("Provider does not support 'code' response type")

        self._provider = provider
        self._client = AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="openid email profile",
            # Passed to underyling OAuth2Client
            code_challenge_method="S256",
            grant_type="authorization_code",
            response_type="code",
            token_endpoint=str(provider.token_endpoint),
        )

    @property
    def _typed_client(self) -> authlib.oauth2.OAuth2Client:
        # HACK: workaround for poor typehinting support in authlib
        return self._client

    def create_authorization_url(self, code_verifier: str) -> tuple[str, str]:
        """Create the authorization url and state."""
        return self._typed_client.create_authorization_url(
            str(self._provider.authorization_endpoint),
            code_verifier=code_verifier,
        )

    # TODO: parse with pydantic model
    async def fetch_token(
        self, request_uri: str, *, code_verifier: str
    ) -> TokenExchangeResponse:
        response = await self._typed_client.fetch_token(
            authorization_response=request_uri,
            code_verifier=code_verifier,
        )
        return TokenExchangeResponse.model_validate(response)
