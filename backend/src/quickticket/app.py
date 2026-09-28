from fastapi import FastAPI

from quickticket.dependencies import SettingsDep
from quickticket.routers import auth

app = FastAPI()
app.include_router(auth.router, prefix="/auth")


@app.get("/")
async def root(settings: SettingsDep):
    return {"message": "Hello World"}
