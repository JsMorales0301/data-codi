from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QScrollArea, QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from codi.ui.styles import TABLE_STYLE as _TABLE_STYLE

# ── Modelos ───────────────────────────────────────────────────────────────────

@dataclass
class ValidacionResult:
    nombre: str
    exitosa: bool
    registros_afectados: int


@dataclass
class HistorialEntry:
    tipo_cargue: str
    exitoso: bool
    fecha_inicio: str
    fecha_fin: str
    duracion: str
    archivo: str
    registros_total: int
    registros_validos: int
    registros_rechazados: int
    validaciones: list[ValidacionResult] = field(default_factory=list)
    error_detalle: Optional[str] = None


# ── Demo data ─────────────────────────────────────────────────────────────────

DEMO_HISTORIAL: list[HistorialEntry] = [
    HistorialEntry(
        tipo_cargue="Candidatos",
        exitoso=True,
        fecha_inicio="2026-03-16 10:30:00",
        fecha_fin="2026-03-16 10:32:14",
        duracion="2m 14s",
        archivo="candidatos_2026.csv",
        registros_total=1250,
        registros_validos=1250,
        registros_rechazados=0,
        validaciones=[
            ValidacionResult("Campo no nulo: primer_nombre",          True,  0),
            ValidacionResult("Campo no nulo: numero_identificacion",  True,  0),
            ValidacionResult("Rango: numero_candidato (1-999)",       True,  0),
            ValidacionResult("Formato: genero_candidato (M/F)",       True,  0),
            ValidacionResult("Longitud: primer_nombre (máx. 100)",    True,  0),
        ],
    ),
    HistorialEntry(
        tipo_cargue="Divipol",
        exitoso=False,
        fecha_inicio="2026-03-15 14:22:00",
        fecha_fin="2026-03-15 14:23:41",
        duracion="1m 41s",
        archivo="divipol_marzo.txt",
        registros_total=890,
        registros_validos=748,
        registros_rechazados=142,
        validaciones=[
            ValidacionResult("Campo no nulo: codigo_departamento",    True,  0),
            ValidacionResult("Rango: codigo_municipio (1-9999)",      False, 142),
            ValidacionResult("Campo no nulo: nombre_municipio",       True,  0),
        ],
        error_detalle=(
            "Fila 45  → codigo_municipio: '99999' fuera de rango (1-9999)\n"
            "Fila 89  → codigo_municipio: '0' fuera de rango (1-9999)\n"
            "... (140 registros más con el mismo error)"
        ),
    ),
    HistorialEntry(
        tipo_cargue="Censo electoral",
        exitoso=True,
        fecha_inicio="2026-03-14 09:15:00",
        fecha_fin="2026-03-14 09:18:52",
        duracion="3m 52s",
        archivo="censo_electoral_2026.xlsx",
        registros_total=4800,
        registros_validos=4800,
        registros_rechazados=0,
        validaciones=[
            ValidacionResult("Campo no nulo: numero_identificacion",  True, 0),
            ValidacionResult("Longitud: codigo_departamento (2)",     True, 0),
            ValidacionResult("Formato: fecha_nacimiento (YYYY-MM-DD)",True, 0),
        ],
    ),
    HistorialEntry(
        tipo_cargue="Transportes",
        exitoso=False,
        fecha_inicio="2026-03-13 16:48:00",
        fecha_fin="2026-03-13 16:48:09",
        duracion="9s",
        archivo="transportes_jornada.csv",
        registros_total=0,
        registros_validos=0,
        registros_rechazados=0,
        validaciones=[],
        error_detalle="Error al leer el archivo: separador incorrecto. Se esperaba ',' pero el archivo usa ';'.",
    ),
    HistorialEntry(
        tipo_cargue="Curules",
        exitoso=True,
        fecha_inicio="2026-03-12 08:05:00",
        fecha_fin="2026-03-12 08:05:44",
        duracion="44s",
        archivo="curules_2026.csv",
        registros_total=320,
        registros_validos=320,
        registros_rechazados=0,
        validaciones=[
            ValidacionResult("Campo no nulo: codigo_corporacion",     True, 0),
            ValidacionResult("Campo no nulo: nombre_corporacion",     True, 0),
        ],
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text: str, pt: int = 9, bold: bool = False) -> QLabel:
    l = QLabel(text)
    f = QFont()
    f.setPointSize(pt)
    f.setBold(bold)
    l.setFont(f)
    return l


def _hsep() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


# ── Item de la lista ──────────────────────────────────────────────────────────

class HistorialItemWidget(QFrame):
    def __init__(
        self,
        entry: HistorialEntry,
        on_click: Callable[[HistorialEntry, "HistorialItemWidget"], None],
        parent=None,
    ):
        super().__init__(parent)
        self._entry = entry
        self._on_click = on_click
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._selected = False
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        color = "#2ecc71" if self._entry.exitoso else "#e74c3c"
        dot.setStyleSheet(f"background-color:{color};border-radius:2px;")
        layout.addWidget(dot)

        info = QVBoxLayout()
        info.setSpacing(1)
        info.addWidget(_lbl(self._entry.tipo_cargue, pt=9, bold=True))
        info.addWidget(_lbl(self._entry.fecha_inicio[:10], pt=8))
        layout.addLayout(info)
        layout.addStretch()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setStyleSheet(
            "background-color: #dce8f7;" if selected else ""
        )

    def mousePressEvent(self, event):
        self._on_click(self._entry, self)
        super().mousePressEvent(event)


# ── Tarjeta de métrica ────────────────────────────────────────────────────────

class _MetricCard(QFrame):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        layout.addWidget(_lbl(label, pt=8))
        self._value_lbl = _lbl("—", pt=11, bold=True)
        layout.addWidget(self._value_lbl)

    def set_value(self, value: str):
        self._value_lbl.setText(value)


# ── Panel de detalle ──────────────────────────────────────────────────────────

class HistorialDetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._show_empty()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(24, 20, 24, 24)
        self._layout.setSpacing(14)

        # — Placeholder vacío —
        self._empty_lbl = _lbl("Selecciona un ítem para ver el detalle", pt=10)
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._empty_lbl)
        self._layout.addStretch()

        # — Header —
        self._header = self._build_header()
        self._header.hide()
        self._layout.insertWidget(0, self._header)

        scroll.setWidget(self._content)
        root.addWidget(scroll)

    def _build_header(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(12)

        # Título + botones
        title_row = QHBoxLayout()
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(16, 16)
        title_row.addWidget(self._status_dot)

        self._title_lbl = _lbl("", pt=12, bold=True)
        title_row.addWidget(self._title_lbl)
        title_row.addStretch()

        btn_retry = QPushButton("Reintentar")
        btn_retry.setFixedWidth(100)
        title_row.addWidget(btn_retry)

        btn_download = QPushButton("Descargar reporte")
        btn_download.setFixedWidth(140)
        title_row.addWidget(btn_download)

        vbox.addLayout(title_row)

        self._archivo_lbl = _lbl("", pt=8)
        vbox.addWidget(self._archivo_lbl)
        vbox.addWidget(_hsep())

        # Métricas
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(8)
        self._cards: dict[str, _MetricCard] = {}
        for key, label in [
            ("inicio",      "Inicio"),
            ("fin",         "Fin"),
            ("duracion",    "Duración"),
            ("total",       "Total registros"),
            ("validos",     "Válidos"),
            ("rechazados",  "Rechazados"),
        ]:
            card = _MetricCard(label)
            self._cards[key] = card
            metrics_row.addWidget(card)

        vbox.addLayout(metrics_row)
        vbox.addWidget(_hsep())

        # Validaciones
        vbox.addWidget(_lbl("Validaciones aplicadas", pt=10, bold=True))
        self._val_table = self._build_val_table()
        vbox.addWidget(self._val_table)

        # Error
        self._error_frame = self._build_error_frame()
        self._error_frame.hide()
        vbox.addWidget(self._error_frame)

        return container

    def _build_val_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Validación", "Estado", "Registros afectados"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.setStyleSheet(_TABLE_STYLE)
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 160)
        return table

    def _build_error_frame(self) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(6)
        lbl = _lbl("Detalle del error", pt=10, bold=True)
        lbl.setStyleSheet("color: #c0392b;")
        vbox.addWidget(lbl)
        self._error_text = QTextEdit()
        self._error_text.setReadOnly(True)
        self._error_text.setMaximumHeight(120)
        self._error_text.setStyleSheet("background-color: #fdf2f2;")
        vbox.addWidget(self._error_text)
        return frame

    # ── API pública ───────────────────────────────────────────────────────────

    def show_entry(self, entry: HistorialEntry):
        self._empty_lbl.hide()
        self._header.show()

        # Dot + título
        color = "#2ecc71" if entry.exitoso else "#e74c3c"
        self._status_dot.setStyleSheet(
            f"background-color:{color};border-radius:3px;"
        )
        self._title_lbl.setText(entry.tipo_cargue)
        self._archivo_lbl.setText(f"Archivo: {entry.archivo}")

        # Métricas
        self._cards["inicio"].set_value(entry.fecha_inicio[11:])
        self._cards["fin"].set_value(entry.fecha_fin[11:])
        self._cards["duracion"].set_value(entry.duracion)
        self._cards["total"].set_value(str(entry.registros_total))
        self._cards["validos"].set_value(str(entry.registros_validos))
        self._cards["rechazados"].set_value(str(entry.registros_rechazados))

        # Validaciones
        self._val_table.setRowCount(len(entry.validaciones))
        for i, v in enumerate(entry.validaciones):
            self._val_table.setItem(i, 0, QTableWidgetItem(v.nombre))
            estado = "✅" if v.exitosa else "❌"
            item_estado = QTableWidgetItem(estado)
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._val_table.setItem(i, 1, item_estado)
            item_afect = QTableWidgetItem(str(v.registros_afectados))
            item_afect.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._val_table.setItem(i, 2, item_afect)

        # Error
        if entry.error_detalle:
            self._error_text.setPlainText(entry.error_detalle)
            self._error_frame.show()
        else:
            self._error_frame.hide()

    def _show_empty(self):
        self._empty_lbl.show()
        self._header.hide()
