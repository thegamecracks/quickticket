import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from quickticket.dependencies.auth import RequiredAccessTokenDep
from quickticket.dependencies.state import SettingsDep

router = APIRouter(tags=["Authentication"])
log = logging.getLogger(__name__)


# TODO: add discovery redirect so frontend can configure itself


@router.get("/validate", deprecated=True)
async def oauth_validate(settings: SettingsDep, access_token: RequiredAccessTokenDep) -> Any:
    """Verify authentication and return the decoded access token."""
    if not settings.frontend.builtin:
        raise HTTPException(404)
    return {"access_token": access_token}
