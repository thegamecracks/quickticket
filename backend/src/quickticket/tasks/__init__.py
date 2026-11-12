import logging

from asynctasq import task
from fastapi_injectable import injectable

from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import Event, EventID

log = logging.getLogger(__name__)


@task
@injectable
async def example_task(x: int) -> int:
    # `task_id = await example_task(123).dispatch()`
    log.debug("example_task(x=%s)", x)
    return x


@task
@injectable
async def example_task_sqlalchemy(
    event_id: EventID,
    session: AsyncSessionDep,
) -> str | None:
    # `task_id = await example_task_sqlalchemy(event.id).dispatch()`

    event = await session.get(Event, event_id)
    if event is None:
        log.debug("Invalid event ID received, ignoring")
        return None

    log.debug("example_task_sqlalchemy(event=%s)", event.id)
    return event.display_name
