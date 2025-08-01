"""Create an engine and do something with it."""
from sqlalchemy import Connection, Engine, create_engine

DATABASE_URL = "sqlite:///experiment.sqlite3"
connection: Connection = None


def init_engine() -> Engine:
    """Create an engine, of course."""
    engine = create_engine(DATABASE_URL,
                           connect_args={},  # "check_same_thread": False for SQLite
                           pool_size=5,      # number of connections in the pool
                           logging_name="",
                           echo=False        # True to see SQL statements on the console
                           )
    return engine


def get_connection(engine: Engine) -> Connection:
    """Create a database connection if it doesn't exist or is closed."""
    global connection
    if not connection or connection.closed:
        connection = engine.connect()
    return connection
