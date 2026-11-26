import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg://postgres:postgres@localhost:5432/service_desk',
)

engine = create_engine(DATABASE_URL,
                       pool_pre_ping=True)  # можно добавть параметр connect_args={"options": "-c client_encoding=UTF8 -c lc_messages=C"}
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
