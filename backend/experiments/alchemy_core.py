"""Experiment with SQLAlchemy Core features including model definition."""

import logging
from sqlalchemy import CursorResult, Engine, Connection
# classes for SQLAlchemy core. Metadata stores info about database and tables.
from sqlalchemy import Table, Column, MetaData
# abstraction for database datatypes
from sqlalchemy import Boolean, Integer, String, TIMESTAMP
from sqlalchemy import sql  # for sql.func

from core import init_engine, get_connection

# Global variables set in __main__  
connection: Connection = None
users: Table = None

# Programmatic way to create table schema

def create_schema(connection: Connection):
    """Create table schema.  Supposedly idempotent."""
    metadata = MetaData()
    users = Table("users", 
                  metadata,
                  Column('id', Integer, primary_key=True),
                  Column('email', String(100), nullable=False, unique=True),
                  Column('username', String(50)),
                  # for Postgres, can also use server_default='CURRENT_TIMESTAMP' or sql.func.current_timestamp()
                  Column('created_at', TIMESTAMP(timezone=True), server_default=sql.func.now(),
                         onupdate=sql.func.current_timestamp()),
                  Column('is_active', Boolean, server_default='TRUE')
                  )
    try:
        metadata.create_all(engine)
    except Exception as e:
        print(f"Error creating schema: {e}")
    return users

def insert_user(email, username):
    user_data = {'email': email, 'username': username}
    connection = get_connection()
    connection.execute(users.insert(), user_data)
    # same as: 
    # statement = users.insert().values(email=email, username=username)
    # connection.execute(statement)
    connection.commit()

def insert_user2(email, username) -> bool:
    """Another way to insert a user."""
    from sqlalchemy import insert
    global users
    statement = insert(users).values(email=email, username=username)
    try:
        result = connection.execute(statement)
        connection.commit()
    except Exception as e:
        logging.error(f"Error inserting user {email}: {e}")
        return False


def show_users():
    global users, connection
    result: CursorResult = connection.execute(users.select())
    for row in result:
        user = row._asdict()
        print(f'{user["id"]:4} {user["username"]:20} {user["email"]:20} {user["created_at"]}')

def run_experiment1():
    insert_user("jb@gmail.com", "Jim")
    insert_user("tip@yahoo.com", "Tip")
    input("Insert a duplicate email to see the error: ")
    try:
        insert_user("jb@gmail.com", "Frank") # This will raise an IntegrityError
    except Exception as e:
        print(f"Error inserting user 'jb@gmail.com': {e}")
    show_users()


def run_experiment2():
    USER_DATA = [ ("jb@gmail.com", "Jim"), ("tip@yahoo.com", "Tip"), 
                  ("fatalai@gmail.com", "Fatalai"), ("frank@hotmail.com", "Frank") 
                ]

    for email, username in USER_DATA:
        print(f"Insert user: {email}, {username}")
        insert_user2(email, username)
    show_users()


def configure_logging():
    """Configure logging for the module."""
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s:  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename='alchemy_core.log',
                        filemode='a')  # 'w' to overwrite the log file each time 
    

if __name__ == '__main__':
    configure_logging()
    engine = init_engine()
    connection = get_connection(engine)
    users = create_schema(connection)
    # idempotent or throw exception?
    users = create_schema(connection)
    # display all users
    show_users()