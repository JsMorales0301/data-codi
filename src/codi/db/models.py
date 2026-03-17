"""Modelos ORM — tablas de la base de datos."""

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codi.db.connection import Base


class Cargue(Base):
    """Registro de cada ejecución de cargue de archivo."""

    __tablename__ = "cargues"

    id:                  Mapped[int]      = mapped_column(BigInteger, primary_key=True)
    tipo_cargue:         Mapped[str]      = mapped_column(String(64), nullable=False)
    archivo:             Mapped[str]      = mapped_column(String(512), nullable=False)
    separador:           Mapped[str]      = mapped_column(String(4), nullable=True)
    tiene_cabecera:      Mapped[bool]     = mapped_column(Boolean, nullable=False, default=True)
    exitoso:             Mapped[bool]     = mapped_column(Boolean, nullable=False)
    registros_total:     Mapped[int]      = mapped_column(Integer, nullable=False, default=0)
    registros_validos:   Mapped[int]      = mapped_column(Integer, nullable=False, default=0)
    registros_rechazados:Mapped[int]      = mapped_column(Integer, nullable=False, default=0)
    error_detalle:       Mapped[str|None] = mapped_column(Text, nullable=True)
    fecha_inicio:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fecha_fin:           Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)

    validaciones: Mapped[list["Validacion"]] = relationship(back_populates="cargue", cascade="all, delete-orphan")
    novedades:    Mapped[list["Novedad"]]    = relationship(back_populates="cargue", cascade="all, delete-orphan")


class Validacion(Base):
    """Resultado de una regla de validación aplicada en un cargue."""

    __tablename__ = "validaciones"

    id:                   Mapped[int]  = mapped_column(BigInteger, primary_key=True)
    cargue_id:            Mapped[int]  = mapped_column(ForeignKey("cargues.id"), nullable=False)
    nombre:               Mapped[str]  = mapped_column(String(256), nullable=False)
    exitosa:              Mapped[bool] = mapped_column(Boolean, nullable=False)
    registros_afectados:  Mapped[int]  = mapped_column(Integer, nullable=False, default=0)

    cargue: Mapped["Cargue"] = relationship(back_populates="validaciones")


class Novedad(Base):
    """Novedad detectada durante la validación de un cargue."""

    __tablename__ = "novedades"

    id:          Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cargue_id:   Mapped[int] = mapped_column(ForeignKey("cargues.id"), nullable=False)
    titulo:      Mapped[str] = mapped_column(String(256), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(
        Enum("bloqueante", "informativa", "comparacion", name="novedad_tipo"),
        nullable=False,
    )
    registros_afectados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    cargue: Mapped["Cargue"] = relationship(back_populates="novedades")
