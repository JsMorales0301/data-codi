"""Servicio para obtener y mapear el historial de cargues desde la base de datos."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from codi.db.connection import SessionLocal
from codi.db.models import Cargue, Validacion
from codi.ui.views.historial_panel import HistorialEntry, ValidacionResult


def _format_duration(start: datetime, end: Optional[datetime]) -> str:
    """Calcula y formatea la duración entre dos fechas."""
    if not end:
        return "En curso"
    
    delta = end - start
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


def fetch_history() -> List[HistorialEntry]:
    """Consulta la base de datos y retorna el historial mapeado a los dataclasses de la UI."""
    with SessionLocal() as session:
        # Consulta con carga adelantada de validaciones
        stmt = (
            select(Cargue)
            .options(selectinload(Cargue.validaciones))
            .order_by(Cargue.fecha_inicio.desc())
        )
        cargues = session.execute(stmt).scalars().all()
        
        history = []
        for c in cargues:
            # Mapear validaciones
            validaciones_res = [
                ValidacionResult(
                    nombre=v.nombre,
                    exitosa=v.exitosa,
                    registros_afectados=v.registros_afectados
                )
                for v in c.validaciones
            ]
            
            # Crear entrada de historial
            entry = HistorialEntry(
                tipo_cargue=c.tipo_cargue,
                exitoso=c.exitoso,
                fecha_inicio=c.fecha_inicio.strftime("%Y-%m-%d %H:%M:%S"),
                fecha_fin=c.fecha_fin.strftime("%Y-%m-%d %H:%M:%S") if c.fecha_fin else "",
                duracion=_format_duration(c.fecha_inicio, c.fecha_fin),
                archivo=c.archivo,
                registros_total=c.registros_total,
                registros_validos=c.registros_validos,
                registros_rechazados=c.registros_rechazados,
                validaciones=validaciones_res,
                error_detalle=c.error_detalle
            )
            history.append(entry)
            
        return history
