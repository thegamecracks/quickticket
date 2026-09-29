from functools import cache
from typing import Annotated

from fastapi import Depends

from quickticket.settings import Settings


@cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
