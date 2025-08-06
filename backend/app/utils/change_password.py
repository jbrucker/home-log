"""Change a user's password."""
import asyncio
from app.core.database import db
from app.core import security
from app.data_access import user_dao


async def async_change_password(email: str, new_password: str = None):
    """Change password for a user identified by email address."""
    async for session in db.get_session():
        print(f"Retrieving user for email {email}")
        user = await user_dao.get_by_email(session, email)
        if not user:
            print(f"No user with email {email}")
            return
        if not new_password:
            new_password = input(f"New password for {email}? ").strip()
        # Change password
        try:
            user_password = await user_dao.set_password(session, user, new_password)
            assert user_password is not None
        except Exception as ex:
            print("Exception from UserDao.set_password:", ex)


def change_password(email: str, new_password: str):
    """Change the password for a user identified by email address."""
    asyncio.run(async_change_password(email, new_password))


async def verify_password(email: str, password: str) -> bool:
    """Verify that a user's password matches the given plain-text password string."""
    async for session in db.get_session():
        print(f"Retrieving user for email {email}")
        user = await user_dao.get_by_email(session, email)
        if not user:
            print(f"No user with email {email}")
            return
        password_hash = await user_dao.get_password(session, user)
        password_matches = security.verify_password(password, password_hash)
        if password_matches:
            print("Password updated successfully")
        else:
            print("Oops. Password does not match.")
        return password_matches


if __name__ == "__main__":
    email = input("Email to change password for? ").strip()
    password = input(f"New password for {email}? ").strip()
    asyncio.run(async_change_password(email, password))
    asyncio.run(verify_password(email, password))
