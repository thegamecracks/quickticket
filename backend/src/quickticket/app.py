from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from quickticket.dependencies.auth import OptionalIdTokenDep
from quickticket.dependencies.state import SettingsDep
from quickticket.errors import ForcedResponse
from quickticket.logging import setup_logging
from quickticket.routers import auth
from quickticket.settings import Settings

# HACK: bypasses dependency injection
_settings = Settings()


# https://github.com/fastapi/fastapi/discussions/8054#discussioncomment-11346542
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging(verbosity=_settings.log.verbosity)
    async with AsyncExitStack() as stack:
        _app.state.stack = stack
        try:
            yield
        finally:
            del _app.state.stack


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix="/auth")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.frontend.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ForcedResponse)
def send_forced_response(request: Request, exc: ForcedResponse) -> Response:
    # FIXME: cookies can still be lost if other exceptions are raised
    return exc.response


@app.get("/")
async def root(request: Request, settings: SettingsDep, token: OptionalIdTokenDep):
    redirect_uri = str(settings.frontend.default_redirect_uri or request.base_url)
    return {
        "auth": {
            "status": "Authenticated" if token is not None else "Not authenticated",
            "login_url": str(request.url_for("oauth_login")),
            "validate_url": str(request.url_for("oauth_validate")),
            "logout_url": str(request.url_for("oauth_logout")),
            "id_token": token,
        },
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
