from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.firebase import verify_firebase_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

security_scheme = HTTPBearer()

# Reusable type alias for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: DBSession,
) -> User:
    """
    Validate Firebase ID token and return the local User.

    Auto-provisions a new user row on first authenticated request.
    """
    try:
        decoded_token = verify_firebase_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired Firebase ID token.",
            },
        )

    firebase_uid: str = decoded_token["uid"]
    phone_number: str = decoded_token.get("phone_number", "")

    user_repo = UserRepository(db)

    # Look up existing user
    user = await user_repo.get_by_firebase_uid(firebase_uid)

    if user is None:
        # Auto-provision on first login
        user = await user_repo.create(
            firebase_uid=firebase_uid,
            phone_number=phone_number,
        )

    return user


# Reusable dependency type
CurrentUser = Annotated[User, Depends(get_current_user)]
