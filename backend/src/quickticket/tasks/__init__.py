import logging

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
async def example_task_sqlalchemy(event: Event) -> Event:
    # `task_id = await example_task_sqlalchemy(event).dispatch()
    log.debug("%r", event)
    log.debug("example_task_sqlalchemy(event=%s)", event.id)

    # Creating a session manually (note function import from quickticket.worker)
    async with get_async_sessionmaker().begin() as session:
        await session.refresh(event)

    return event
