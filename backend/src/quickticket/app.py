import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import cast

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from securecookies import SecureCookiesMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from quickticket.dependencies.ratelimits import apply_request_limit

# from starlette_csrf.middleware import CSRFMiddleware
from quickticket.errors import ForcedResponse
from quickticket.logging import setup_logging
from quickticket.routers import auth, events, notifications, organizations, profile, venues
from quickticket.settings import Settings

# HACK: bypasses dependency injection
_settings = Settings()
setup_logging(verbosity=_settings.log.verbosity)
log = logging.getLogger(__name__)


# https://github.com/fastapi/fastapi/discussions/8054#discussioncomment-11346542
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        _app.state.stack = stack
        try:
            yield
        finally:
            del _app.state.stack


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


if _settings.log.debug:
    log.warning(
        "Starlette's debug mode is enabled. Disable in production with: BACKEND__LOG__DEBUG=0"
    )

app = FastAPI(
    lifespan=lifespan,
    title="QuickTicket",
    description="",
    dependencies=[
        # FIXME: replace with middleware, FastAPI routes and exception handlers override headers
        Depends(apply_request_limit),
        Depends(store_response_object),
    ],
    root_path=_settings.root_path,
    debug=_settings.log.debug,
    openapi_url=_settings.openapi.url,
    docs_url=_settings.openapi.swagger_url,
    redoc_url=_settings.openapi.redoc_url,
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

if _settings.frontend.builtin:
    from quickticket import frontend

    log.warning(
        "Serving minimal frontend. Disable in production with: BACKEND__FRONTEND__BUILTIN=0"
    )
    app.mount("/static", frontend.static, name="static")
    app.include_router(frontend.router)

# Middleware in LIFO order; bottom/outermost middleware runs first
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.frontend.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, compresslevel=1)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=_settings.security.trusted_proxies)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_settings.security.allowed_hosts)

# TODO: require frontend to send x-csrftoken header from csrftoken cookie
# csrf_secret = _settings.security.csrf_secret.get_secret_value()
# if csrf_secret.startswith("insecure"):
#     log.warning("csrf_secret not set, using insecure hardcoded value")
# app.add_middleware(CSRFMiddleware, secret=csrf_secret)


def add_profiling_middleware() -> None:
    try:
        from pyinstrument import Profiler
    except ModuleNotFoundError:
        log.warning(
            "Request profiling is unavailable due to pyinstrument not being installed. "
            "Disable in production with: BACKEND__LOG__PROFILING=0"
        )
        return

    log.warning(
        "Enabling request profiling with ?profile=1. "
        "Disable in production with: BACKEND__LOG__PROFILING=0"
    )

    # https://pyinstrument.readthedocs.io/en/latest/guide.html
    @app.middleware("http")
    async def profile_request(request: Request, call_next):
        profiling = request.query_params.get("profile", False)
        if not profiling:
            return await call_next(request)

        profiler = Profiler()
        profiler.start()
        await call_next(request)
        profiler.stop()
        return HTMLResponse(profiler.output_html())


if _settings.log.profiling:
    add_profiling_middleware()


# This preserves headers from FastAPI's temporary response object by transferring
# them to the current response object. For this to work, it must wrap all other middleware
# that may return its own response object, like the profiling response above.
@app.middleware("http")
async def preserve_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    response = await call_next(request)

    temp_response = cast(Response | None, getattr(request.state, "temp_response", None))
    if temp_response is None:
        # Likely 404 Not Found, FastAPI routing returned before running dependencies
        return response

    if response is temp_response:
        return response

    for k, v in temp_response.headers.items():
        response.headers.append(k, v)
        # log.debug("Adding %s header #%s: %s", k, len(response.headers.getlist(k)), v)

    return response


# https://securecookies.thearchitector.dev/securecookies.html
# Cookie encryption must be outermost middleware, after other middlewares add their cookies
cookie_secrets = [s.get_secret_value() for s in _settings.security.cookie_encryption_secrets]
if cookie_secrets and cookie_secrets[0] == "Qfw1bmzNtFba8qLxYZzxtEDfgd4P58LCDKiuMezO6lU=":
    log.warning("cookie_encryption_secrets not set, using insecure hardcoded value")

app.add_middleware(
    SecureCookiesMiddleware,
    secrets=cookie_secrets,
    cookie_httponly=True,
    cookie_secure=True,
)


@app.exception_handler(ForcedResponse)
def send_forced_response(request: Request, exc: ForcedResponse) -> Response:
    return exc.response
