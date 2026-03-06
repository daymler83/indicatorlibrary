'''
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
'''

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Usa DATABASE_URL si existe (Heroku o servidor), si no usa SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./indicator_system.db")

# Heroku a veces usa postgres:// en vez de postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configuración especial para SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)
