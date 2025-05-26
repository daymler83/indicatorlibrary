# routers/permissions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User, Permission
from db import SessionLocal
from auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["permissions"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{user_id}/permissions")
def assign_permission(
    user_id: int,
    permission_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if current user has manage_users permission
    if "manage_users" not in [p.name for p in current_user.permissions]:
        raise HTTPException(status_code=403, detail="You do not have permission to manage users.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    permission = db.query(Permission).filter(Permission.name == permission_name).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found.")

    if permission in user.permissions:
        return {"message": "User already has this permission."}

    user.permissions.append(permission)
    db.commit()

    return {"message": f"Permission '{permission_name}' assigned to user {user.email}"}
