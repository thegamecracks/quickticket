from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from quickticket.dependencies import SettingsDep
from quickticket.routers import auth


# https://github.com/fastapi/fastapi/discussions/8054#discussioncomment-11346542
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        _app.state.stack = stack
        try:
            yield
        finally:
            del _app.state.stack


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router, prefix="/auth")


@app.get("/")
async def root(settings: SettingsDep):
    return {"message": "Hello World"}
