import logging
from datetime import timedelta
from typing import Annotated, Any, NoReturn
from urllib.parse import quote

from fastapi import Depends, HTTPException
from joserfc.jwk import KeySet
from pydantic_core import from_json

from quickticket.dependencies.cache import CacheDep, SettingsDep
from quickticket.dependencies.state import HTTPClientDep
from quickticket.oauth import OAuth2Client, OpenIDProvider

__all__ = (
    "OAuth2ClientDep",
    "OpenIDProviderDep",
    "OpenIDProviderJWKsDep",
    "get_oauth_client",
    "get_openid_provider",
    "get_openid_provider_jwks",
)

_CACHE_ERROR_PREFIX = "ERROR"
log = logging.getLogger(__name__)


async def _cache_get_with_error(cache: CacheDep, key: str) -> Any | None:
    ret = await cache.get(key)
    if ret is not None and ret.startswith(_CACHE_ERROR_PREFIX):
        raise HTTPException(500, ret)
    return ret


async def _cache_mark_failed(cache: CacheDep, key: str, message: str) -> NoReturn:
    expiry = timedelta(minutes=1)
    message = f"{_CACHE_ERROR_PREFIX}: {message} (can retry in: {expiry})".rstrip()
    log.warning("Storing error in cache [%s]: %s", key, message)
    await cache.set(key, message, expiry=expiry)
    raise HTTPException(500, message)


def _get_discovery_cache_key(settings: SettingsDep) -> str:
    # Prevents reusing cached responses when changing between providers
    if settings.openid is None:
        raise HTTPException(500, "OpenID is not configured")

    discovery_url = quote(str(settings.openid.discovery_url), "")
    return f"openid/{discovery_url}"


async def get_openid_provider(
    http: HTTPClientDep,
    cache: CacheDep,
    cache_key: _OpenIDCacheKeyDep,
    settings: SettingsDep,
) -> OpenIDProvider:
    async def fail(message: str = "") -> NoReturn:
        message = f"OpenID discovery is misconfigured ({message})"
        await _cache_mark_failed(cache, discovery_key, message)

    async def parse_provider(data: str) -> OpenIDProvider:
        assert settings.openid is not None

        id, secret = settings.openid.client_id, settings.openid.client_secret
        try:
            data = from_json(data)
            return OpenIDProvider(client_id=id, client_secret=secret, discovery=data)
        except ValueError as e:
            log.error("Cannot parse provider", exc_info=e)
            return await fail("malformed response")

    if settings.openid is None:
        raise HTTPException(500, "OpenID is not configured")

    discovery_key = f"{cache_key}/discovery"
    cached = await _cache_get_with_error(cache, discovery_key)
    if cached is not None:
        return await parse_provider(cached)

    log.info("Fetching discovery URL from OpenID provider")
    response = await http.get(str(settings.openid.discovery_url))
    if not response.is_success:
        await fail(f"HTTP {response.status_code}")

    provider = await parse_provider(response.text)
    await cache.set(discovery_key, response.text, expiry=timedelta(hours=1))
    return provider


async def get_openid_provider_jwks(
    cache: CacheDep,
    cache_key: _OpenIDCacheKeyDep,
    http: HTTPClientDep,
    provider: OpenIDProviderDep,
) -> KeySet:
    async def fail(message: str = "") -> NoReturn:
        message = f"OpenID JWKs are misconfigured ({message})"
        await _cache_mark_failed(cache, jwks_key, message)

    async def parse_key_set(data: str) -> KeySet:
        try:
            return KeySet.import_key_set(from_json(data))
        except ValueError as e:
            log.error("Cannot parse JWKs", exc_info=e)
            await fail("malformed response")

    jwks_key = f"{cache_key}/jwks"
    cached = await _cache_get_with_error(cache, jwks_key)
    if cached is not None:
        return await parse_key_set(cached)

    log.info("Fetching JWKs from OpenID provider")
    response = await http.get(str(provider.discovery.jwks_uri))
    if not response.is_success:
        await fail(f"HTTP {response.status_code}")

    keys = await parse_key_set(response.text)
    await cache.set(jwks_key, response.text, expiry=timedelta(hours=1))
    return keys


def get_oauth_client(provider: OpenIDProviderDep) -> OAuth2Client:
    return OAuth2Client(provider)


_OpenIDCacheKeyDep = Annotated[str, Depends(_get_discovery_cache_key)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
