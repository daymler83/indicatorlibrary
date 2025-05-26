import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base 

# Usa la URL del entorno si existe, si no usa la local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql:///indicator_system_db")

# Si Heroku usa postgres://, arreglamos eso para SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 👇 Create tables based on models if they don't exist
Base.metadata.create_all(bind=engine)