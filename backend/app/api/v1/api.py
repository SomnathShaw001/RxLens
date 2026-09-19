from fastapi import APIRouter
from app.api.v1.endpoints import prescriptions, drugs, medications, chat, users, profiles

api_router = APIRouter()

api_router.include_router(prescriptions.router,  prefix="/prescriptions", tags=["prescriptions"])
api_router.include_router(drugs.router,           prefix="/drugs",         tags=["drugs"])
api_router.include_router(medications.router,     prefix="/medications",   tags=["medications"])
api_router.include_router(chat.router,            prefix="/chat",          tags=["chat"])
api_router.include_router(profiles.router,        prefix="/profiles",      tags=["profiles"])
api_router.include_router(users.router,           prefix="/users",         tags=["users"])
api_router.include_router(users.router,           prefix="",               tags=["auth"])
