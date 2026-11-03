import logging

from asynctasq import task

log = logging.getLogger(__name__)


@task
async def example_task(x: int) -> int:
    # `task_id = await example_task(123).dispatch()`
    log.debug("Hello world!")
    return x
