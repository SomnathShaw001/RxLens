import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from app.core.config import settings

# Initialize Firebase Admin if credentials or project ID provided
_firebase_initialized = False
try:
    if settings.FIREBASE_CREDENTIALS_PATH:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    elif settings.FIREBASE_PROJECT_ID:
        firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
        _firebase_initialized = True
except Exception:
    _firebase_initialized = False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """Verifies Firebase ID token or allows simulated token in local dev environment."""
    if _firebase_initialized:
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Firebase verification failed: {str(e)}",
            )
    else:
        # Dev simulation mode if Firebase is not connected yet
        if id_token.startswith("mock_") or settings.ENVIRONMENT == "development":
            return {
                "uid": id_token.replace("mock_", "") or "dev_user_123",
                "email": "dev_user@example.com",
                "name": "Dev User"
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase Auth is not configured on the backend.",
        )


async def get_current_user_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extracts and validates Bearer token from request headers."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ")[1]
    return decode_token(token)
