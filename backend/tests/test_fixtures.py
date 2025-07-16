"""Test that we can get the database fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from .fixtures import session


@pytest.mark.asyncio
async def test_inject_session(session):
    assert session is not None
    assert isinstance(session, AsyncSession)

