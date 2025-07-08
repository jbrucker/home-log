"""ORM operations for DataSource objects.
   The DAO do not perform authentication checks -- routes should do that.
"""

from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select, and_

from app import models, schemas

logger = logging.getLogger(__name__)

async def create_data_source(session: AsyncSession, 
                             source_data: schemas.DataSourceCreate
                             ) -> models.DataSource:
    """Add a new data source to persistent storage, assigning an id and creation date.

    :param session: database connection "session" object
    :param source_data: schema object containing attributes for a new data source
    :returns: a DataSource model instance with persisted values
    :raises IntegrityError: if uniqueness constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    data_source = models.DataSource(**source_data.model_dump())
    session.add(data_source)
    await session.commit()
    await session.refresh(data_source)     # update the id and created_at
    logger.info(f"Created DataSource id={data_source.id} owner_id={data_source.owner_id} name={data_source.name}")
    return data_source


async def get_data_source_by_id(session: AsyncSession, data_source_id: int) -> models.DataSource | None:
    """Get a data source from database using his id (primary key).
    
    :returns: models.DataSource instance or None if no match for id
    """
    if not isinstance(data_source_id, int) or data_source_id <= 0:
        return None
    # Another way:
    # stmt = select(models.DataSource).where(models.DataSource.id == user_id)
    # result = await session.execute(stmt)
    # Return the first result or None if no match.
    result = await session.get(models.DataSource, data_source_id, 
                               options=[joinedload(models.DataSource.owner)])
    return result


async def get_data_sources_by(session: AsyncSession, *conditions, **filters) -> list[models.DataSource]:
    """
    Get data sources matching arbitrary filter criteria.
    Usage: await get_data_sources_by(session, owner_id=11, name="Foo")
    
    :param filters: named parameters where names are model attributes, e.g. owner_id=11
    :param conditions: S
    :returns: list of matching entities, may be empty
    """
    stmt = select(models.DataSource)
    if filters:
        stmt = stmt.where(and_(*(getattr(models.DataSource, k) == v for k, v in filters.items())))
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_data_sources_by_owner(session: AsyncSession, user: models.User | int) -> list[models.DataSource] | None:
    """Get all the DataSources owned by a given user."""
    if isinstance(user, int):
        user_id = user
    else:
        user_id = user.id
    result = await get_data_sources_by(session, owner_id=user_id)
    return result


async def update_data_source(session: AsyncSession, data_source_id: int, 
                             source_data: schemas.DataSourceCreate) -> models.DataSource | None:
    """Update the data for an existing data source, identified by `data_source_id`.

       :param dat_source_id: id (primary key) of DataSource to update
       :param source_data: new data for the update. Only fields with values are updated.
       :raises ValueError: if no persisted DataSource with the given id
    """
    data_source = await get_data_source_by_id(session, data_source_id)
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
    data_source = await get_data_source_by_id(session, data_source_id)
    if not data_source:
        logger.warning(f"Tried to delete non-existent DataSource id={data_source_id}")
        return None
    await session.delete(data_source)
    await session.commit()
    logger.info(f"Deleted DataSource id={data_source.id} name={data_source.name}")
    # To indicate that the instance is no longer persisted, set id to None?
    return data_source

