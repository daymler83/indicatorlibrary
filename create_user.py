# create_user.py

from db import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(email, password, full_name=""):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print("User already exists.")
            return
        hashed_pw = pwd_context.hash(password)
        user = User(email=email, password_hash=hashed_pw, full_name=full_name)
        db.add(user)
        db.commit()
        print(f"✅ Created user: {email}")
    finally:
        db.close()

if __name__ == "__main__":
    create_user("dofarrill@minpublico.cl", "Alma2025", "Regular User")
