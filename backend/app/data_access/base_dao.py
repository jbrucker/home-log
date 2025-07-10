"""Common CRUD operations that can be invoked by concrete DAOs."""

from datetime import datetime
import logging
from typing import Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
# select is now asynchronous by default, so don't need to import from sqlachemy.future
from sqlalchemy import select, and_

from app import models, schemas
from app.core.database import Base

logger = logging.getLogger(__name__)


async def create(model_class: Type[models.Base],  session: AsyncSession, data: Type[schemas.BaseModel]
                ) -> models.Base:
    """Add a new model_class instance to persistent storage, assigning an id and creation date.

    :param model_class: the type of model to create, e.g. models.User
    :param session: database connection "session" object
    :param data: creational schema object containing attributes for the new entity
    :returns: a persisted model instance with persisted values
    :raises IntegrityError: if any constraint(s) violated
    :raises ValueError: if any required values are missing or invalid (Note)

    Note: the Schema object should perform data validation, so a ValueError on
          save indicates an inconsistency between schema validators and 
          database requirements.
    """
    try:
        new_entity = model_class(**data.model_dump())
        session.add(new_entity)
        await session.commit()
        await session.refresh(new_entity)     # update the id and created_at
    except Exception as ex:
        logger.error(f"Exception creating {model_class.__name__} with data {data.model_dump()}. Exception: {ex}")
        raise ex
    logger.info(f"Created {model_class.__name__} {str(new_entity)} at {datetime.now()}")
    return new_entity


async def get_by_id(model_class: Type[Base], session: AsyncSession, model_id: Any, options = []):
    """Get an entity from persistent storage, using its id (primary key)
    
    :options: a list of options for `get`, such as `joinedload(models.User.user_password)`
    :returns: an instance of `model_class` or None
    """
    if not model_id:
        return None
    # since the caller must await the result of this function, do we need await here?
    return await session.get(model_class, model_id, options=options)


# TODO Add an 'order_by' parameter
async def get_all(model_class: Type[Base], session: AsyncSession, 
                  offset: int = 0, limit: int = 0) -> list[Base]:
    """Get all entities, ordered by id attribute.

    This method does **not** eagerly load relationships. 

    :param limit: max number of values to return, default is unlimited
    :param skip: start returning users after skipping this many initial records
    :returns: list of entities from model_class. May be empty.
    """
    stmt = select(model_class).order_by(model_class.id)
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit > 0:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

# TODO Add 'offset=offset' and 'limit=n', with tests
async def find_by(model_class: Type[Base], session: AsyncSession, *conditions, **filters) -> list:
    """
    Get persisted instances of `model_class` matching arbitrary filter criteria.
    Usage: await get_data_sources_by(models.User, session, owner_id=11, name="Foo")
    
    :param model_class: the *class* of the model type, e.g. models.User
    :param filters: named parameters where names are model attributes, e.g. owner_id=11
    :param conditions: SqlAlchemy filter expressions, e.g. models.User.email.contains("gmail.com")
    :returns: list of matching entities, may be empty
    """
    stmt = select(model_class)
    all_conditions = list(conditions)
    if filters:
        all_conditions += [getattr(model_class, key) == value 
                           for key, value in filters.items() ]
    if all_conditions:
        stmt = stmt.where(and_(*all_conditions))
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_by_id(model_class: Type[Base], session: AsyncSession, entity_id: Any) -> Base | None:
    """Delete a persisted object by id.

    :returns: data for the deleted entity or None if no match for the entity_id.
    """
    result = await get_by_id(model_class, session, entity_id)
    model_name = model_class.__name__
    if not result:
        logger.warning(f"Failed to delete non-existent {model_name} id={entity_id}")
        return None
    await session.delete(result)
    #await session.flush()  # flush not necessary together with 'commit'
    await session.commit()
    logger.info(f"Deleted {model_name} {str(result)}")
    return result
    