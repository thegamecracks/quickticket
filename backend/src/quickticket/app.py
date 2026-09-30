from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from quickticket.dependencies import SettingsDep
from quickticket.logging import LogVerbosity, setup_logging
from quickticket.routers import auth
from quickticket.settings import Settings


# https://github.com/fastapi/fastapi/discussions/8054#discussioncomment-11346542
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging(verbose=LogVerbosity.PACKAGE_DEBUG)  # TODO: add setting for verbosity
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
    allow_origins=Settings().frontend.origins,  # HACK: bypasses dependency injection
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root(request: Request, settings: SettingsDep):
    return {
        "openapi": str(request.url_for("openapi")),
        "swagger_url": str(request.url_for("swagger_ui_html")),
        "redoc_url": str(request.url_for("redoc_html")),
        "login_url": str(request.url_for("oauth_login")),
        "validate_url": str(request.url_for("oauth_validate")),
        "logout_url": str(request.url_for("oauth_logout")),
        "default_redirect_uri": settings.frontend.default_redirect_uri,
        "origins": settings.frontend.origins,
    }
