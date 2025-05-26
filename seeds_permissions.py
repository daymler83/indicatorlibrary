# seed_permissions.py

from sqlalchemy.orm import Session
from db import SessionLocal  # from your db.py
from models import Permission, DEFAULT_PERMISSIONS  # from your models.py

def seed_permissions():
    db: Session = SessionLocal()
    try:
        for perm in DEFAULT_PERMISSIONS:
            exists = db.query(Permission).filter(Permission.name == perm["name"]).first()
            if not exists:
                new_perm = Permission(name=perm["name"], description=perm["description"])
                db.add(new_perm)
                print(f"✅ Inserted permission: {perm['name']}")
            else:
                print(f"ℹ️ Already exists: {perm['name']}")
        db.commit()
        print("🎉 Permissions seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error while seeding permissions: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_permissions()
