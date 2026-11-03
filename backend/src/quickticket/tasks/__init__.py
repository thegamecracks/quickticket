import logging
from uuid import UUID

from asynctasq import task

from quickticket.models import Event
from quickticket.worker import get_async_sessionmaker

log = logging.getLogger(__name__)


@task
async def example_task(x: int) -> int:
    # `task_id = await example_task(123).dispatch()`
    log.debug("example_task(x=%s)", x)
    return x


@task
async def example_task_sqlalchemy(event_id: UUID) -> str | None:
    # `task_id = await example_task_sqlalchemy(event.id).dispatch()`

    # Creating a session manually (note function import from quickticket.worker)
    async with get_async_sessionmaker().begin() as session:
        event = await session.get(Event, event_id)

    if event is None:
        log.debug("Invalid event ID received, ignoring")
        return

    log.debug("example_task_sqlalchemy(event=%s)", event.id)
    return event.display_name
