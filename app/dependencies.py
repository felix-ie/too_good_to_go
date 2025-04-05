from fastapi import Depends, HTTPException, status
from app.models import User
from app.auth import get_current_user
from sqlalchemy.orm import Session
from app.database import get_db

def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_super_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user