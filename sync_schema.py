# sync_schema.py
from models import Base
from db import engine

Base.metadata.create_all(bind=engine)
print("✅ Schema synced")
