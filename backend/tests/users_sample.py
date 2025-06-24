# experiments/users_sample.py

import asyncio
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Database URL is defined in config.py
# Example alternatives:
# DATABASE_URL = "sqlite:///test_homelog.db"
# DATABASE_URL = "postgresql://user:password@localhost/mydatabase"
# DATABASE_URL = "mysql+pymysql://user:password@localhost/mydatabase"

# Import your models (assuming they're in models.py)
from app.models import User, UserPassword
from app.core.database import db 

async def insert_sample_users():
    """Insert sample users into the database."""
    #db = SessionLocal()
    
    try:
        # Sample user 1
        user1 = User(
            email="user1@example.com",
            username="user1",
            created_at=datetime.utcnow()
        )
        session = db.get_session()
        session.add(user1)
        await session.commit()
        await session.refresh(user1)
        
        user1_password = UserPassword(
            user_id=user1.id,
            hashed_password="hashed_password_123"  # In real usage, use proper password hashing
        )
        # TODO

        session = db.get_session()
        
        # Sample user 2
        user2 = User(
            email="user2@example.com",
            username="user2",
            created_at=datetime.utcnow()
        )
        session.add(user2)
        await session.commit()
        await session.refresh(user2)
        
        user2_password = UserPassword(
            user_id=user2.id,
            hashed_password="hashed_password_456"
        )

        
    except Exception as e:
        session.rollback()
        print(f"Error inserting users: {e}")


async def main():
    # Create tables if they don't exist
    await db.create_tables()
    
    # Insert sample data
    await insert_sample_users()

if __name__ == "__main__":
    asyncio.run(main())