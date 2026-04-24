# Authentication routes
from fastapi import APIRouter, HTTPException
from datetime import datetime

from db import db
from models import User, LoginRequest, TokenResponse
from services.auth import verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login and get JWT token"""
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_doc.pop("password")
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    token = create_token(user)
    
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=User)
async def get_me(current_user: User = None):
    """Get current user info"""
    # Note: current_user is injected by the dependency in main.py
    return current_user
