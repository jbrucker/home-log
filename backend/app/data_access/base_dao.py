"""Base for common DAO functions, to avoid duplicate code in model-specific DAO."""

from datetime import datetime
import logging
from typing import Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select, select, and_
# select is now asynchronous by default, so don't need to import sqlachemy.future

from app import models, schemas
from app.core.database import Base

logger = logging.getLogger(__name__)


async def create(Model: Type[models.Base], session: AsyncSession, data: Type[schemas.BaseModel]
                 ) -> models.Base:
    """Add a new Model (class) instance to persistent storage, assigning an id and creation date.

    :param Model: the type of model to create, e.g. models.User
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
        new_entity = Model(**data.model_dump())
        session.add(new_entity)
        await session.commit()
        await session.refresh(new_entity)     # update the id and created_at
    except Exception as ex:
        logger.error(f"Exception creating {Model.__name__} with data {data.model_dump()}. Exception: {ex}")
        raise ex
    logger.info(f"Created {Model.__name__} {str(new_entity)} at {datetime.now()}")
    return new_entity


async def get_by_id(Model: Type[Base], session: AsyncSession, model_id: Any, options=[]):
    """Get an entity from persistent storage, using its id (primary key).

    :paaram Model: a model class that extends SqlAlchemy's Base class.
    :param session: an async session
    :param model_id: the id of the Model instance to get from persistent storage
    :param options: a list of options for `get`, such as `joinedload(models.User.user_password)`
    :returns: an instance of `model_class` or None
    """
    if not model_id:
        return None
    # since the caller must await the result of this function, do we need await here?
    return await session.get(Model, model_id, options=options)


# TODO Add an 'order_by' parameter
# TODO Eliminate this function and use find_by instead.
async def get_all(Model: Type[Base], session: AsyncSession,
                  limit: int = 0, offset: int = 0) -> list[Base]:
    """Get all entities, ordered by id attribute.

    This method does **not** eagerly load relationships.

    :paaram Model: a model class that extends SqlAlchemy's Base class.
    :param limit: max number of values to return, default is unlimited
    :param offset: start returning entities after skipping this many initial records
    :returns: list of entities from model_class. May be empty.
    """
    stmt = select(Model).order_by(Model.id)
    result = await session.execute(paginate(stmt, limit, offset))
    return result.scalars().all()


async def find_by(Model: Type[Base],
                  session: AsyncSession,
                  *conditions,
                  limit: int = 0,
                  offset: int = 0,
                  **filters) -> list:
    """
    Get persisted instances of `model_class` matching arbitrary filter criteria.

    Usage: await find_by(models.User, session, User.created_at<somedate, limit=10, username="Foo")
    :param Model: the *class* of the model type, e.g. models.User
    :param filters: named parameters where names are model attributes, e.g. owner_id=11
    :param limit: max number of values to return, default is unlimited
    :param offset: start returning matches after skipping this many initial matching records
    :param conditions: SqlAlchemy select expressions, e.g. models.User.email.contains("gmail.com")
    :returns: list of matching entities, may be empty
    """
    stmt = select(Model)
    all_conditions = list(conditions)
    if filters:
        all_conditions += [getattr(Model, key) == value
                           for key, value in filters.items()]
    if all_conditions:
        stmt = stmt.where(and_(*all_conditions))
    # Apply ordering after WHERE
    stmt = stmt.order_by(Model.id)
    # Finally apply pagination
    result = await session.execute(paginate(stmt, limit, offset))
    return result.scalars().all()


async def delete_by_id(Model: Type[Base], session: AsyncSession, entity_id: Any) -> Base | None:
    """Delete a persisted object by id.

    :returns: data for the deleted entity or None if no match for the entity_id.
    """
    result = await get_by_id(Model, session, entity_id)
    model_name = Model.__name__
    if not result:
        logger.warning(f"Failed to delete non-existent {model_name} id={entity_id}")
        return None
    await session.delete(result)
    # await session.flush()  # flush not necessary when used with 'commit'
    await session.commit()
    logger.info(f"Deleted {model_name} {str(result)}")
    return result


def paginate(stmt: Select, limit: int = 0, offset: int = 0) -> Select:
    """Apply options to paginate result of a Select statement.

       The statement (stmt) should already contain a `.order_by` clause
       for the desired ordering.
    """
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit > 0:
        stmt = stmt.limit(limit)
    return stmt
