"""Servicio de datos para el Tablero de Producción de Impresión."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import text

from codi.db.connection import engine

TOTAL_KITS = 125_260

# ── Prefijos que aparecen en imp_tetiquetas (columna RFID del tablero) ──────
PREFIJOS_RFID: list[str] = ['44', '46', '47', '48', '49', '93', '94', '95', '97']

# ── Prefijos que aparecen en imp_trfid pero NO son tarjetas electorales ──────
PREFIJOS_ESTANDAR: list[str] = [
    '20', '45', '52', '53', '90', '91', '92', '98', '99', 'C1', 'DE', 'DF', 'EE', 'F0',
]

# ── Consultas SQL ─────────────────────────────────────────────────────────────

_SQL_NOMBRES_TARJETAS = """
SELECT rep_cprefijo, rep_ctitulo
FROM   configura.ele_preportes
WHERE  rep_ctipo = 'RTC'
ORDER  BY rep_norden
"""

_SQL_TOTAL_ASIGNADO = """
SELECT pub_cprefijo,
       pub_cplanta,
       COUNT(*) AS total
FROM   impresion.pub_ttarjetas_x_planta
GROUP  BY pub_cprefijo, pub_cplanta
"""

_SQL_BLOQUES_PLANTAS = """
WITH kits AS (
    SELECT DISTINCT r.imp_cprefijo,
                    p.pub_cplanta,
                    r.div_nkit
    FROM  impresion.imp_trfid             r
    JOIN  impresion.pub_ttarjetas_x_planta p
          ON  p.pub_nkit    = r.div_nkit
          AND p.pub_cprefijo = r.imp_cprefijo
    WHERE r.val_ncodigo = 0
),
islands AS (
    SELECT imp_cprefijo,
           pub_cplanta,
           div_nkit,
           div_nkit - ROW_NUMBER() OVER (
               PARTITION BY imp_cprefijo, pub_cplanta
               ORDER BY div_nkit
           ) AS grp
    FROM kits
)
SELECT imp_cprefijo,
       pub_cplanta,
       MIN(div_nkit) AS bloque_ini,
       MAX(div_nkit) AS bloque_fin
FROM   islands
GROUP  BY imp_cprefijo, pub_cplanta, grp
ORDER  BY imp_cprefijo, pub_cplanta, bloque_ini
"""


def _sql_bloques_etiquetas(prefijos: list[str], tabla: str) -> str:
    lista = ", ".join(f"'{p}'" for p in prefijos)
    return f"""
WITH kits AS (
    SELECT DISTINCT imp_cprefijo, div_nkit
    FROM   {tabla}
    WHERE  val_ncodigo = 0
      AND  imp_cprefijo IN ({lista})
),
islands AS (
    SELECT imp_cprefijo,
           div_nkit,
           div_nkit - ROW_NUMBER() OVER (
               PARTITION BY imp_cprefijo ORDER BY div_nkit
           ) AS grp
    FROM kits
)
SELECT imp_cprefijo,
       MIN(div_nkit) AS bloque_ini,
       MAX(div_nkit) AS bloque_fin
FROM   islands
GROUP  BY imp_cprefijo, grp
ORDER  BY imp_cprefijo, bloque_ini
"""


def _sql_titulos_elementos(prefijos: list[str]) -> str:
    lista = ", ".join(f"'{p}'" for p in prefijos)
    return f"""
SELECT ele_cprefijo,
       ele_celemento
FROM   certificacion.ele_pelem_ctrl
WHERE  ele_cprefijo IN ({lista})
"""


# ── Dataclasses de salida ─────────────────────────────────────────────────────

@dataclass
class Bloque:
    ini: int
    fin: int


@dataclass
class FilaPlanta:
    planta: str
    bloques: list[Bloque] = field(default_factory=list)
    total_asignado: int = 0

    @property
    def kits_impresos(self) -> int:
        return sum(b.fin - b.ini + 1 for b in self.bloques)


@dataclass
class GrupoTarjeta:
    prefijo: str
    titulo: str
    plantas: list[FilaPlanta] = field(default_factory=list)


@dataclass
class FilaElemento:
    prefijo: str
    titulo: str
    bloques: list[Bloque] = field(default_factory=list)

    @property
    def kits_impresos(self) -> int:
        return sum(b.fin - b.ini + 1 for b in self.bloques)


@dataclass
class DatosTablero:
    tarjetas: list[GrupoTarjeta] = field(default_factory=list)
    rfid: list[FilaElemento] = field(default_factory=list)
    estandar: list[FilaElemento] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DetalleElemento:
    prefijo: str
    titulo: str
    reimpresos: int
    errores: int
    fecha_inicio: datetime | None
    fecha_ultimo: datetime | None
    n_impresoras: int
    impresoras: list[str]
    n_usuarios: int


# ── Consultas de detalle ──────────────────────────────────────────────────────

_SQL_DETALLE = """
SELECT
    (SELECT COUNT(*) FROM (
        SELECT div_nkit FROM {tabla}
        WHERE  imp_cprefijo = :pref AND val_ncodigo = 0
        GROUP  BY div_nkit HAVING COUNT(*) > 1
    ) r)                                     AS reimpresos,
    (SELECT COUNT(DISTINCT div_nkit) FROM {tabla}
     WHERE  imp_cprefijo = :pref AND val_ncodigo != 0) AS errores,
    MIN(imp_impreso)                          AS fecha_inicio,
    MAX(imp_impreso)                          AS fecha_ultimo,
    COUNT(DISTINCT imp_cimpresora)            AS n_impresoras,
    COUNT(DISTINCT imp_usuario)               AS n_usuarios
FROM {tabla}
WHERE imp_cprefijo = :pref AND val_ncodigo = 0
"""

_SQL_IMPRESORAS = """
SELECT DISTINCT imp_cimpresora
FROM   {tabla}
WHERE  imp_cprefijo = :pref
  AND  val_ncodigo  = 0
  AND  imp_cimpresora IS NOT NULL
ORDER  BY imp_cimpresora
"""


def cargar_detalle(prefijo: str, titulo: str, tabla: str) -> DetalleElemento:
    """Carga estadísticas de detalle para un elemento/tarjeta."""
    sql_det = _SQL_DETALLE.format(tabla=tabla)
    sql_imp = _SQL_IMPRESORAS.format(tabla=tabla)
    with engine.connect() as conn:
        row = conn.execute(text(sql_det), {"pref": prefijo}).fetchone()
        impresoras = [
            r.imp_cimpresora
            for r in conn.execute(text(sql_imp), {"pref": prefijo})
        ]
    return DetalleElemento(
        prefijo=prefijo,
        titulo=titulo,
        reimpresos=int(row.reimpresos or 0),
        errores=int(row.errores or 0),
        fecha_inicio=row.fecha_inicio,
        fecha_ultimo=row.fecha_ultimo,
        n_impresoras=int(row.n_impresoras or 0),
        impresoras=impresoras,
        n_usuarios=int(row.n_usuarios or 0),
    )


# ── Función principal ─────────────────────────────────────────────────────────

def cargar_datos() -> DatosTablero:
    """Ejecuta todas las consultas y devuelve un DatosTablero listo para pintar."""
    with engine.connect() as conn:

        # 1. Nombres de tarjetas
        nombres: dict[str, str] = {
            row.rep_cprefijo: row.rep_ctitulo
            for row in conn.execute(text(_SQL_NOMBRES_TARJETAS))
        }

        # 2. Total asignado por prefijo+planta
        total_asignado: dict[tuple[str, str], int] = {
            (row.pub_cprefijo, row.pub_cplanta): row.total
            for row in conn.execute(text(_SQL_TOTAL_ASIGNADO))
        }

        # 3. Bloques impresos por tarjeta+planta
        bloques_plantas: dict[tuple[str, str], list[Bloque]] = {}
        for row in conn.execute(text(_SQL_BLOQUES_PLANTAS)):
            key = (row.imp_cprefijo, row.pub_cplanta)
            bloques_plantas.setdefault(key, []).append(Bloque(row.bloque_ini, row.bloque_fin))

        # 4. Bloques RFID (imp_tetiquetas)
        titulos_rfid: dict[str, str] = {
            row.ele_cprefijo: row.ele_celemento
            for row in conn.execute(text(
                _sql_titulos_elementos(PREFIJOS_RFID)
            ))
        }
        bloques_rfid: dict[str, list[Bloque]] = {}
        for row in conn.execute(text(
            _sql_bloques_etiquetas(PREFIJOS_RFID, 'impresion.imp_tetiquetas')
        )):
            bloques_rfid.setdefault(row.imp_cprefijo, []).append(
                Bloque(row.bloque_ini, row.bloque_fin)
            )

        # 5. Bloques Estándar (imp_trfid, no tarjetas)
        titulos_est: dict[str, str] = {
            row.ele_cprefijo: row.ele_celemento
            for row in conn.execute(text(
                _sql_titulos_elementos(PREFIJOS_ESTANDAR)
            ))
        }
        bloques_est: dict[str, list[Bloque]] = {}
        for row in conn.execute(text(
            _sql_bloques_etiquetas(PREFIJOS_ESTANDAR, 'impresion.imp_trfid')
        )):
            bloques_est.setdefault(row.imp_cprefijo, []).append(
                Bloque(row.bloque_ini, row.bloque_fin)
            )

    # ── Armar estructura de salida ────────────────────────────────────────────

    # Tarjetas: sólo las que tienen datos en pub_ttarjetas_x_planta
    prefijos_con_datos = {k[0] for k in total_asignado}
    tarjetas: list[GrupoTarjeta] = []
    for prefijo, titulo in nombres.items():
        if prefijo not in prefijos_con_datos:
            continue
        plantas_del_grupo = sorted({k[1] for k in total_asignado if k[0] == prefijo})
        grupo = GrupoTarjeta(prefijo=prefijo, titulo=titulo)
        for planta in plantas_del_grupo:
            fila = FilaPlanta(
                planta=planta,
                bloques=bloques_plantas.get((prefijo, planta), []),
                total_asignado=total_asignado.get((prefijo, planta), 0),
            )
            grupo.plantas.append(fila)
        tarjetas.append(grupo)

    # RFID (orden fijo del tablero)
    rfid: list[FilaElemento] = [
        FilaElemento(
            prefijo=p,
            titulo=titulos_rfid.get(p, p),
            bloques=bloques_rfid.get(p, []),
        )
        for p in PREFIJOS_RFID
        if p in titulos_rfid
    ]

    # Estándar (orden fijo del tablero)
    estandar: list[FilaElemento] = [
        FilaElemento(
            prefijo=p,
            titulo=titulos_est.get(p, p),
            bloques=bloques_est.get(p, []),
        )
        for p in PREFIJOS_ESTANDAR
        if p in titulos_est
    ]

    return DatosTablero(tarjetas=tarjetas, rfid=rfid, estandar=estandar)
