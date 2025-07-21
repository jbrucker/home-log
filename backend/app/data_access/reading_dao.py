"""Persistence operations for Reading objects."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
# select is now asynchronous by default, so don't need to import from sqlachemy.future

import logging
from app import models, schemas
from app.data_access import base_dao

logger = logging.getLogger(__name__)


async def create(session: AsyncSession, reading_data: schemas.ReadingCreate) -> models.Reading:
    """Add a new user to persistent storage, assigning a user id and creation date.

    :param session: database connection "session" object
    :param reading_data: schema object containing attributes for a new reading entity
    :returns: a Reading model instance with persisted values
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid

    Does NOT validate that the reading components names (keys in values) match keys
    in DataSource definition.
    """
    data_source_id = reading_data.data_source_id
    if not data_source_id:
        raise ValueError("Missing data source id")
    ds = await base_dao.get_by_id(models.DataSource, session, data_source_id)
    if not ds:
        raise ValueError(f"No data source for id {data_source_id}")
    verify_values(reading_data.values, ds)
    return await base_dao.create(models.Reading, session, reading_data)


async def get(session: AsyncSession, reading_id: int) -> models.Reading | None:
    """Get a Reading using its id (primary key).

    :returns: models.Reading instance or None if no match for `reading_id`
    """
    if not isinstance(reading_id, int) or reading_id <= 0:
        return None
    # options = [joinedload(...)]
    return await base_dao.get_by_id(models.Reading, session, reading_id)


async def find(session: AsyncSession, *conditions, **filters) -> list[models.Reading]:
    """
    Get readings matching arbitrary conditions and filter criteria.

    Example: Get up to 100 readings from data source #11
             results: list[Reading] = await find(session, data_source_id=11, limit=100)

    :param conditions: SqlAlchemy filter expressions
    :param filters: named parameters where names are model attributes, e.g. data_source_id=11
    `filters` may include `limit=(int)n` and/or `offset=(int)m` named variables
    :returns: list of matching entities, may be empty
    """
    return await base_dao.find_by(models.Reading, session, *conditions, **filters)


async def update(session: AsyncSession,
                 reading_id: int,
                 reading_data: schemas.ReadingCreate) -> models.Reading | None:
    """Update the data for an existing reading, identified by id.

    :param reading_id: id (primary key) of Reading to update
    :param reading_data: new data for the reading.
    :raises ValueError: if no persisted Reading with the given `reading_id`
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are invalid
    """
    reading = await base_dao.get_by_id(models.Reading, session, reading_id)
    if not reading:
        raise ValueError(f"Unknown reading id {reading_id}")
    data_source_id = reading_data.data_source_id
    if not data_source_id:
        raise ValueError(f"Missing data source id in update data {reading_data}")
    ds = await base_dao.get_by_id(models.DataSource, session, data_source_id)
    if not ds:
        raise ValueError(f"No data source for id {data_source_id}")
    verify_values(reading_data.values, ds)
    # General way to get the attributes in an instance of a class:
    #   vars(instance_ref)
    # Pydantic method for schemas:
    #   schema_instance.model_dump(exclude_unset=True)
    # Both return a dict
    for (key, value) in reading_data.model_dump(exclude_unset=True).items():
        # update the attribute unless None
        if value:
            setattr(reading, key, value)
        else:
            logger.warning("update: not updating {key}={value} from {reading_data}")
    await session.commit()
    await session.refresh(reading)
    logger.info(f"Updated Reading id={reading.id} fields: {vars(reading_data)}")
    return reading


async def delete_reading(session: AsyncSession, reading_id: int) -> models.Reading | None:
    """Delete a reading by id.

    :returns: data for the deleted entity or None if no match for the id.
    """
    return await base_dao.delete_by_id(models.Reading, session, reading_id)


def verify_values(values: dict[str, Any], ds: models.DataSource) -> bool:
    """Verify that all keys in the `values` dict are components in the datasource data.

    :raises ValueError: if any key in `values` is not a component of DataSource data
    """
    for key in values.keys():
        if key not in ds.components():
            raise ValueError(f'Reading data: "{key}" is not a component of DataSource {ds.id}')
    return True
