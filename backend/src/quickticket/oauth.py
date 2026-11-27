import logging

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, Secret

log = logging.getLogger(__name__)


class OpenIDDiscovery(BaseModel):
    """https://aboutauth.com/docs/learn/oidc/openid-connect-discovery/"""

    model_config = ConfigDict(extra="allow")

    # Required
    issuer: AnyUrl
    authorization_endpoint: AnyUrl
    token_endpoint: AnyUrl
    userinfo_endpoint: AnyUrl
    jwks_uri: AnyUrl
    response_types_supported: list[str]
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]

    # Recommended
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
    revocation_endpoint_auth_signing_alg_values_supported: list[str] = Field(default_factory=list)
    backchannel_logout_supported: bool | None = None
    backchannel_logout_session_supported: bool | None = None
    backchannel_token_delivery_modes_supported: list[str] = Field(default_factory=list)
    backchannel_authentication_endpoint: AnyUrl | None = None
    backchannel_authentication_request_signing_alg_values_supported: list[str] = Field(
        default_factory=list,
    )

    device_authorization_endpoint: AnyUrl | None = None

    require_pushed_authorization_requests: bool | None = None
    pushed_authorization_request_endpoint: AnyUrl | None = None


class OpenIDProvider(BaseModel):
    client_id: Secret[str]
    client_secret: Secret[str]
    discovery: OpenIDDiscovery
