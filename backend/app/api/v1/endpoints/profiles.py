from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.users import Profile, User
from app.schemas.profiles import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter()


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/profiles
    Creates a new family member profile for the authenticated user.
    """
    # Verify user exists
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    profile = Profile(
        user_id=payload.user_id,
        name=payload.name,
        relationship_type=payload.relationship_type,
        dob=payload.dob,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        relationship_type=profile.relationship_type,
        dob=profile.dob,
    )


@router.get("", response_model=List[ProfileResponse])
async def list_profiles(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /v1/profiles?user_id=...
    Lists all family profiles belonging to the user.
    """
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profiles = result.scalars().all()
    return [
        ProfileResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            relationship_type=p.relationship_type,
            dob=p.dob,
        )
        for p in profiles
    ]


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """GET /v1/profiles/{profile_id}"""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        relationship_type=profile.relationship_type,
        dob=profile.dob,
    )


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """PATCH /v1/profiles/{profile_id} — Update name, relationship, dob"""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    if payload.name is not None:
        profile.name = payload.name
    if payload.relationship_type is not None:
        profile.relationship_type = payload.relationship_type
    if payload.dob is not None:
        profile.dob = payload.dob

    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        relationship_type=profile.relationship_type,
        dob=profile.dob,
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """DELETE /v1/profiles/{profile_id} — Deletes profile and all associated data (cascade)."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await db.delete(profile)
    await db.commit()
    return None
