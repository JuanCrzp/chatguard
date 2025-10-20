"""Infraestructura de base de datos opcional (SQLAlchemy).

No se usa por defecto. Los repos existentes siguen en memoria.
Puedes optar por usarlo en producción configurando DB_URL y creando las tablas.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DB_URL = os.getenv(
    "DB_URL",
    "sqlite:///./communityguard.db",  # fallback seguro en local
)

# pool_pre_ping para resiliencia con MySQL
engine = create_engine(DB_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
