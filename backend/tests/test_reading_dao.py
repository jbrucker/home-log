"""Tests of the reading_dao"""

import asyncio
from datetime import datetime, timezone
import logging
import random
from pydantic import ValidationError
import pytest, pytest_asyncio
from app import models, schemas
from app.data_access import reading_dao as dao
from .utils import as_utc_time
from .fixtures import db, session, ds1, ds2, user1, user2

# flake8: noqa: E251
# flake8: noqa: F811 Parameter name shadows import

logger = logging.getLogger(__name__)

#def pytest_runtest_logreport(report):
#    if report.when == "call":
#        logger.info(f"Test function: {report.nodeid} - {report.outcome}")


async def create_readings(howmany: int, ds: models.DataSource, value=None) -> list[int]:
    """Create some readings and persist them.

       :param ds: the DataSource for the readings
       :param value: a constant value for all readings. If None then random values are assigned.
       :returns: list of id's of the created readings
    """
    created_ids = []
    components = ds.components()
    def make_value():
        if value: return value
        return random.randint(0,100)
    async for session in db.get_session():
        for n in range(1, howmany+1):
            # dict of "measurement_name: unit" 
            values = {key: make_value() for key in components}
            reading_create = schemas.ReadingCreate(
                name=f"Reading {n}",
                data_source_id=ds.id,
                values=values
                )
            reading = models.Reading(**reading_create.model_dump())
            session.add(reading)
            await session.commit()
            await session.refresh(reading)
            created_ids.append(reading.id)
    return created_ids


@pytest.mark.asyncio
async def test_create_reading(session, ds1: models.DataSource, user1: models.User):
    """Can create and persist a Reading with a given owner (user1)."""
    value_names = ds1.components()
    # Create a Reading schema with required fields
    data = schemas.ReadingCreate(data_source_id=ds1.id, 
                                 created_by_id=user1.id,
                                 values={name: 0.5 for name in value_names}
                                 )
    # Call the DAO to create the reading
    starting_time = datetime.now(timezone.utc)
    reading = await dao.create(session, data)
    assert isinstance(reading, models.Reading)
    assert reading.id is not None
    assert reading.data_source_id == ds1.id
    assert all(reading.values[name] == 0.5 for name in value_names)
    # timestamp is automatically assigned
    assert reading.timestamp is not None
    # Cludge: SQLite datetime is not timezone aware
    assert as_utc_time(reading.timestamp) >= starting_time


@pytest.mark.asyncio
async def test_cannot_create_reading_with_missing_data_values(
            session, ds2: models.DataSource, user2: models.User):
    """Cannot create and persist a reading missing some value names declared by DataSource."""
    value_names = ds2.components()
    # Delete one
    del value_names[-1]
    values = {name: 1.0 for name in value_names}
    # Create a Reading schema with required fields
    data = schemas.ReadingCreate(data_source_id=ds2.id, 
                                 created_by_id=user2.id,
                                 values=values
                                 )
    with pytest.raises(ValueError):
        reading = await dao.create(session, data)
        assert reading is None


@pytest.mark.asyncio
async def test_cannot_create_reading_with_wrong_components(
            session, ds2: models.DataSource, user2: models.User):
    """Cannot create and persist a reading with extra value names not declared by DataSource."""
    value_names = ds2.components()
    values = {name: 1.0 for name in value_names}
    # Bogus reading data
    bad_name = "NOT_" + value_names[0]
    values[bad_name] = 0.0
    # Create a Reading schema with required fields
    data = schemas.ReadingCreate(data_source_id=ds2.id, 
                                 created_by_id=user2.id,
                                 values=values
                                 )
    with pytest.raises(ValueError):
        reading = await dao.create(session, data)
        assert reading is None


@pytest.mark.asyncio
async def test_cannot_create_reading_for_nonexistant_source(
            session, ds1: models.DataSource, user1: models.User):
    """Cannot create and persist a reading for a source that doesn't exist."""
    ds_id = ds1.id + 9
    value_names = ds1.components()
    # Create a Reading schema with required fields
    data = schemas.ReadingCreate(data_source_id=ds_id,  # should not exist 
                                 created_by_id=user1.id,
                                 values={name: 0.5 for name in value_names}
                                 )
    with pytest.raises(ValueError):
        reading = await dao.create(session, data)
        assert reading is None


@pytest.mark.asyncio
async def test_get_reading_by_id(session, ds1: models.DataSource):
    """Can retrieve a reading by id."""
    ids = await create_readings(5, ds1)
    # fetch a particular one
    result = await dao.get(session, ids[2])
    assert result is not None
    assert result.data_source_id == ds1.id
    assert result.values.keys() == ds1.metrics.keys()


@pytest.mark.asyncio
async def test_get_reading_by_id_not_found(session, ds1: models.DataSource):
    """If a reading id is not found the DAO returns None."""
    result = await dao.get(session, 99999)
    assert result is None
    ids = await create_readings(10, ds1)
    result = await dao.get(session, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_readings_by_source(session, ds1: models.DataSource, ds2: models.DataSource):
    """Can get all readings for a given data source."""
    readings1 = await create_readings(10, ds1)
    readings2 = await create_readings(20, ds2, value=5)
    readings1.extend( await create_readings(15, ds1, value=10))
    # get all readings for ds1
    result = await dao.find(session, data_source_id=ds1.id)
    assert len(result) == len(readings1)
    assert all(r.data_source_id == ds1.id for r in result)
    # all readings for ds2
    result = await dao.find(session, data_source_id=ds2.id)
    assert len(result) == len(readings2)
    assert all(r.data_source_id == ds2.id for r in result)


@pytest.mark.asyncio
async def test_get_for_data_source_with_none(session, ds1: models.DataSource, ds2: models.DataSource):
    """If no readings for a data source, the dao should return an empty list."""
    await create_readings(10, ds1)
    result = await dao.find(session, data_source_id=ds2.id)
    assert isinstance(result, list), "Result should be a list even if empty"
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_readings_by_timestamp(session, ds1: models.DataSource, ds2: models.DataSource):
    """Can get all readings created within a given range of time."""
    await create_readings(10, ds1)
    await create_readings(20, ds2, value=5)
    # wait a bit
    await asyncio.sleep(0.25)  # seconds
    start_time = datetime.now(tz=timezone.utc)
    ids = await create_readings(4, ds1)
    ids += await create_readings(4, ds2)
    ids += await create_readings(2, ds1)
    stop_time = datetime.now(tz=timezone.utc)
    # wait a bit, then create some more
    await asyncio.sleep(0.25)  # seconds
    await create_readings(10, ds2, value=5)
    await create_readings(10, ds1, value=10)
    # get all readings for start <= timestamp <= stop
    result = await dao.find(session, models.Reading.timestamp >= start_time, models.Reading.timestamp <= stop_time)
    assert len(result) == len(ids)
    assert all(r.id in ids for r in result)


@pytest.mark.asyncio
async def test_update_reading(session, ds2: models.DataSource, user1: models.User):
    """Update an existing reading replaces only the fields specified in update data."""
    ids = await create_readings(5, ds2, value=20)
    # Choose a reading to update
    reading = await dao.get(session, ids[0])
    # vars creates a dict of an object's attributes
    original = vars(reading)
    # change reading data. Assumes ds2 has at least 2 data components
    components = ds2.components()
    assert len(components) >= 2, "Test requires a data source with at least 2 data components"
    first = components[0]
    second = components[1]
    values = dict.copy(reading.values)
    values[first] += 10
    values[second] = values[second] * 2 + 1
    updates = schemas.ReadingCreate(data_source_id=ds2.id, created_by_id=user1.id, values=values)
    updated = await dao.update(session, reading.id, updates)
    assert updated.id == original['id']
    assert updated.created_by_id == user1.id
    assert updated.values[first] == values[first]
    assert updated.values[second] == values[second]
    # did not change other attributes
    assert updated.timestamp == original["timestamp"]
    assert updated.data_source_id == original["data_source_id"]


@pytest.mark.asyncio
async def test_update_reading_with_invalid_measurement(session, 
                                                       ds2: models.DataSource, user1: models.User):
    """Update should raise exception if any value names are not value names of the DataSource."""
    ids = await create_readings(5, ds2, value=20)
    # Choose a reading to update
    reading = await dao.get(session, ids[1])
    # Get the existing reading data and append some bogus data
    values = dict.copy(reading.values)
    # append a bogus value
    values["SHOULD_NOT_EXIST"] = 1
    updates = schemas.ReadingCreate(data_source_id=ds2.id, created_by_id=user1.id, values=values)
    with pytest.raises(ValueError):
        updated = await dao.update(session, reading.id, updates)
        assert updated is None


@pytest.mark.asyncio
async def test_update_nonexistent_reading(session, ds1: models.DataSource):
    """Should raise ValueError if reading does not exist."""
    reading_data = schemas.ReadingCreate(data_source_id=ds1.id, 
                                         values={name: 0 for name in ds1.components()}
                                         )
    with pytest.raises(ValueError):
        await dao.update(session, 8888, reading_data)

@pytest.mark.asyncio
async def test_delete_reading(session, ds1):
    """Can delete a reading by id."""
    ids = await create_readings(3, ds1)
    reading_id = ids[0]
    deleted = await dao.delete_reading(session, reading_id)
    assert deleted is not None
    assert deleted.id == reading_id
    # Try to fetch the deleted reading
    result = await dao.get(session, reading_id)
    assert result is None
    # Another reading is still there
    result = await dao.get(session, ids[1])
    assert result is not None


@pytest.mark.asyncio
async def test_delete_nonexistent_reading(session, ds1: models.DataSource):
    """Deleting a reading with non-existing id returns None."""
    await create_readings(20, ds1)   # lets not make it too easy
    deleted = await dao.delete_reading(session, 9999)
    assert deleted is None
