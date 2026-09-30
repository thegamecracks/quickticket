import logging

from fastapi import APIRouter, WebSocket

router = APIRouter(tags=["Notifications"])
log = logging.getLogger(__name__)


# https://fastapi.tiangolo.com/advanced/websockets/
# Could use Server Sent Events, but the user will need to acknowledge notifications
# so duplex communication is required
@router.websocket("/")
async def notification_ws(websocket: WebSocket) -> None:
    """Start a websocket for notification streaming."""
