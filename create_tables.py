# create_tables.py
from models import Base
from db import engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables created!")
