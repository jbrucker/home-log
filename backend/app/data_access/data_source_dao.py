"""ORM operations for DataSource objects.

The DAO do not perform authorization checks -- application or service layer should do that.
"""

from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from app import models, schemas
from app.data_access import base_dao

logger = logging.getLogger(__name__)


async def create(session: AsyncSession,
                 data: schemas.DataSourceCreate
                 ) -> models.DataSource:
    """Add a new data source to persistent storage, assigning an id and creation date.

    :param session: database connection "session" object
    :param data: schema object containing attributes for a new data source
    :returns: a DataSource model instance with persisted values
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    return await base_dao.create(models.DataSource, session, data)


async def get(session: AsyncSession, data_source_id: int) -> models.DataSource | None:
    """Get a data source from database using its id (primary key).
    
    :returns: models.DataSource instance or None if no match for id
    """
    if not isinstance(data_source_id, int) or data_source_id <= 0:
        return None
    options = [joinedload(models.DataSource.owner)]
    return await base_dao.get_by_id(models.DataSource, session, data_source_id, options=options)


async def find(session: AsyncSession, *conditions, **filters) -> list[models.DataSource]:
    """
    Get data sources matching arbitrary conditions and filter criteria.

    Example: await find(session, models.DataSource.created_at < somedate, owner_id=11, name="Foo")

    :param conditions: SqlAlchemy filter expressions
    :param filters: named parameters where names are model attributes, e.g. owner_id=11
    `filters` may include `limit=(int)n` and/or `offset=(int)m` named variables
    :returns: list of matching entities, may be empty
    """
    return await base_dao.find_by(models.DataSource, session, *conditions, **filters)


async def update(session: AsyncSession, data_source_id: int,
                 source_data: schemas.DataSourceCreate
                 ) -> models.DataSource | None:
    """Update the data for an existing data source, identified by `data_source_id`.

    :param dat_source_id: id (primary key) of DataSource to update
    :param source_data: new data for the update. Only fields with values are updated.
    :raises ValueError: if no persisted DataSource with the given id
    """
    data_source = await get(session, data_source_id)
    if not data_source:
        logger.warning(f"Attempt to update non-existent DataSource id={data_source_id}")
        raise ValueError(f"No data source found with id {data_source_id}")
    # TODO Get all fields or only the "set" fields?
    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(data_source, field, value)
    data_source.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(data_source)
    logger.info(f"Updated DataSource id={data_source.id} fields={list(update_data.keys())}")
    return data_source


async def delete_data_source(session: AsyncSession, data_source_id: int) -> models.DataSource | None:
    """Delete a data source by id.

    :returns: data for the deleted object or None if no match.
    """
    return await base_dao.delete_by_id(models.DataSource, session, data_source_id)
