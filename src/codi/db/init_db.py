"""Script de inicialización para crear las tablas en la base de datos."""

from codi.db.connection import engine, Base
# Importar todos los modelos para que Base los registre
from codi.db.models import Cargue, Validacion, Novedad


def init_db():
    """Crea todas las tablas definidas en los modelos de SQLAlchemy."""
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente.")


if __name__ == "__main__":
    init_db()
