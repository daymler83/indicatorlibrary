# delete_user.py

from db import SessionLocal
from models import User

def delete_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found.")
            return
        db.delete(user)
        db.commit()
        print(f"✅ User '{email}' deleted.")
    finally:
        db.close()

if __name__ == "__main__":
    delete_user("daymler.ofarrill@gmail.com")
