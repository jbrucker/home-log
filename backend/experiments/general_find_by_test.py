"""Tests of the data_source_dao."""

import asyncio
from datetime import datetime, timezone
from app import models, schemas
from app.data_access import data_source_dao as dao
from app.core.database import db


async def create_user(session, username, email) -> models.User:
    """Fixture to inject a persisted User model."""
    user = models.User(username=username, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_data_sources(howmany: int, owner: models.User) -> list[int]:
    """Create some data sources and persist them.

       :returns: list of id's of the created data sources
    """
    # Some interesting names
    NAMES = ["Electric Meter {:02d}", "Sensor No. {}", "Car A{:04d}", "PWA #{:06d}"]
    # specify custom creation dates
    year = 2024
    month = 3  # 3 is March
    day = 1
    created_ids = []
    async for session in db.get_session():
        for n in range(1, howmany + 1):
            ds_create = schemas.DataSourceCreate(
                name=NAMES[n % len(NAMES)].format(n),
                description=f"The #{n} choice for data",
                owner_id=owner.id,
                unit=f"unit{n}"
                )
            ds = models.DataSource(**ds_create.model_dump())
            ds.created_at = datetime(year, month, day, tzinfo=timezone.utc)
            day += 1
            session.add(ds)
            await session.commit()
            await session.refresh(ds)
            created_ids.append(ds.id)
    return created_ids


async def run_get_data_sources_by_date(session, user1, user2):
    """Can use an expression to select datasources by owner and date range."""
    user1_ds_ids = await create_data_sources(20, user1)
    user2_ds_ids = await create_data_sources(20, user2)

    # Get all their data sources
    user1_ds = await dao.find(session, owner_id=user1.id)
    user2_ds = await dao.find(session, owner_id=user2.id)
    assert user1_ds_ids == [ds.id for ds in user1_ds]
    assert user2_ds_ids == [ds.id for ds in user2_ds]
    assert len(user1_ds) == 20

    # Date range we will query for:
    year = 2024
    month = 3  # 3 is March
    start_date = datetime(year, month, 7, tzinfo=timezone.utc)
    end_date = datetime(year, month, 10, tzinfo=timezone.utc)

    print("Data sources for", user1)
    result = await dao.find(session, owner_id=user1.id)
    print_results(result)

    input(f"All DS created between {start_date:%d-%m-%Y} and {end_date:%d-%m-%Y}...")
    # The test:
    result = await dao.find(session,
                            models.DataSource.created_at >= start_date,
                            models.DataSource.created_at <= end_date
                            )
    print_results(result)

    end_date = datetime(year, month, 4, tzinfo=timezone.utc)
    input(f"DS owned by {user2} and created before {end_date:%d-%m-%Y}...")
    result = await dao.find(session,
                            models.DataSource.created_at <= end_date,
                            owner_id=user2.id
                            )
    print_results(result)

    input(f"Cars owned by {user2}...")
    result = await dao.find(session,
                            models.DataSource.name.contains("Car"),
                            owner_id=user2.id
                            )
    print_results(result)


def print_results(result):
    """Print them, of course."""
    for ds in result:
        print(ds)
    print()


async def main():
    """Make some users so we can find them in tests."""
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    db.create_engine(TEST_DATABASE_URL)
    await db.create_tables()
    async for session in db.get_session():
        user1 = await create_user(session, "Lord of DAO", "lordofdao@generic.org")
        user2 = await create_user(session, "Imperial User", "trump@narcists.com")
        await run_get_data_sources_by_date(session, user1, user2)

if __name__ == '__main__':
    asyncio.run(main())
