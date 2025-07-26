"""REST endpoints for readings from a data source."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import status
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import models, schemas
from app.data_access import data_source_dao, reading_dao
from app.utils import oauth2

router = APIRouter(prefix="/sources/{source_id}/readings", tags=["Readings"])

logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.Reading, status_code=status.HTTP_201_CREATED)
async def create_reading(source_id: int,
                         reading_data: schemas.ReadingData,
                         request: Request,
                         response: Response,
                         session: AsyncSession = Depends(db.get_session),
                         current_user: models.User = Depends(oauth2.get_current_user)):
    """Create a new reading for a data source."""
    # Data source must exist and belong to current user
    ds: models.DataSource = await data_source_dao.get(session, source_id)
    if not ds:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No data source with id {source_id}")
    if not ds.owner_id == current_user.id:
        # User is authenticated but does not have authority to create readings for this source
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your data source")
    # Verify that keys in reading data match keys in data source's data schema
    try:
        reading_dao.verify_values(reading_data.values, ds)
    except ValueError as ex:
        # FastAPI returns 422 Unprocessable Entity if schema validation fails
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(ex))
    # Add other information from the request
    reading_create = schemas.ReadingCreate(
                        data_source_id=source_id,
                        created_by_id=current_user.id,
                        **reading_data.model_dump(exclude_unset=True)
                        )
    # Save it and return reading with location
    result = await reading_dao.create(session, reading_create)
    # Add Location of new resource - "url_for" performs reverse mapping
    location = request.url_for("get_reading", reading_id=str(result.id), source_id=source_id)
    response.headers["Location"] = str(location)
    logging.info(f"User {current_user.id} created {result}. url={location}")
    # Serialized automatically by FastAPI, using response_model
    return result


@router.get("/{reading_id}", response_model=schemas.Reading)
async def get_reading(source_id: int,
                      reading_id: int,
                      session: AsyncSession = Depends(db.get_session),
                      current_user: models.User = Depends(oauth2.get_current_user)
                      ) -> schemas.Reading:
    """Get one reading from a data source, identified by the reading id."""
    reading: models.Reading = await validate_and_get(source_id, reading_id, session, current_user)
    return reading


@router.get("/", response_model=list[schemas.ReadingDataOut])
async def get_readings(source_id: int,
                       start: str = Query(None),
                       end: str = Query(None),
                       limit: int = Query(100, ge=0),
                       offset: int = Query(0, ge=0),
                       session: AsyncSession = Depends(db.get_session),
                       current_user: models.User = Depends(oauth2.get_current_user)):
    """Get multiple data source readings."""
    # TODO only allow GET readings for DataSource owned by current_user
    filters = {}
    filters['limit'] = limit
    if offset and offset >= 0: filters['offset'] = offset  # noqa: E701 (multiple statements)
    filters['data_source_id'] = source_id
    readings = await reading_dao.find(session, **filters)
    return readings


@router.put("/{reading_id}", response_model=schemas.Reading)
async def update_reading(source_id: int,
                         reading_id: int,
                         reading_data: schemas.ReadingData,
                         session: AsyncSession = Depends(db.get_session),
                         current_user: models.User = Depends(oauth2.get_current_user)
                         ) -> schemas.Reading:
    """Update a reading from a data source."""
    # Get the reading if and only if current_user has permission to modify it
    reading: models.Reading = await validate_and_get(source_id, reading_id, session, current_user)
    try:
        # Which user should created_by refer to?
        creator_id = reading.created_by_id if reading.created_by_id else current_user.id
        # Populate a ReadingCreate with data source id for the DAO
        update_data = schemas.ReadingCreate(
                            data_source_id=reading.data_source_id,
                            created_by_id=creator_id,
                            **reading_data.model_dump(exclude_unset=True))
        # TODO If no created_by_id (such as deleted the user) then revert to data source creator?
        updated = await reading_dao.update(session, reading_id=reading_id, update_data=update_data)
        return updated
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Data integrity error")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading(source_id: int,
                         reading_id: int,
                         session: AsyncSession = Depends(db.get_session),
                         current_user: models.User = Depends(oauth2.get_current_user)
                         ):
    """Delete a reading from a data source using the reading's id."""
    reading = await validate_and_get(source_id, reading_id, session, current_user)
    assert reading is not None
    await reading_dao.delete_reading(session, reading_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def validate_and_get(source_id: int,
                           reading_id: int,
                           session: AsyncSession,
                           current_user: models.User) -> models.Reading:
    """Get the requested Reading if the current user has authority to modify it.

    :raises HTTPException: 404 NOT FOUND, 403 FORBIDDEN, or other
    """
    # Get the reading to update
    reading: models.Reading = await reading_dao.get(session, reading_id)
    # Must belong to this data source
    if not reading or reading.data_source_id != source_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    # current user must be either a) owner of data source, or b) creator of reading
    if reading.created_by_id and reading.created_by_id == current_user.id:
        # User can get/edit a reading he created
        return reading
    # Is the current user the data source owner?
    ds: models.DataSource = await data_source_dao.get(session, source_id)
    if not ds:
        # This should not occur!
        logging.error(f"Got reading {reading} for non-existent data source {source_id}")
        # Allow it, so user can delete it.
        return reading
    if ds.owner_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            detail="Must be reading creator or data source owner")
    return reading
