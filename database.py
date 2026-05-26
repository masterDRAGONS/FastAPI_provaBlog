"""
Modulo di configurazione del database.
Inizializza il motore SQLAlchemy, la factory di sessioni (`SessionLocal`) e la
`Base` dichiarativa usata da `models.py` per definire le tabelle.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(
    settings.database_url
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session