"""REST endpoints for readings from a data source."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi import status
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import db
from app import models, schemas
from app.data_access import data_source_dao, reading_dao
from app.utils import oauth2

router = APIRouter(prefix="/sources/{source_id}/readings", tags=["Readings"])


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
    # Verify that keys in data match keys in data source
    if any(key not in ds.data for key in reading_data.values):
        # FastAPI returns 422 Unprocessable Entity if schema validation fails
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid data name in reading data")
    # Add other information from the request
    # created_by_id is Optional for reading_data - make it explicit now
    reading_data.created_by_id = current_user.id
    reading_create = schemas.ReadingCreate(
                        data_source_id=source_id,
                        **reading_data.model_dump(exclude_unset=True)
                        )
    # Save it and return reading with location
    result = await reading_dao.create(session, reading_create)
    # Add Location of new resource - "url_for" performs reverse mapping
    location = request.url_for("get_reading", reading_id=str(result.id), source_id=source_id)
    response.headers["Location"] = str(location)
    # result is serialized automatically by FastAPI
    return result


@router.get("/{reading_id}", response_model=schemas.Reading)
async def get_reading(source_id: int,
                      reading_id: int,
                      session: AsyncSession = Depends(db.get_session),
                      current_user: models.User = Depends(oauth2.get_current_user)
                      ) -> schemas.Reading:
    """Get one reading from a data source, identified by the reading id."""
    ds: models.DataSource = await data_source_dao.get(session, source_id)
    if not ds:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"No data source with id {source_id}")
    if not ds.owner_id == current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your data source")
    # Ensure this reading belongs to this data source
    readings = await reading_dao.find(session, id=reading_id, data_source_id=source_id)
    if not readings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Reading id {reading_id} of source {source_id} not found")
    # should be only one match
    return readings[0]


@router.get("/", response_model=list[schemas.ReadingData])
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
    if offset and offset >= 0: filters['offset'] = offset
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
    # Get the reading to update
    reading: models.Reading = await reading_dao.get(session, reading_id)
    # Must belong to this data source and current user
    if not reading or reading.data_source_id != source_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if reading.created_by_id and reading.created_by_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Reading not owned by current user")
    try:
        # Populate a ReadingCreate with data source id for the DAO
        update_data = schemas.ReadingCreate(**reading_data.model_dump())
        update_data.data_source_id = reading.data_source_id
        # TODO If no created_by_id (such as deleted the user) then revert to data source creator?
        update_data.created_by_id = reading.created_by_id
        updated = await reading_dao.update(session, reading_id=reading_id, update_data=update_data)
        return updated
    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Data integrity error")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading(source_id: int, reading_id: int):
    """Delete a reading from a data source."""
    raise HTTPException(status.HTTP_404_NOT_FOUND)
