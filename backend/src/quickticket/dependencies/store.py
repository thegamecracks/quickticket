import logging
from typing import TYPE_CHECKING, Annotated, cast

from fastapi import Depends, HTTPException
from fastapi.datastructures import URL
from obstore.store import ObjectStoreMethods, from_url

from quickticket.dependencies.state import SettingsDep, StateDep

if TYPE_CHECKING:
    from obstore.store import S3Config

__all__ = (
    "ObjectStoreDep",
    "Store",
    "get_object_store",
)

log = logging.getLogger(__name__)

type Store = ObjectStoreMethods


async def get_object_store(settings: SettingsDep, state: StateDep) -> Store:
    store = cast(Store | None, getattr(state, "store", None))
    if store is not None:
        return store

    if settings.s3 is None:
        raise HTTPException(500, "S3 is not configured (.env)")

    url = URL(str(settings.s3.url.get_secret_value()))

    # https://developmentseed.org/obstore/latest/api/store/#obstore.store.from_url
    allow_http = False
    if url.scheme in ("s3+http", "s3+https"):
        endpoint = url.replace(scheme=url.scheme.lstrip("s3+"))
        url = url.replace(scheme="s3")
        allow_http = endpoint.scheme == "http"
        config: S3Config = {
            "access_key_id": settings.s3.access_key.get_secret_value(),
            "endpoint": str(endpoint),
            "region": settings.s3.region.get_secret_value(),
            "secret_access_key": settings.s3.secret_key.get_secret_value(),
            "virtual_hosted_style_request": False,  # path-style vs. vhost-style
        }
    elif url.scheme in ("s3", "s3a"):
        config: S3Config = {
            "access_key_id": settings.s3.access_key.get_secret_value(),
            "region": settings.s3.region.get_secret_value(),
            "secret_access_key": settings.s3.secret_key.get_secret_value(),
            "virtual_hosted_style_request": False,  # path-style vs. vhost-style
        }
    elif url.scheme == "gs":
        raise NotImplementedError("GCP store not supported")
    elif url.scheme == "az":
        raise NotImplementedError("Azure store not supported")
    else:
        config = None

    state.store = store = from_url(
        str(url),
        config=config,
        client_options={"allow_http": allow_http},
    )

    # Doesn't support context manager oddly enough
    # await stack.enter_async_context(store)

    log.info("Initialized %s", type(store).__name__)
    return store


ObjectStoreDep = Annotated[Store, Depends(get_object_store)]
