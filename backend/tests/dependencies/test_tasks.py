from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from asynctasq import AsyncTasQIntegration, task
from fastapi import FastAPI


@pytest.mark.asyncio
async def test_asynctasq_mock_dispatcher(asynctasq_dispatcher: AsyncMock) -> None:
    @task
    async def my_task(x: int) -> None: ...

    task_id = await my_task(123).dispatch()
    assert task_id == "task-id-123"

    asynctasq_dispatcher.dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_asynctasq_mock_integration(
    app: FastAPI,
    asynctasq_dispatcher: AsyncMock,
    asynctasq_driver: MagicMock,
) -> None:
    asynctasq_driver.connect.assert_called_once()

    integration = cast(AsyncTasQIntegration, app.state.asynctasq)
    assert integration.get_dispatcher() is asynctasq_dispatcher
    assert integration.get_driver() is asynctasq_driver

    await test_asynctasq_mock_dispatcher(asynctasq_dispatcher)
