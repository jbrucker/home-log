"""Experiment with how to access related entities, using User and UserPassword.

User.user_password -> refers to a UserPassword or None
UserPassword.user  -> refers to the related User. Should never be None.

Requires: test database already contains users with passwords.
"""

import asyncio
from sqlalchemy.orm import joinedload
from app.models import User, UserPassword
from app.core.database import db

# Database URL for experiments
DATABASE_URL = "sqlite+aiosqlite://./dev.sqlite3"


async def fetch_user_with_password():
    """Get a user and test if we also get the related user_password."""
    async for session in db.get_session():
        # Get a user and see if we get the related user_password
        for user_id in range(1, 5):
            user = await session.get(User, user_id, options=[joinedload(User.user_password)])
            if not user:
                continue
            print(f"user id {user_id}", str(user))
            try:
                # works only if 
                # 1. lazy="joined" is used in model def'n
                # or 
                # 2. "get" with options=[joinedload(User.user_password)]
                user_password: UserPassword = user.user_password
            except Exception as ex:
                print("Exception at user.user_password", ex)
                return
            if user_password is None:
                print(f"User {user.id} has no user_password")
            else:
                print("password =", user_password.hashed_password)


async def main():
    """Perform sample actions.  Create tables, insert users."""
    await fetch_user_with_password()


if __name__ == "__main__":
    asyncio.run(main())
