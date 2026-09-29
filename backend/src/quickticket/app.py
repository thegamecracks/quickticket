from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, Request

from quickticket.logging import LogVerbosity, setup_logging
from quickticket.routers import auth


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


@app.get("/")
async def root(request: Request):
    return {
        "openapi": str(request.url_for("openapi")),
        "swagger_url": str(request.url_for("swagger_ui_html")),
        "redoc_url": str(request.url_for("redoc_html")),
        "login_url": str(request.url_for("oauth_login")),
        "validate_url": str(request.url_for("oauth_validate")),
        "logout_url": str(request.url_for("oauth_logout")),
    }
