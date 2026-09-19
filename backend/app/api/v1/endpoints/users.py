from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.core.security import verify_firebase_token, create_access_token, create_refresh_token, decode_token
from app.models.users import User, Profile, Consent
from app.models.audit import AuditLog
from app.schemas.auth import TokenExchangeRequest, TokenResponse, RefreshTokenRequest

router = APIRouter()


@router.post("/auth/exchange", response_model=TokenResponse)
async def exchange_token(
    payload: TokenExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/auth/exchange
    Verifies Firebase ID token and exchanges it for a short-lived access token and refresh token.
    Creates user and default profile if not exists.
    """
    decoded = await verify_firebase_token(payload.firebase_id_token)
    google_uid = decoded.get("uid")
    email = decoded.get("email") or f"{google_uid}@example.com"

    result = await db.execute(select(User).where(User.google_uid == google_uid))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            google_uid=google_uid,
            email=email,
            locale=payload.locale or "en"
        )
        db.add(user)
        await db.flush()

        profile = Profile(
            user_id=user.id,
            name=decoded.get("name") or "Primary User",
            relationship_type="self"
        )
        db.add(profile)

        consent = Consent(
            user_id=user.id,
            purpose="Prescription digitization and reminder tracking"
        )
        db.add(consent)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/auth/refresh
    Generates a new access token using a valid refresh token.
    """
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided token is not a refresh token"
        )

    user_id = decoded.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    new_access = create_access_token({"sub": user.id, "email": user.email})
    new_refresh = create_refresh_token({"sub": user.id})

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user_id=user.id,
        email=user.email
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """
    DELETE /v1/users/me
    Right to Erasure (DPDP Act Compliance). Permanently deletes user and cascade deletes
    all associated profiles, prescriptions, medications, and logs.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        # Audit log of erasure
        audit = AuditLog(
            user_id=user_id,
            action="right_to_erasure_account_deleted",
            entity="User",
        )
        db.add(audit)
        await db.commit()

        # Delete user
        await db.delete(user)
        await db.commit()

    return None
