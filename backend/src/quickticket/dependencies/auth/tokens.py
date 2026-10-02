import logging
from dataclasses import dataclass
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import Depends
from joserfc import jwt
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry, Token as _JoseToken
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from quickticket.dependencies.auth.provider import OpenIDProviderDep, OpenIDProviderJWKsDep
from quickticket.dependencies.cache import SettingsDep

__all__ = (
    "AccessToken",
    "IdToken",
    "IdTokenClaims",
    "TokenHeader",
    "TokenValidator",
    "TokenValidatorDep",
    "ValidTokens",
    "get_access_claims_registry",
    "get_id_claims_registry",
)

log = logging.getLogger(__name__)


def get_access_claims_registry(
    settings: SettingsDep,
    provider: OpenIDProviderDep,
) -> JWTClaimsRegistry:
    # https://jose.authlib.org/en/guide/jwt/#validate-claims
    registry = jwt.JWTClaimsRegistry(
        leeway=settings.security.token_leeway,
        iss={"essential": True, "value": str(provider.discovery.issuer)},
        sub={"essential": True},
        aud={"essential": True, "value": provider.client_id.get_secret_value()},
        exp={"essential": True},
        iat={"essential": True},
    )
    return registry


def get_id_claims_registry(
    settings: SettingsDep,
    provider: OpenIDProviderDep,
) -> JWTClaimsRegistry:
    # https://jose.authlib.org/en/guide/jwt/#validate-claims
    registry = jwt.JWTClaimsRegistry(
        leeway=settings.security.token_leeway,
        iss={"essential": True, "value": str(provider.discovery.issuer)},
        sub={"essential": True},
        aud={"essential": True, "value": provider.client_id.get_secret_value()},
        exp={"essential": True},
        iat={"essential": True},
        # Identity
        email={"essential": True},
        email_verified={"essential": True, "value": True},
        name={"essential": True},
        given_name={"essential": True},
        family_name={"essential": True},
        preferred_username={"essential": True},
        groups={"essential": True},
    )
    return registry


class TokenHeader(BaseModel):
    model_config = ConfigDict(extra="allow")

    alg: str
    typ: str
    kid: str


class TokenClaims(BaseModel):
    model_config = ConfigDict(extra="allow")

    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    aud: str
    sub: str
    typ: str
    azp: str
    sid: str


class AccessTokenClaims(TokenClaims):
    scope: str


# CAUTION: provider must support JWT access tokens!
# https://datatracker.ietf.org/doc/html/rfc9068
class AccessToken(BaseModel):
    header: TokenHeader
    claims: AccessTokenClaims
    raw: str


class Address(BaseModel):
    # https://openid.net/specs/openid-connect-core-1_0-final.html#AddressClaim
    formatted: str | None = None
    street_address: str | None = None
    country: str | None = None
    locality: str | None = None
    region: str | None = None
    postal_code: str | None = None


class IdTokenClaims(TokenClaims):
    model_config = ConfigDict(extra="allow")

    # FIXME: likely needs looser validation to support other providers
    at_hash: str
    acr: str
    email_verified: bool
    name: str
    groups: list[str] = Field(default_factory=list)
    preferred_username: str
    given_name: str
    family_name: str
    email: EmailStr
    nonce: str | None = None
    # Optional user profile attributes
    zoneinfo: ZoneInfo | None = None
    website: str | None = None
    resource_access: dict[str, Any] = Field(default_factory=dict)
    address: Address | None = None
    gender: str | None = None
    locale: str | None = None
    picture: str | None = None
    upn: str | None = None
    realm_access: dict[str, Any] = Field(default_factory=dict)
    organization: list[str] = Field(default_factory=list)


class IdToken(BaseModel):
    header: TokenHeader
    claims: IdTokenClaims
    raw: str


def _parse_token(raw: str, keys: KeySet, registry: JWTClaimsRegistry) -> _JoseToken:
    token = jwt.decode(raw, keys)
    registry.validate(token.claims)
    return token


class ValidTokens(BaseModel):
    access_token: AccessToken
    id_token: IdToken


@dataclass(kw_only=True, repr=False)
class TokenValidator:
    access_registry: _AccessRegistryDep
    id_registry: _IdRegistryDep
    keys: OpenIDProviderJWKsDep

    def parse_tokens(self, *, access_token: str, id_token: str) -> ValidTokens:
        return ValidTokens(
            access_token=self._parse_access_token(access_token),
            id_token=self._parse_id_token(id_token),
        )

    def _parse_access_token(self, raw: str) -> AccessToken:
        # Can raise JoseError exceptions:
        # - BadSignatureError
        # - InvalidPayloadError
        # - InvalidClaimError
        # - MissingClaimError
        access_token = jwt.decode(raw, self.keys)
        self.access_registry.validate(access_token.claims)
        return AccessToken(
            header=access_token.header,
            claims=access_token.claims,
            raw=raw,
        )

    def _parse_id_token(self, raw: str) -> IdToken:
        id_token = jwt.decode(raw, self.keys)
        self.id_registry.validate(id_token.claims)
        return IdToken(
            header=id_token.header,
            claims=id_token.claims,
            raw=raw,
        )


_AccessRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_access_claims_registry)]
_IdRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_id_claims_registry)]
TokenValidatorDep = Annotated[TokenValidator, Depends(TokenValidator)]
