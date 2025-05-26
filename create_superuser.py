# create_superuser.py

from sqlalchemy.orm import Session
from db import SessionLocal
from models import User, Permission
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_superuser(email, password, full_name=""):
    db: Session = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if user:
            print("⚠️ User already exists.")
            return

        # Create user
        hashed_pw = get_password_hash(password)
        user = User(email=email, password_hash=hashed_pw, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Assign all permissions
        all_permissions = db.query(Permission).all()
        user.permissions = all_permissions
        db.commit()

        print(f"✅ Superuser '{email}' created with ALL permissions.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # CHANGE THESE:
    create_superuser("user@industry.gov.sa", "data2025", "Admin User")
