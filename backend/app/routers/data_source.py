"""REST endpoints for a data source.

   To declare a response model used to serialize the return value, use a schema class not a model class.
"""
# flake8: noqa: E251
# E251 unexpected space around equals in 'parameter=value'

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import status  # for HTTP status codes. Can alternatively use http.HTTPStatus.
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import schemas
from app.data_access import data_source_dao, user_dao
from app.utils import oauth2

# add option prefix="/source" to factor out path prefix.
router = APIRouter(tags=["data source"])


@router.get("/sources")
async def get_data_sources(
                    limit: int = Query(20, ge=1, le=100),
                    offset: int = Query(0, ge=0),
                    session: AsyncSession = Depends(db.get_session),
                    current_user = Depends(oauth2.get_current_user)) -> list[schemas.DataSource]:
    """Get data sources owned by current user, up to specified `limit`.
    
    :param limit: maximum number of sources to return.  Use 0 for unlimited.
    :param offset: number of sources (ordered by id) to skip before first result returned.
    """
    owner_id = current_user.id
    sources = await data_source_dao.find(session, owner_id=owner_id, limit=limit, offset=offset)
    return sources


# TODO Add current_user and only get a source owned by current user
@router.get("/sources/{source_id}")
async def get_data_source(source_id: int, session: AsyncSession = Depends(db.get_session)) -> schemas.DataSource:
    """Get a data source with the matching id."""
    result = await data_source_dao.get(session, source_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"DataSource id {source_id} not found")
    return result


@router.post("/sources", status_code=status.HTTP_201_CREATED, response_model=schemas.DataSource)
async def create_source(data: schemas.DataSourceCreate,
                        request: Request,
                        response: Response,
                        session: AsyncSession = Depends(db.get_session),
                        current_user = Depends(oauth2.get_current_user)
                        ):
    """Persist a new data source, owned by the currently authenticated user.

       :returns: the source data and a `Location:` header containing the URL of the new entity.
    """
    # Currently there are no uniqueness constraints on data sources.
    try:
        data.owner_id = current_user.id
        result = await data_source_dao.create(session, data)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Invalid data for data source. Exception: {ex}")

    # Add Location of new user. "url_for" performs reverse mapping
    location = request.url_for("get_data_source", source_id=str(result.id))
    response.headers["Location"] = str(location)
    # result is serialized automatically by FastAPI
    return result


@router.put("/sources/{source_id}", status_code=status.HTTP_200_OK, response_model=schemas.DataSource)
async def update_source(source_id: int, 
                        data: schemas.DataSourceCreate, 
                        session: AsyncSession = Depends(db.get_session),
                        current_user = Depends(oauth2.get_current_user)
                        ):
    """Update the data for an existing source, using the `source_id` to identify the entity to modify."""
    result = await data_source_dao.get(session, source_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"No data source with id {source_id}")
    # Cannot modify another person's DataSource
    if current_user.id != result.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Cannot modify data source you don't own")
    # May change ownership to another user, but owner_id must exist
    if data.owner_id and data.owner_id != current_user.id:
        user = user_dao.get(session, data.owner_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Owner id {data.owner_id} does not exist")
    # return the updated DataSource model
    return await data_source_dao.update(session,
                                data_source_id=source_id,
                                source_data=data)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: int,
                      session: AsyncSession = Depends(db.get_session),
                      current_user = Depends(oauth2.get_current_user)):
    """Delete a data source by id.  Returns the data for the deleted item."""
    logging.getLogger(__name__).info(f"delete_source source_id {source_id} by {str(current_user)}")
    assert source_id > 0
    data_source = await data_source_dao.get(session,source_id)
    if not data_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if data_source.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You do not have authorization to delete data source {source_id}")
    result = await data_source_dao.delete_data_source(session, source_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data source with id {source_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)