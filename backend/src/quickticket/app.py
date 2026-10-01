import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from securecookies import SecureCookiesMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# from starlette_csrf.middleware import CSRFMiddleware
from quickticket.dependencies.auth import OpenIDProviderDep, OptionalIdTokenDep, OptionalUserDep
from quickticket.dependencies.state import SettingsDep
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


app = FastAPI(
    lifespan=lifespan,
    title="QuickTicket",
    description="",
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

# Middleware in LIFO order; bottom/outermost middleware runs first

# Cookie encryption must be innermost middleware, after other middlewares add their cookies
cookie_secrets = [s.get_secret_value() for s in _settings.security.cookie_encryption_secrets]
if cookie_secrets and cookie_secrets[0] == "Qfw1bmzNtFba8qLxYZzxtEDfgd4P58LCDKiuMezO6lU=":
    log.warning("cookie_encryption_secrets not set, using insecure hardcoded value")
app.add_middleware(
    SecureCookiesMiddleware,
    secrets=cookie_secrets,
    cookie_httponly=True,
    cookie_secure=True,
)

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


@app.exception_handler(ForcedResponse)
def send_forced_response(request: Request, exc: ForcedResponse) -> Response:
    # FIXME: cookies can still be lost if other exceptions are raised
    return exc.response


@app.get("/")
async def root(
    request: Request,
    settings: SettingsDep,
    token: OptionalIdTokenDep,
    provider: OpenIDProviderDep,
    user: OptionalUserDep,
):
    redirect_uri = str(settings.frontend.default_redirect_uri or request.base_url)
    return {
        "auth": {
            "status": "Authenticated" if token is not None else "Not authenticated",
            "login_url": str(request.url_for("oauth_login")),
            "validate_url": str(request.url_for("oauth_validate")),
            "logout_url": str(request.url_for("oauth_logout")),
            "provider": str(provider.discovery.issuer),
            "id_token": token,
        },
        "profile": user and await profile.profile_me(user),
        "settings": {
            "default_redirect_uri": redirect_uri,
            "origins": settings.frontend.origins,
        },
        "docs": {
            "openapi": str(request.url_for("openapi")),
            "swagger_url": str(request.url_for("swagger_ui_html")),
            "redoc_url": str(request.url_for("redoc_html")),
        },
    }
