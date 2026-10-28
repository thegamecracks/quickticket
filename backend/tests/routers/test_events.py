from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.routers.events import EventsRead, get_events
from tests.conftest import DatasetLoader


@pytest.mark.asyncio
async def test_get_events(
    dataset_loader: DatasetLoader,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    await dataset_loader.load()

    async with make_session() as session:
        response = await get_events(user=None, session=session)
        response = EventsRead.model_validate(response, from_attributes=True)

    # TODO: validate full payload? would be noisy with the descriptions though...
    event_ids = (
        UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
        UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
        UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
        UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
        UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
        UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
        UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
        UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
        UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
        UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
    )

    assert len(response.events) == len(event_ids)
    for i, event_id in enumerate(event_ids):
        assert response.events[i].id == event_id
