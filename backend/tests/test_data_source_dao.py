"""Tests of the data_source_dao"""

from datetime import datetime, timezone
import logging
import pytest, pytest_asyncio
from app import models, schemas
from app.data_access import data_source_dao as dao
from .utils import as_utc_time
from .fixtures import db, session


logger = logging.getLogger(__name__)

#def pytest_runtest_logreport(report):
#    if report.when == "call":
#        logger.info(f"Test function: {report.nodeid} - {report.outcome}")

@pytest_asyncio.fixture()
async def user1(session) -> models.User:
    """Fixture to inject a persisted User model"""
    user = models.User(username="User 1", email="user1@mydomain.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture()
async def user2(session) -> models.User:
    """Fixture to inject a *different* persisted User model"""
    user = models.User(username="User 2", email="user2@mydomain.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture()
async def ds_data() -> schemas.DataSourceCreate:
    """Fixture to inject a schema object with data for a new DataSource."""
    ds_create = schemas.DataSourceCreate(
        name="Test Source",
        description="A test data source",
        # no owner_id yet
        unit="test unit"
    )
    return ds_create

async def create_data_sources(howmany: int, owner: models.User) -> list[int]:
    """Create some data sources and persist them.
    
       :returns: list of id's of the created data sources
    """
    created_ids = []
    async for session in db.get_session():
        for n in range(1, howmany+1):
            ds_create = schemas.DataSourceCreate(
                name = f"Data Source {n}",
                description = f"The #{n} choice for data",
                owner_id = owner.id,
                unit=f"unit{n}")
            ds = models.DataSource(**ds_create.model_dump())
            session.add(ds)
            await session.commit()
            await session.refresh(ds)
            created_ids.append(ds.id)
    return created_ids


@pytest.mark.asyncio
async def test_create_data_source(session, ds_data, user1):
    """Can create and persist a DataSource with a given owner (user1)."""
    # Create a DataSourceCreate schema with required fields
    ds_data.owner_id = user1.id
    # Call the DAO to create the data source
    starting_time = datetime.now(timezone.utc)
    ds = await dao.create_data_source(session, ds_data)
    assert isinstance(ds, models.DataSource)
    assert ds.id is not None
    assert ds.owner_id == user1.id
    assert ds.name == "Test Source"
    assert ds.description == "A test data source"
    assert ds.unit == "test unit"
    # automatically assigned
    # Cludge: SQLite datetime is not timezone aware
    assert as_utc_time(ds.created_at) >= starting_time
    assert ds.is_public == False  # the default


@pytest.mark.asyncio
async def test_get_data_source_by_id(session, ds_data, user1):
    """Can retrieve a data source by id."""
    ids = await create_data_sources(5, user1)
    ds_data.owner_id = user1.id
    # Call the DAO to create the data source
    ds = await dao.create_data_source(session, ds_data)
    # create a few more
    await create_data_sources(4, user1)
    # fetch a particular one
    result = await dao.get_data_source_by_id(session, ds.id)
    assert result is not None
    assert result.id == ds.id
    assert result.name == ds_data.name

@pytest.mark.asyncio
async def test_get_data_source_by_id_includes_owner(session, ds_data, user1):
    """When you get a data source it includes the owner reference as a User model."""
    ds_data.owner_id = user1.id
    # Call the DAO to create the data source
    ds = await dao.create_data_source(session, ds_data)
    # fetch a particular one
    result = await dao.get_data_source_by_id(session, ds.id)
    assert isinstance(result.owner, models.User)
    assert result.owner.email == user1.email

@pytest.mark.asyncio
async def test_get_data_source_by_id_not_found(session, user1):
    # initially no DataSources in persistence
    result = await dao.get_data_source_by_id(session, 99999)
    assert result is None
    ids = await create_data_sources(10, user1)
    result = await dao.get_data_source_by_id(session, 99999)
    assert result is None

@pytest.mark.asyncio
async def test_get_data_source_by_owner(session, user1, user2):
    """Can get all data sources for a given owner."""
    ds1 = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="Owner1 Source1",
            description="Owned by user1",
            owner_id=user1.id
        )
    )
    ds2 = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="Owner1 Source2",
            description="Owned by user1",
            owner_id=user1.id
        )
    )
    ds3 = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="Owner2 Source1",
            description="Owned by user2",
            owner_id=user2.id
        )
    )
    user1_sources = await dao.get_data_sources_by_owner(session, user1)
    user2_sources = await dao.get_data_sources_by_owner(session, user2.id)
    assert len(user1_sources) == 2
    assert all(ds.owner_id == user1.id for ds in user1_sources)
    assert len(user2_sources) == 1
    assert user2_sources[0].owner_id == user2.id

@pytest.mark.asyncio
async def test_get_data_source_for_owner_with_none(session, user1, user2):
    """If a user does not own any data sources, it returns None."""
    ds1 = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="Owner1 Source1",
            description="Owned by user1",
            owner_id=user1.id
        )
    )
    ds2 = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="Owner1 Source2",
            description="Owned by user1",
            owner_id=user1.id
        )
    )
    user2_sources = await dao.get_data_sources_by_owner(session, user2.id)
    assert isinstance(user2_sources, list)
    assert len(user2_sources) == 0


@pytest.mark.asyncio
async def test_get_data_sources_by_date(session, user1, user2):
    """Can use an expression to select datasources by owner and date range."""
    user1_ds_ids = await create_data_sources(20, user1)
    user2_ds_ids = await create_data_sources(20, user2)
    # revise the creation dates
    year = 2024
    month = 3  # 3 is March
    day = 1
    # Get all their data sources
    user1_ds = await dao.get_data_sources_by(session, owner_id=user1.id)
    user2_ds = await dao.get_data_sources_by(session, owner_id=user2.id)
    assert user1_ds_ids == [ds.id for ds in user1_ds]
    assert user2_ds_ids == [ds.id for ds in user2_ds]
    assert len(user1_ds) == 20

    # DataSources ids that will match our query
    matching_ds = []
    # Date range we will query for:
    start_date = datetime(year, month, 7, tzinfo=timezone.utc)
    end_date = datetime(year, month, 10, tzinfo=timezone.utc)
    for ds1, ds2 in zip(user1_ds, user2_ds):
        # a new creation date
        create_date = datetime(year, month, day, tzinfo=timezone.utc)
        if start_date <= create_date <= end_date:
            matching_ds.append(ds1.id)
        # revise the create date
        ds1.created_at = create_date
        ds2.created_at = create_date
        session.add(ds1)
        session.add(ds2)
        day += 1
    await session.commit()
    # The test:
    result = await dao.get_data_sources_by(session,
                                           models.DataSource.created_at >= start_date,
                                           models.DataSource.created_at <= end_date,
                                           owner_id=user1.id
                                           )
    logger.info("DataSource matching the dates")
    for ds in result:
        logger.info(f"Matched: id={ds.id} {ds.name} owner={ds.owner_id}")
    assert matching_ds == [ds.id for ds in result]


@pytest.mark.asyncio
async def test_update_data_source(session, user1):
    ds = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="To Update",
            description="Before update",
            owner_id=user1.id
            # no unit
        )
    )
    ds_id = ds.id
    update_data = schemas.DataSourceCreate(
        name="Updated Name",
        description="After update",
        # owner_id=user1.id,
        unit="grams"
    )
    # TODO What _should_ happen to attributes that are unspecified in the update?
    updated = await dao.update_data_source(session, ds.id, update_data)
    assert updated.id == ds_id
    assert updated.name == "Updated Name"
    assert updated.description == "After update"
    assert updated.unit == "grams", "update did not set the unit"
    assert updated.owner_id == user1.id, "update changed owner_id which was unspecified in update"

@pytest.mark.asyncio
async def test_update_nonexistent_data_source(session):
    update_data = schemas.DataSourceCreate(
        name="Doesn't Matter",
        description="No such source",
        owner_id=1
    )
    with pytest.raises(ValueError):
        await dao.update_data_source(session, 99999, update_data)

@pytest.mark.asyncio
async def test_delete_data_source(session, user1):
    """Can delete a data source by id"""
    await create_data_sources(5, user1)  # for obfuscation
    ds = await dao.create_data_source(
        session,
        schemas.DataSourceCreate(
            name="To Delete",
            description="Delete me",
            owner_id=user1.id,
            unit="bytes"
        )
    )
    ds_id = ds.id
    # add some more for obfuscation
    await create_data_sources(15, user1)
    deleted = await dao.delete_data_source(session, ds_id)
    assert deleted is not None
    #assert deleted.id == ds.id
    # Should not be found anymore
    result = await dao.get_data_source_by_id(session, ds_id)
    assert result is None

@pytest.mark.asyncio
async def test_delete_nonexistent_data_source(session):
    """Deleting a datasource with non-existing id returns None."""
    deleted = await dao.delete_data_source(session, 999999)
    assert deleted is None