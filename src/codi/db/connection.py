"""Configuración de la conexión a PostgreSQL mediante SQLAlchemy."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Carga el .env desde la raíz del proyecto (dos niveles arriba de este archivo)
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_PATH, override=True)


def _build_url() -> str:
    host     = os.getenv("DB_HOST", "localhost")
    port     = os.getenv("DB_PORT", "5433")
    name     = os.getenv("DB_NAME", "congreso2026")
    user     = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "1234")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


engine = create_engine(
    _build_url(),
    echo=False,
    pool_pre_ping=True,   # verifica la conexión antes de usarla
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


def get_session():
    """Context manager / generador de sesión.

    Uso:
        with get_session() as session:
            session.execute(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    """Verifica que la base de datos sea alcanzable. Retorna True si OK."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
