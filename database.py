from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# URL di connessione al database SQLite locale.
SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

# Crea il motore di connessione a SQLite.
# check_same_thread=False è necessario solo per SQLite quando l'app usa più thread.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},#serve sono in sqlite, per altri db non serve perché non è multithread
)

# SessionLocal è una factory di sessioni che useremo per aprire/chiudere il DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    # Generatore che fornisce una sessione DB per ogni richiesta FastAPI.
    # La sessione viene chiusa automaticamente al termine del blocco with.
    with SessionLocal() as db:
        yield db


# Questa sezione contiene i modelli SQLAlchemy. In un progetto ordinato,
# sarebbe preferibile separarli in un file dedicated models.py.
## models.py
# Questa sezione definisce i modelli del database.
# Idealmente andrebbe spostata in un file separato models.py per evitare confusione.
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )

    # Relazione uno-a-molti: un utente può avere più post.
    posts: Mapped[list[Post]] = relationship(back_populates="author")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    author: Mapped[User] = relationship(back_populates="posts")