from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QSplitter, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush

from codi.ui.styles import TABLE_STYLE as _TABLE_STYLE

# ── Modelos ───────────────────────────────────────────────────────────────────

@dataclass
class RegistroNovedad:
    campos: dict[str, str]
    campos_anterior: dict[str, str] | None = None   # None = registro nuevo
    linea_anterior: int | None = None
    linea_nueva: int | None = None


@dataclass
class Novedad:
    titulo: str
    descripcion: str
    tipo: str                                    # "informativa" | "bloqueante" | "comparacion"
    registros: list[RegistroNovedad] = field(default_factory=list)


# ── Demo data ─────────────────────────────────────────────────────────────────

DEMO_NOVEDADES: list[Novedad] = [
    Novedad(
        titulo="Doble militancia",
        descripcion="Candidatos registrados en más de un partido político.",
        tipo="bloqueante",
        registros=[
            RegistroNovedad({"numero_identificacion": "10234567", "primer_nombre": "Carlos",
                             "primer_apellido": "Gómez", "codigo_partido": "001 / 004",
                             "nombre_partido": "Partido A / Partido D"}),
            RegistroNovedad({"numero_identificacion": "98765432", "primer_nombre": "María",
                             "primer_apellido": "Torres", "codigo_partido": "002 / 005",
                             "nombre_partido": "Partido B / Partido E"}),
        ],
    ),
    Novedad(
        titulo="Rango inválido: numero_candidato",
        descripcion="El número de candidato está fuera del rango permitido (1-999).",
        tipo="bloqueante",
        registros=[
            RegistroNovedad({"numero_candidato": "1050", "primer_nombre": "Luis",
                             "primer_apellido": "Pérez", "codigo_municipio": "05001"}),
        ],
    ),
    Novedad(
        titulo="Género no reconocido",
        descripcion="El campo genero_candidato contiene un valor diferente a M o F.",
        tipo="informativa",
        registros=[
            RegistroNovedad({"numero_identificacion": "55512345", "primer_nombre": "Alex",
                             "primer_apellido": "Ruiz", "genero_candidato": "X"}),
            RegistroNovedad({"numero_identificacion": "55598765", "primer_nombre": "Jordan",
                             "primer_apellido": "Mora", "genero_candidato": "N/A"}),
            RegistroNovedad({"numero_identificacion": "55511111", "primer_nombre": "Sam",
                             "primer_apellido": "Díaz", "genero_candidato": ""}),
        ],
    ),
    Novedad(
        titulo="Segundo nombre vacío",
        descripcion="El campo segundo_nombre no tiene valor. No es bloqueante.",
        tipo="informativa",
        registros=[
            RegistroNovedad({"numero_identificacion": "11122233", "primer_nombre": "Ana",
                             "primer_apellido": "Castro", "segundo_nombre": ""}),
        ],
    ),
    # ── Novedades de comparación (archivo anterior vs nuevo) ──────────────────
    Novedad(
        titulo="Candidatos modificados",
        descripcion="Registros que presentan cambios respecto al archivo anterior cargado en BD.",
        tipo="comparacion",
        registros=[
            RegistroNovedad(
                campos={
                    "numero_identificacion": "10234567",
                    "primer_nombre": "Carlos",
                    "primer_apellido": "Gómez",
                    "codigo_partido": "004",
                    "nombre_partido": "Partido D",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "M",
                },
                campos_anterior={
                    "numero_identificacion": "10234567",
                    "primer_nombre": "Carlos",
                    "primer_apellido": "Gomez",
                    "codigo_partido": "001",
                    "nombre_partido": "Partido A",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "M",
                },
                linea_anterior=45,
                linea_nueva=47,
            ),
            RegistroNovedad(
                campos={
                    "numero_identificacion": "55512345",
                    "primer_nombre": "Alexandra",
                    "primer_apellido": "Ruiz",
                    "codigo_partido": "002",
                    "nombre_partido": "Partido B",
                    "estado_lista": "RETIRADO",
                    "genero_candidato": "F",
                },
                campos_anterior={
                    "numero_identificacion": "55512345",
                    "primer_nombre": "Alex",
                    "primer_apellido": "Ruiz",
                    "codigo_partido": "002",
                    "nombre_partido": "Partido B",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "F",
                },
                linea_anterior=112,
                linea_nueva=109,
            ),
        ],
    ),
    Novedad(
        titulo="Nuevos candidatos",
        descripcion="Candidatos presentes en el archivo nuevo que no existían en el archivo anterior.",
        tipo="comparacion",
        registros=[
            RegistroNovedad(
                campos={
                    "numero_identificacion": "99988877",
                    "primer_nombre": "Laura",
                    "primer_apellido": "Mendez",
                    "codigo_partido": "003",
                    "nombre_partido": "Partido C",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "F",
                },
                campos_anterior=None,
                linea_nueva=318,
            ),
            RegistroNovedad(
                campos={
                    "numero_identificacion": "44433322",
                    "primer_nombre": "Ricardo",
                    "primer_apellido": "Pinto",
                    "codigo_partido": "005",
                    "nombre_partido": "Partido E",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "M",
                },
                campos_anterior=None,
                linea_nueva=319,
            ),
        ],
    ),
    Novedad(
        titulo="Candidatos retirados",
        descripcion="Candidatos presentes en el archivo anterior que no aparecen en el archivo nuevo.",
        tipo="comparacion",
        registros=[
            RegistroNovedad(
                campos={},
                campos_anterior={
                    "numero_identificacion": "11100022",
                    "primer_nombre": "Roberto",
                    "primer_apellido": "Vargas",
                    "codigo_partido": "001",
                    "nombre_partido": "Partido A",
                    "estado_lista": "ACTIVO",
                    "genero_candidato": "M",
                },
                linea_anterior=88,
            ),
        ],
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text: str, pt: int = 9, bold: bool = False,
         color: str | None = None) -> QLabel:
    l = QLabel(text)
    f = QFont()
    f.setPointSize(pt)
    f.setBold(bold)
    l.setFont(f)
    if color:
        l.setStyleSheet(f"color:{color};")
    return l


def _hsep() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


# ── Item de novedad ───────────────────────────────────────────────────────────

class _NovedadItem(QFrame):
    _COLOR_BLOQUEANTE  = "#e74c3c"
    _COLOR_INFORMATIVA = "#f39c12"
    _COLOR_COMPARACION = "#2980b9"

    def __init__(
        self,
        novedad: Novedad,
        on_click: Callable[[Novedad, "_NovedadItem"], None],
        parent=None,
    ):
        super().__init__(parent)
        self._novedad = novedad
        self._on_click = on_click
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        if self._novedad.tipo == "bloqueante":
            color = self._COLOR_BLOQUEANTE
        elif self._novedad.tipo == "comparacion":
            color = self._COLOR_COMPARACION
        else:
            color = self._COLOR_INFORMATIVA

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background-color:{color};border-radius:2px;")
        layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(_lbl(self._novedad.titulo, pt=9, bold=True))
        count = len(self._novedad.registros)
        info.addWidget(_lbl(f"{count} registro{'s' if count != 1 else ''}", pt=8))
        layout.addLayout(info)
        layout.addStretch()

    def set_selected(self, selected: bool):
        self.setStyleSheet("background-color:#e8f4fd;" if selected else "")

    def mousePressEvent(self, event):
        self._on_click(self._novedad, self)
        super().mousePressEvent(event)


# ── Panel izquierdo: lista de novedades ───────────────────────────────────────

class _NovedadesListPanel(QWidget):
    def __init__(
        self,
        novedades: list[Novedad],
        on_select: Callable[[Novedad, _NovedadItem], None],
        parent=None,
    ):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self._build(novedades, on_select)

    def _build(self, novedades: list[Novedad],
               on_select: Callable[[Novedad, _NovedadItem], None]):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)

        bloqueantes   = [n for n in novedades if n.tipo == "bloqueante"]
        informativas  = [n for n in novedades if n.tipo == "informativa"]
        comparaciones = [n for n in novedades if n.tipo == "comparacion"]

        if bloqueantes:
            header = _lbl(f"Bloqueantes ({len(bloqueantes)})", pt=9, bold=True,
                          color="#c0392b")
            header.setContentsMargins(2, 4, 0, 4)
            vbox.addWidget(header)
            for n in bloqueantes:
                vbox.addWidget(_NovedadItem(n, on_select))
            vbox.addWidget(_hsep())

        if informativas:
            header = _lbl(f"Informativas ({len(informativas)})", pt=9, bold=True,
                          color="#d68910")
            header.setContentsMargins(2, 4, 0, 4)
            vbox.addWidget(header)
            for n in informativas:
                vbox.addWidget(_NovedadItem(n, on_select))

        if comparaciones:
            if bloqueantes or informativas:
                vbox.addWidget(_hsep())
            header = _lbl(f"Comparación ({len(comparaciones)})", pt=9, bold=True,
                          color="#2471a3")
            header.setContentsMargins(2, 4, 0, 4)
            vbox.addWidget(header)
            for n in comparaciones:
                vbox.addWidget(_NovedadItem(n, on_select))

        vbox.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)


# ── Panel derecho: detalle de novedad ─────────────────────────────────────────

class _NovedadDetailPanel(QWidget):
    # Colores para la tabla diff
    _C_HEADER_BG   = QColor("#dce8f7")
    _C_CHANGED_BG  = QColor("#fff8e1")
    _C_CHANGED_FG  = QColor("#c0392b")   # valor nuevo cambiado → rojo
    _C_CHANGED_OLD = QColor("#999999")   # valor anterior → gris
    _C_NEW_BG      = QColor("#eafaf1")
    _C_NEW_FG      = QColor("#1e8449")
    _C_REM_BG      = QColor("#fdedec")
    _C_REM_FG      = QColor("#922b21")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20, 16, 20, 16)
        self._root.setSpacing(12)

        self._empty = _lbl("Selecciona una novedad para ver el detalle", pt=10)
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._root.addWidget(self._empty)
        self._root.addStretch()

        self._detail = QWidget()
        detail_layout = QVBoxLayout(self._detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)

        self._titulo_lbl = _lbl("", pt=11, bold=True)
        detail_layout.addWidget(self._titulo_lbl)

        self._desc_lbl = _lbl("", pt=9)
        self._desc_lbl.setWordWrap(True)
        detail_layout.addWidget(self._desc_lbl)

        detail_layout.addWidget(_hsep())

        self._count_lbl = _lbl("", pt=9, bold=True)
        detail_layout.addWidget(self._count_lbl)

        # Tabla estándar (bloqueante / informativa)
        self._table = QTableWidget()
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setStyleSheet(_TABLE_STYLE)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        detail_layout.addWidget(self._table, stretch=1)

        # Tabla diff (comparacion)
        self._diff_table = QTableWidget()
        self._diff_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._diff_table.setAlternatingRowColors(False)
        self._diff_table.setShowGrid(True)
        self._diff_table.setStyleSheet(_TABLE_STYLE)
        self._diff_table.verticalHeader().setVisible(False)
        self._diff_table.setColumnCount(3)
        self._diff_table.setHorizontalHeaderLabels(["Campo", "Anterior", "Nuevo"])
        h = self._diff_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._diff_table.setColumnWidth(0, 200)
        detail_layout.addWidget(self._diff_table, stretch=1)

        self._detail.hide()
        self._root.insertWidget(0, self._detail)

    # ── API pública ───────────────────────────────────────────────────────────

    def show_novedad(self, novedad: Novedad):
        self._empty.hide()
        self._detail.show()

        self._titulo_lbl.setText(novedad.titulo)
        self._desc_lbl.setText(novedad.descripcion)
        count = len(novedad.registros)
        self._count_lbl.setText(f"Registros afectados: {count}")

        if novedad.tipo == "comparacion":
            self._table.hide()
            self._diff_table.show()
            self._populate_diff_table(novedad)
        else:
            self._diff_table.hide()
            self._populate_standard_table(novedad)
            self._table.show()

    def _populate_standard_table(self, novedad: Novedad):
        if not novedad.registros:
            self._table.hide()
            return
        campos = list(novedad.registros[0].campos.keys())
        self._table.setColumnCount(len(campos))
        self._table.setHorizontalHeaderLabels(campos)
        self._table.setRowCount(len(novedad.registros))
        for row, registro in enumerate(novedad.registros):
            for col, key in enumerate(campos):
                self._table.setItem(row, col, QTableWidgetItem(registro.campos.get(key, "")))

    def _populate_diff_table(self, novedad: Novedad):
        # Construir lista plana de filas: (kind, ...)
        rows: list[tuple] = []

        for registro in novedad.registros:
            ant = registro.campos_anterior or {}
            new = registro.campos

            # Identificador del registro para la fila de cabecera
            ident = (new or ant).get("numero_identificacion", "")
            nombre = (
                f"{(new or ant).get('primer_nombre', '')} "
                f"{(new or ant).get('primer_apellido', '')}"
            ).strip()

            # Sufijo de línea(s)
            if registro.linea_anterior is not None and registro.linea_nueva is not None:
                linea_info = f"  ·  línea ant. {registro.linea_anterior}  →  línea nueva {registro.linea_nueva}"
            elif registro.linea_nueva is not None:
                linea_info = f"  ·  línea {registro.linea_nueva}"
            elif registro.linea_anterior is not None:
                linea_info = f"  ·  línea ant. {registro.linea_anterior}"
            else:
                linea_info = ""

            if not new:                          # registro eliminado
                rows.append(("header_rem", f"⛔  {nombre}  ·  {ident}  —  Retirado{linea_info}"))
                for campo, val in ant.items():
                    rows.append(("rem", campo, val, "—"))

            elif not ant:                        # registro nuevo
                rows.append(("header_new", f"✅  {nombre}  ·  {ident}  —  Nuevo{linea_info}"))
                for campo, val in new.items():
                    rows.append(("new", campo, "—", val))

            else:                                # registro modificado
                rows.append(("header_mod", f"✏️   {nombre}  ·  {ident}  —  Modificado{linea_info}"))
                all_fields = list(ant.keys())
                for campo in all_fields:
                    ant_val = ant.get(campo, "—")
                    new_val = new.get(campo, "—")
                    kind = "changed" if ant_val != new_val else "same"
                    rows.append((kind, campo, ant_val, new_val))

        self._diff_table.setRowCount(len(rows))

        bold_font = QFont()
        bold_font.setBold(True)

        for i, row in enumerate(rows):
            kind = row[0]

            if kind.startswith("header"):
                bg = {
                    "header_rem": self._C_REM_BG,
                    "header_new": self._C_NEW_BG,
                    "header_mod": self._C_HEADER_BG,
                }[kind]
                item = QTableWidgetItem(row[1])
                item.setBackground(QBrush(bg))
                item.setFont(bold_font)
                self._diff_table.setItem(i, 0, item)
                self._diff_table.setSpan(i, 0, 1, 3)
                self._diff_table.setRowHeight(i, 26)

            else:
                _, campo, ant_val, new_val = row

                campo_item = QTableWidgetItem(campo)
                ant_item   = QTableWidgetItem(ant_val)
                new_item   = QTableWidgetItem(new_val)

                if kind == "changed":
                    for it in (campo_item, ant_item, new_item):
                        it.setBackground(QBrush(self._C_CHANGED_BG))
                    ant_item.setForeground(QBrush(self._C_CHANGED_OLD))
                    new_item.setForeground(QBrush(self._C_CHANGED_FG))
                    new_item.setFont(bold_font)

                elif kind == "new":
                    for it in (campo_item, ant_item, new_item):
                        it.setBackground(QBrush(self._C_NEW_BG))
                    new_item.setForeground(QBrush(self._C_NEW_FG))
                    new_item.setFont(bold_font)

                elif kind == "rem":
                    for it in (campo_item, ant_item, new_item):
                        it.setBackground(QBrush(self._C_REM_BG))
                    ant_item.setForeground(QBrush(self._C_REM_FG))

                self._diff_table.setItem(i, 0, campo_item)
                self._diff_table.setItem(i, 1, ant_item)
                self._diff_table.setItem(i, 2, new_item)


# ── Vista principal de novedades ──────────────────────────────────────────────

class NovedadesView(QWidget):
    def __init__(
        self,
        novedades: list[Novedad],
        on_continuar: Callable,
        on_cancelar: Callable,
        parent=None,
    ):
        super().__init__(parent)
        self._novedades = novedades
        self._on_continuar = on_continuar
        self._on_cancelar = on_cancelar
        self._selected_item: _NovedadItem | None = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Cabecera
        header = QWidget()
        header.setStyleSheet("background-color:#f8f9fa;")
        hbox = QHBoxLayout(header)
        hbox.setContentsMargins(20, 12, 20, 12)
        bloq  = sum(1 for n in self._novedades if n.tipo == "bloqueante")
        info  = sum(1 for n in self._novedades if n.tipo == "informativa")
        comp  = sum(1 for n in self._novedades if n.tipo == "comparacion")
        title = _lbl("Novedades del archivo", pt=11, bold=True)
        hbox.addWidget(title)
        hbox.addStretch()
        hbox.addWidget(_lbl(f"🔴 {bloq} bloqueante{'s' if bloq != 1 else ''}", pt=9))
        hbox.addSpacing(16)
        hbox.addWidget(_lbl(f"🟡 {info} informativa{'s' if info != 1 else ''}", pt=9))
        hbox.addSpacing(16)
        hbox.addWidget(_lbl(f"🔵 {comp} comparación", pt=9))
        root.addWidget(header)
        root.addWidget(_hsep())

        # Cuerpo: lista izquierda + detalle derecha
        self._detail_panel = _NovedadDetailPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(
            _NovedadesListPanel(self._novedades, self._on_item_click)
        )
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, stretch=1)

        root.addWidget(_hsep())

        # Barra de botones inferior
        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 10, 16, 10)
        btn_layout.setSpacing(8)

        btn_descargar = QPushButton("Descargar reportes")
        btn_descargar.setFixedWidth(150)
        btn_layout.addWidget(btn_descargar)

        btn_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedWidth(100)
        btn_cancelar.clicked.connect(self._on_cancelar)
        btn_layout.addWidget(btn_cancelar)

        has_bloqueantes = any(n.tipo == "bloqueante" for n in self._novedades)
        btn_continuar = QPushButton("Continuar")
        btn_continuar.setFixedWidth(100)
        btn_continuar.setEnabled(not has_bloqueantes)
        if has_bloqueantes:
            btn_continuar.setToolTip(
                "Existen novedades bloqueantes. Corrija el archivo antes de continuar."
            )
        btn_continuar.clicked.connect(self._on_continuar)
        btn_layout.addWidget(btn_continuar)

        root.addWidget(btn_bar)

    def _on_item_click(self, novedad: Novedad, widget: _NovedadItem):
        if self._selected_item:
            self._selected_item.set_selected(False)
        widget.set_selected(True)
        self._selected_item = widget
        self._detail_panel.show_novedad(novedad)
