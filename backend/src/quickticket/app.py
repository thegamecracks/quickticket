import importlib.metadata
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import cast

from asynctasq import AsyncTasQIntegration
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi_injectable import register_app
from PIL.Image import DecompressionBombError, UnidentifiedImageError
from securecookies import SecureCookiesMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette_csrf.middleware import CSRFMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from quickticket.dependencies.ratelimits import apply_request_limit
from quickticket.errors import (
    EntityNotFound,
    FileProcessingError,
    ForcedResponse,
    ImageFormatNotAccepted,
    UnauthorizedError,
)
from quickticket.logging import setup_logging
from quickticket.routers import auth, events, notifications, organizations, profile, venues
from quickticket.settings import Settings

__all__ = (
    "app",
    "create_app_from_settings",
)

log = logging.getLogger(__name__)


def create_app_from_settings(settings: Settings) -> FastAPI:
    if settings.log.debug:
        log.warning(
            "Starlette's debug mode is enabled. Disable in production with: BACKEND__LOG__DEBUG=0",
        )

    assert __package__ is not None
    app = FastAPI(
        lifespan=lifespan,
        title="QuickTicket",
        description="",
        version=importlib.metadata.version(__package__),
        dependencies=[
            Depends(apply_request_limit),
            Depends(store_response_object),
        ],
        root_path=settings.root_path,
        debug=settings.log.debug,
        openapi_url=settings.openapi.url,
        docs_url=settings.openapi.swagger_url,
        redoc_url=settings.openapi.redoc_url,
        # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        # set withCredentials to allow cross-origin cookies for OpenID
        swagger_ui_parameters={"withCredentials": True},
    )
    api = APIRouter()
    api.include_router(auth.router, prefix="/auth")
    api.include_router(events.router, prefix="/events")
    api.include_router(notifications.router, prefix="/notifications")
    api.include_router(organizations.router, prefix="/organizations")
    api.include_router(profile.router, prefix="/profile")
    api.include_router(venues.router, prefix="/venues")
    app.include_router(api, prefix="/api")

    if settings.frontend.builtin:
        from quickticket import frontend  # noqa: PLC0415

        log.warning(
            "Serving minimal frontend. Disable in production with: BACKEND__FRONTEND__BUILTIN=0",
        )
        app.mount("/static", frontend.static, name="static")
        app.include_router(frontend.router)

    # Middleware in LIFO order; bottom/outermost middleware runs first
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, compresslevel=1)
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.security.trusted_proxies)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.security.allowed_hosts)

    # TODO: require frontend to send x-csrftoken header from csrftoken cookie
    csrf_secret = settings.security.csrf_secret.get_secret_value()
    if csrf_secret is not None:
        if csrf_secret.startswith("insecure"):
            log.warning("csrf_secret not set, using insecure hardcoded value")
        app.add_middleware(CSRFMiddleware, secret=csrf_secret)

    if settings.log.profiling:
        add_profiling_middleware(app)

    # This preserves headers from FastAPI's temporary response object by transferring
    # them to the current response object. For this to work, it must wrap all other middleware
    # that may return its own response object, like the profiling response above.
    app.add_middleware(BaseHTTPMiddleware, dispatch=preserve_headers)

    # https://securecookies.thearchitector.dev/securecookies.html
    # Cookie encryption must be outermost middleware, after other middlewares add their cookies
    cookie_secrets = [s.get_secret_value() for s in settings.security.cookie_encryption_secrets]
    if cookie_secrets and cookie_secrets[0] == "Qfw1bmzNtFba8qLxYZzxtEDfgd4P58LCDKiuMezO6lU=":
        log.warning("cookie_encryption_secrets not set, using insecure hardcoded value")

    app.add_middleware(
        SecureCookiesMiddleware,
        secrets=cookie_secrets,
        cookie_httponly=True,
        cookie_secure=True,
    )

    app.add_exception_handler(DecompressionBombError, handle_decompression_bomb)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(EntityNotFound, handle_entity_not_found)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(FileProcessingError, handle_file_processing_error)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(ForcedResponse, handle_forced_response)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(ImageFormatNotAccepted, handle_image_format_not_accepted)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(UnauthorizedError, handle_unauthorized_error)  # ty: ignore[invalid-argument-type]
    app.add_exception_handler(UnidentifiedImageError, handle_unidentified_image)  # ty: ignore[invalid-argument-type]

    return app


def app() -> FastAPI:
    settings = Settings()

    # Logging is configured here since this application factory is called by Uvicorn.
    # Tests will call `create_app_from_settings()` directly, where logging may be mocked.
    setup_logging(verbosity=settings.log.verbosity)

    return create_app_from_settings(settings)


# https://github.com/fastapi/fastapi/discussions/8054#discussioncomment-11346542
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await register_app(app)  # fastapi-injectable
    app.state.asynctasq = AsyncTasQIntegration()
    async with AsyncExitStack() as stack:
        app.state.stack = stack
        await stack.enter_async_context(app.state.asynctasq.lifespan(app))
        try:
            yield
        finally:
            del app.state.stack


async def store_response_object(request: Request, response: Response) -> None:
    # HACK:
    # FastAPI creates a temporary response object we can use to set headers,
    # however this response is overwritten if an exception is raised or a
    # Response object is returned. To restore our headers, we need to recover
    # this response object and transfer the headers over to the actual response.
    #
    # We'll use a global dependency to store FastAPI's temporary response in
    # the request, and then extract it further down at the ASGI middleware level.
    request.state.temp_response = response


def add_profiling_middleware(app: FastAPI) -> None:
    try:
        from pyinstrument import Profiler  # noqa: PLC0415
    except ModuleNotFoundError:
        log.warning(
            "Request profiling is unavailable due to pyinstrument not being installed. "
            "Disable in production with: BACKEND__LOG__PROFILING=0",
        )
        return

    log.warning(
        "Enabling request profiling with ?profile=1. "
        "Disable in production with: BACKEND__LOG__PROFILING=0",
    )

    # https://pyinstrument.readthedocs.io/en/latest/guide.html
    @app.middleware("http")
    async def profile_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[object]],
    ) -> object:
        profiling = request.query_params.get("profile", False)
        if not profiling:
            return await call_next(request)

        profiler = Profiler()
        profiler.start()
        await call_next(request)
        profiler.stop()
        return HTMLResponse(profiler.output_html())


async def preserve_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)

    temp_response = cast(Response | None, getattr(request.state, "temp_response", None))
    if temp_response is None:
        # Likely 404 Not Found, FastAPI routing returned before running dependencies
        return response

    if response is temp_response:
        return response

    for k, v in temp_response.headers.items():
        # HACK:
        # If a route returns plain data, FastAPI will automatically transfer
        # headers from the temporary response to the response object.
        # Ideally we'd detect that and skip transferring headers, but the
        # `response is temp_response` condition doesn't handle this.
        #
        # Skip values that were already transferred, but never overwrite distinct
        # values: multi-valued headers like Set-Cookie must be preserved as-is.
        if v not in response.headers.getlist(k):
            response.headers.append(k, v)

    return response


def handle_forced_response(request: Request, exc: ForcedResponse) -> Response:
    return exc.response


# https://fastapi.tiangolo.com/tutorial/handling-errors/#reuse-fastapis-exception-handlers
async def handle_entity_not_found(request: Request, exc: EntityNotFound) -> Response:
    http_exception = HTTPException(status_code=400, detail=str(exc))
    return await http_exception_handler(request, http_exception)


async def handle_file_processing_error(request: Request, exc: FileProcessingError) -> Response:
    http_exception = HTTPException(status_code=400, detail=str(exc))
    return await http_exception_handler(request, http_exception)


async def handle_image_format_not_accepted(
    request: Request,
    exc: ImageFormatNotAccepted,
) -> Response:
    http_exception = HTTPException(status_code=415, detail=str(exc))
    return await http_exception_handler(request, http_exception)


async def handle_unidentified_image(request: Request, exc: UnidentifiedImageError) -> Response:
    log.warning("Rejected unidentified image: %s", exc)
    http_exception = HTTPException(status_code=415, detail="Image format not accepted")
    return await http_exception_handler(request, http_exception)


async def handle_decompression_bomb(request: Request, exc: DecompressionBombError) -> Response:
    log.warning("Rejected decompression bomb: %s", exc)
    http_exception = HTTPException(status_code=400, detail="Image exceeds maximum pixel count")
    return await http_exception_handler(request, http_exception)


async def handle_unauthorized_error(request: Request, exc: UnauthorizedError) -> Response:
    http_exception = HTTPException(status_code=403, detail=str(exc))
    return await http_exception_handler(request, http_exception)
