from __future__ import annotations #serve per permettere di usare i tipi di dati che non sono ancora stati definiti, come Post all'interno della classe User e User all'interno della classe Post in python 3.14 non serve.

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import della base comune al database definita in database.py.
from database import Base


class User(Base):
    __tablename__ = "users"

    # Colonne della tabella users.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )

    # Relazione: un utente può avere molti post.
    posts: Mapped[list[Post]] = relationship(back_populates="author")

    @property
    def image_path(self) -> str:
        # Restituisce il percorso dell'immagine del profilo,
        # oppure un percorso di default se non è presente.
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"

    # Colonne della tabella posts.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    # La data di pubblicazione viene salvata con timezone UTC.
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    author: Mapped[User] = relationship(back_populates="posts")