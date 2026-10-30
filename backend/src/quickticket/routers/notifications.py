import logging

from fastapi import APIRouter, WebSocket

from quickticket.dependencies.auth import OptionalUserDep

router = APIRouter(tags=["Notifications"])
log = logging.getLogger(__name__)


# https://fastapi.tiangolo.com/advanced/websockets/
# Could use Server Sent Events, but the user will need to acknowledge notifications
# so duplex communication is required
@router.websocket("")
async def notification_ws(user: OptionalUserDep, websocket: WebSocket) -> None:
    """Start a websocket for notification streaming."""
