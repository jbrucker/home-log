"""Create table schema for a "dev" database using PostgreSQL in a Docker container.

   Then copy data from the Sqlite database to Postgres.  This totally screwed up the
   auto-generated index mechanism. Subsequent creates (INSERT) caused Integrity errors.
"""

import json
# from tqdm import tqdm  # for progress bar. Requires: pip install tqdm
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from decouple import config

# The SQLAlchemy model classes
from app.models import Base

# SQLite (source) configuration
sqlite_engine = create_engine('sqlite:///dev.sqlite3')
SqliteSession = sessionmaker(bind=sqlite_engine)

# PostgreSQL (target) configuration
# Clean way to create a database URL for Postgres

url = URL.create(
        drivername="postgresql",
        username=config("POSTGRES_USER"),
        password=config("POSTGRES_PASSWORD"),
        host="localhost",  # if running the script on host os
        port=5432,
        database=config("POSTGRES_DB")
        )

url_str = url.__to_string__(hide_password=False)
input("URL = " + url_str)

pg_engine = create_engine(url_str)
PgSession = sessionmaker(bind=pg_engine)


def init_postgres_schema():
    """Create all tables in PostgreSQL with proper JSONB columns."""
    # This will use your existing model definitions but create them in PostgreSQL
    Base.metadata.create_all(pg_engine)
    # migrate_json_columns(pg_engine)


def migrate_json_columns(pg_engine):
    """If you need to modify any column types specifically for PostgreSQL."""
    with pg_engine.connect() as conn:
        # Example: Change TEXT columns to JSONB where appropriate
        stmt = "ALTER TABLE readings ALTER COLUMN values TYPE JSONB USING values::JSONB"
        conn.execute(stmt)


def migrate_data(batch_size=1000):
    """Migrate data from SQLite to PostgreSQL with JSON conversion."""
    sqlite_session = SqliteSession()
    pg_session = PgSession()

    # Get all model classes from your Base
    models = Base.registry._class_registry.values()

    for model in models:
        if not hasattr(model, '__tablename__'):
            continue

        table_name = model.__tablename__
        print(f"\nMigrating {table_name}...")
        # Get all records from SQLite
        records = sqlite_session.query(model).yield_per(batch_size)

        # Identify JSON columns (you can also hardcode these if known)
        # json_columns = [
        #    column.name for column in model.__table__.columns
        #    if column.name.endswith('json') or column.name.startswith('json')
        # ]
        json_columns = ["values", "metrics"]
        # Batch insert into PostgreSQL
        for i, record in records:
            # Convert JSON fields
            data = {c.name: getattr(record, c.name) for c in model.__table__.columns}

            for col in json_columns:
                if col in data and data[col] is not None and isinstance(data[col], str):
                    try:
                        data[col] = json.loads(data[col])
                    except json.JSONDecodeError:
                        data[col] = None

            # Create new record in PostgreSQL
            pg_record = model(**data)
            pg_session.add(pg_record)
            # Commit in batches
            if i % batch_size == 0:
                pg_session.commit()
        pg_session.commit()

    pg_session.close()
    sqlite_session.close()


if __name__ == '__main__':
    # init_postgres_schema()
    # migrate_json_columns(pg_engine)
    migrate_data()
