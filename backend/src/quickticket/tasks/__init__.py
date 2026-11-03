import logging

from asynctasq import task

from quickticket.models import Event

log = logging.getLogger(__name__)


@task
async def example_task(x: int) -> int:
    # `task_id = await example_task(123).dispatch()`
    log.debug("example_task(x=%s)", x)
    return x


@task
async def example_task_sqlalchemy(event: Event) -> Event:
    # `task_id = await example_task_sqlalchemy(event).dispatch()`
    # FIXME: allow injecting async sessionmaker from cli.py
    # FIXME: add custom serialization hooks for Money and Point types
    #        https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/src/asynctasq/serializers/hooks/__init__.py
    log.debug("example_task_sqlalchemy(event=%s)", event.id)
    return event
