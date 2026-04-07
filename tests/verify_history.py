"""Script de verificación para el flujo de historial desde la base de datos."""

import sys
import os
from datetime import datetime, timedelta

# Asegurar que el src está en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from codi.db.connection import engine, SessionLocal, Base
from codi.db.models import Cargue, Validacion
from codi.db.init_db import init_db
from codi.core.history_service import fetch_history


def verify():
    # 1. Inicializar DB
    init_db()

    # 2. Insertar registro de prueba
    with SessionLocal() as session:
        # Limpiar datos previos de prueba para tener un estado conocido
        # (Opcional, pero útil para que el test sea determinista)
        # session.query(Validacion).delete()
        # session.query(Cargue).delete()
        
        now = datetime.now()
        cargue = Cargue(
            tipo_cargue="Test Cargue",
            archivo="test_file.csv",
            exitoso=True,
            registros_total=100,
            registros_validos=95,
            registros_rechazados=5,
            fecha_inicio=now - timedelta(minutes=5),
            fecha_fin=now,
        )
        session.add(cargue)
        session.flush() # Para obtener el ID

        val1 = Validacion(
            cargue_id=cargue.id,
            nombre="Validación Test 1",
            exitosa=True,
            registros_afectados=0
        )
        val2 = Validacion(
            cargue_id=cargue.id,
            nombre="Validación Test 2",
            exitosa=False,
            registros_afectados=5
        )
        session.add_all([val1, val2])
        session.commit()
        print(f"Registro de prueba insertado (ID: {cargue.id})")

    # 3. Recuperar via history_service
    history = fetch_history()
    
    found = False
    for entry in history:
        if entry.tipo_cargue == "Test Cargue" and entry.archivo == "test_file.csv":
            found = True
            print("¡Éxito! Se encontró el registro en el historial.")
            print(f"Detalles: {entry.registros_total} registros, {len(entry.validaciones)} validaciones.")
            print(f"Duración calculada: {entry.duracion}")
            
            # Verificar validaciones
            names = [v.nombre for v in entry.validaciones]
            if "Validación Test 1" in names and "Validación Test 2" in names:
                print("Validaciones recuperadas correctamente.")
            else:
                print("Error: No se recuperaron todas las validaciones.")
            break
    
    if not found:
        print("Error: No se encontró el registro insertado.")
        sys.exit(1)


if __name__ == "__main__":
    verify()
