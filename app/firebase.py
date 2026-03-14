import firebase_admin
from firebase_admin import auth, credentials

from app.config import settings

_firebase_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App:
    """Initialize the Firebase Admin SDK (idempotent)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.

    Returns dict with at least: 'uid', 'email'
    Raises firebase_admin.auth.InvalidIdTokenError on failure.
    """
    decoded = auth.verify_id_token(id_token)
    return decoded
