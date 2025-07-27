"""Test that we can inject fixtures.

Perform this test first to spot fixture problems early.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from .fixtures import session, user1, user2

# Ignore F811 Parameter name shadows import
# flake8: noqa: F811


@pytest.mark.asyncio
async def test_inject_session(session):
    """We can inject a session object into a test."""
    assert session is not None
    assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_inject_users(user1, user2):
    """We can inject a session object into a test."""
    assert user1 is not None
    assert isinstance(user1, models.User)
    assert user1.id > 0
    assert user1.email is not None
    assert isinstance(user2, models.User)
    assert user2.id > 0
    assert user2.email is not None


def test_inject_async_fixture_in_sync_test(user1):
    """Can we inject an async fixture into non-async test?"""
    assert user1 is not None
    assert isinstance(user1, models.User)
    assert user1.id > 0
