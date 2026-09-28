# https://fastapi.tiangolo.com/advanced/settings/
from typing import Literal

from pydantic import Secret
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    smtp_host: str
    smtp_port: str
    smtp_tls: Literal["none", "implicit", "explicit"]
    smtp_from: str
    smtp_username: str
    smtp_password: Secret[str]
