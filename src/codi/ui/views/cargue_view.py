import os
from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QFileDialog,
    QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QCheckBox, QHeaderView, QSizePolicy, QTabWidget,
    QSplitter, QScrollArea, QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush

from codi.ui.styles import TABLE_STYLE as _TABLE_STYLE


class _NoScrollComboBox(QComboBox):
    """QComboBox que ignora wheel events a menos que tenga foco."""
    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)


from codi.ui.views.historial_panel import (
    HistorialEntry, HistorialItemWidget, HistorialDetailPanel,
)
from codi.ui.views.novedades_view import NovedadesView, DEMO_NOVEDADES
from codi.core.history_service import fetch_history

# ── Datos ─────────────────────────────────────────────────────────────────────

TIPOS_CARGUE = [
    "",
    "Candidatos",
    "Censo electoral",
    "Curules",
    "Divipol",
    "Mesas de votación",
    "Puestos de votación",
    "Transportes",
]

SEPARADORES = [
    ("",                    ""),
    ("Coma  ( , )",         ","),
    ("Punto y coma  ( ; )", ";"),
    ("Tabulador  ( \\t )",  "\t"),
    ("Pipe  ( | )",         "|"),
    ("Espacio",             " "),
]

TIPOS_DATO = ["varchar", "int", "float", "bool", "date", "timestamp"]

_PREVIEW_ROWS = 10

# ── Estilos de tabla ──────────────────────────────────────────────────────────


# ── Modelos ───────────────────────────────────────────────────────────────────

@dataclass
class ColumnaDef:
    titulo: str
    tipo_dato: str = "varchar"
    not_null: bool = False
    rango_inicial: Optional[float] = None
    rango_final: Optional[float] = None


_CANDIDATOS_COLS = [
    "orden_candidato", "numero_sorteo", "codigo_departamento", "nombre_departamento",
    "codigo_municipio", "nombre_municipio", "codigo_corporacion", "nombre_corporacion",
    "codigo_circunscripcion", "nombre_circunscripcion", "opcion_voto", "tipo_aval",
    "codigo_partido", "nombre_partido", "codigo_comuna", "nombre_comuna",
    "numero_candidato", "numero_identificacion", "primer_nombre", "segundo_nombre",
    "primer_apellido", "segundo_apellido", "genero_candidato", "letra_partido",
    "estado_lista", "marca_candidato",
]

ESTRUCTURAS: dict[str, list[ColumnaDef]] = {
    "Candidatos": [ColumnaDef(titulo=col) for col in _CANDIDATOS_COLS],
}

_TABLE_HEADERS = ["Título", "Tipo de dato", "Not Null", "Rango inicial", "Rango final"]
_C_TITULO, _C_TIPO, _C_NOT_NULL, _C_RANGO_INI, _C_RANGO_FIN = range(5)

# ── Demo preview data ─────────────────────────────────────────────────────────

_DEMO_PREVIEW: dict[str, tuple[list[str], list[list[str]]]] = {
    "Candidatos": (
        _CANDIDATOS_COLS,
        [
            ["1","3","05","ANTIOQUIA","05001","MEDELLÍN","02","CONCEJO MUNICIPAL","05","MEDELLÍN","LISTA","PARTIDO","001","PARTIDO A","01","EL CENTRO","001","10234567","CARLOS","ALBERTO","GÓMEZ","RODRÍGUEZ","M","A","ACTIVO","0"],
            ["2","7","05","ANTIOQUIA","05001","MEDELLÍN","02","CONCEJO MUNICIPAL","05","MEDELLÍN","LISTA","PARTIDO","001","PARTIDO A","01","EL CENTRO","002","98765432","MARÍA","ELENA","TORRES","SILVA","F","A","ACTIVO","0"],
            ["3","1","05","ANTIOQUIA","05001","MEDELLÍN","02","CONCEJO MUNICIPAL","05","MEDELLÍN","LISTA","PARTIDO","002","PARTIDO B","02","LA CANDELARIA","001","55512345","ALEX","","RUIZ","MENDEZ","F","B","ACTIVO","0"],
            ["4","5","05","ANTIOQUIA","05001","MEDELLÍN","02","CONCEJO MUNICIPAL","05","MEDELLÍN","LISTA","AVAL","003","PARTIDO C","02","LA CANDELARIA","002","44433322","RICARDO","ANDRÉS","PINTO","CASTRO","M","C","ACTIVO","0"],
            ["5","2","11","BOGOTÁ D.C.","11001","BOGOTÁ","03","CONCEJO DISTRITAL","11","BOGOTÁ","LISTA","PARTIDO","004","PARTIDO D","03","CHAPINERO","001","11100022","ROBERTO","","VARGAS","HERRERA","M","D","ACTIVO","0"],
            ["6","9","11","BOGOTÁ D.C.","11001","BOGOTÁ","03","CONCEJO DISTRITAL","11","BOGOTÁ","LISTA","PARTIDO","004","PARTIDO D","03","CHAPINERO","002","22233344","ANA","LUCÍA","CASTRO","MORENO","F","D","ACTIVO","0"],
            ["7","4","76","VALLE DEL CAUCA","76001","CALI","02","CONCEJO MUNICIPAL","76","CALI","LISTA","COALICIÓN","005","PARTIDO E","04","SAN ANTONIO","001","33344455","LUIS","FERNANDO","PÉREZ","DÍAZ","M","E","ACTIVO","0"],
        ],
    ),
    "Censo electoral": (
        ["numero_identificacion", "tipo_documento", "primer_nombre", "segundo_nombre",
         "primer_apellido", "segundo_apellido", "fecha_nacimiento", "genero",
         "codigo_departamento", "nombre_departamento", "codigo_municipio", "nombre_municipio",
         "codigo_puesto", "nombre_puesto", "numero_mesa"],
        [
            ["10234567","CC","CARLOS","ALBERTO","GÓMEZ","RODRÍGUEZ","1985-03-12","M","05","ANTIOQUIA","05001","MEDELLÍN","0101","I.E. CENTRAL","001"],
            ["98765432","CC","MARÍA","ELENA","TORRES","SILVA","1990-07-25","F","05","ANTIOQUIA","05001","MEDELLÍN","0101","I.E. CENTRAL","001"],
            ["55512345","CC","ALEX","","RUIZ","MENDEZ","1978-11-03","F","05","ANTIOQUIA","05001","MEDELLÍN","0102","I.E. LA PAZ","002"],
            ["44433322","CC","RICARDO","ANDRÉS","PINTO","CASTRO","2000-01-18","M","11","BOGOTÁ D.C.","11001","BOGOTÁ","0201","COL. NACIONAL","001"],
            ["11100022","CC","ROBERTO","","VARGAS","HERRERA","1965-09-30","M","76","VALLE DEL CAUCA","76001","CALI","0301","I.E. SAN PEDRO","003"],
        ],
    ),
    "Divipol": (
        ["codigo_departamento", "nombre_departamento", "codigo_municipio", "nombre_municipio",
         "codigo_zona", "nombre_zona", "codigo_corregimiento", "nombre_corregimiento"],
        [
            ["05","ANTIOQUIA","05001","MEDELLÍN","01","URBANA","",""],
            ["05","ANTIOQUIA","05002","ABEJORRAL","01","URBANA","",""],
            ["05","ANTIOQUIA","05004","ABRIAQUÍ","01","URBANA","01","VEREDA EL ORO"],
            ["11","BOGOTÁ D.C.","11001","BOGOTÁ D.C.","01","URBANA","",""],
            ["76","VALLE DEL CAUCA","76001","CALI","01","URBANA","",""],
            ["76","VALLE DEL CAUCA","76020","ALCALÁ","01","URBANA","01","CORREGIMIENTO NORTE"],
        ],
    ),
    "Curules": (
        ["codigo_corporacion", "nombre_corporacion", "codigo_circunscripcion",
         "nombre_circunscripcion", "total_curules", "umbral_porcentaje"],
        [
            ["01","SENADO","00","NACIONAL","108","3.0"],
            ["02","CÁMARA","05","ANTIOQUIA","17","0.0"],
            ["02","CÁMARA","11","BOGOTÁ D.C.","18","0.0"],
            ["02","CÁMARA","76","VALLE DEL CAUCA","13","0.0"],
        ],
    ),
    "Transportes": (
        ["codigo_municipio", "nombre_municipio", "codigo_puesto", "nombre_puesto",
         "numero_mesa", "tipo_transporte", "capacidad", "origen", "destino"],
        [
            ["05001","MEDELLÍN","0101","I.E. CENTRAL","001","BUS","40","TERMINAL SUR","I.E. CENTRAL"],
            ["05001","MEDELLÍN","0102","I.E. LA PAZ","002","BUSETA","19","PARQUE BERRÍO","I.E. LA PAZ"],
            ["76001","CALI","0301","I.E. SAN PEDRO","003","BUS","40","TERMINAL CALI","I.E. SAN PEDRO"],
        ],
    ),
    "Mesas de votación": (
        ["codigo_departamento", "codigo_municipio", "nombre_municipio", "codigo_puesto",
         "nombre_puesto", "numero_mesa", "total_inscritos", "habilitada"],
        [
            ["05","05001","MEDELLÍN","0101","I.E. CENTRAL","001","320","S"],
            ["05","05001","MEDELLÍN","0101","I.E. CENTRAL","002","315","S"],
            ["05","05001","MEDELLÍN","0102","I.E. LA PAZ","001","298","S"],
            ["11","11001","BOGOTÁ","0201","COL. NACIONAL","001","400","S"],
            ["76","76001","CALI","0301","I.E. SAN PEDRO","001","280","N"],
        ],
    ),
    "Puestos de votación": (
        ["codigo_departamento", "codigo_municipio", "nombre_municipio",
         "codigo_puesto", "nombre_puesto", "direccion", "total_mesas", "total_inscritos"],
        [
            ["05","05001","MEDELLÍN","0101","I.E. CENTRAL","CL 50 # 42-90","12","3840"],
            ["05","05001","MEDELLÍN","0102","I.E. LA PAZ","CR 80 # 11-20","8","2384"],
            ["11","11001","BOGOTÁ","0201","COL. NACIONAL","AV 68 # 57-40","20","8000"],
            ["76","76001","CALI","0301","I.E. SAN PEDRO","CL 5 # 24-10","6","1680"],
        ],
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _label(text: str, bold: bool = False, pt: int = 9) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setPointSize(pt)
    f.setBold(bold)
    lbl.setFont(f)
    return lbl


def _centered_checkbox(checked: bool = False) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    cb = QCheckBox()
    cb.setChecked(checked)
    layout.addWidget(cb)
    return container


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


# ── Vista ─────────────────────────────────────────────────────────────────────

class CargueView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget()
        tabs.addTab(self._build_procesamiento_tab(), "Procesamiento")
        tabs.addTab(self._build_historial_tab(), "Historial")

        root.addWidget(tabs)

    def _build_procesamiento_tab(self) -> QWidget:
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        self._proc_stack = QStackedWidget()
        self._proc_stack.addWidget(self._build_formulario_page())
        self._proc_stack.addWidget(QWidget())

        tab_layout.addWidget(self._proc_stack)
        return tab

    def _build_formulario_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(16, 16, 16, 0)
        outer.setSpacing(0)

        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        panel_layout.addLayout(self._build_form())
        panel_layout.addWidget(_separator())
        panel_layout.addWidget(self._build_archivo_group())

        # ── Estructura del archivo ──────────────────────────────────────────
        self._table_separator = _separator()
        self._table_label = _label("Estructura del archivo", bold=True, pt=10)
        self._table = self._build_structure_table()

        self._table_separator.hide()
        self._table_label.hide()
        self._table.hide()

        panel_layout.addWidget(self._table_separator)
        panel_layout.addWidget(self._table_label)
        panel_layout.addWidget(self._table, stretch=1)

        # ── Vista previa ────────────────────────────────────────────────────
        self._preview_separator = _separator()
        self._preview_label = _label("Vista previa del archivo", bold=True, pt=10)
        self._preview_info_lbl = _label("", pt=9)
        self._preview_info_lbl.setStyleSheet("color: #888;")
        self._preview_table = self._build_preview_table()

        self._preview_separator.hide()
        self._preview_label.hide()
        self._preview_info_lbl.hide()
        self._preview_table.hide()

        panel_layout.addWidget(self._preview_separator)
        panel_layout.addWidget(self._preview_label)
        panel_layout.addWidget(self._preview_info_lbl)
        panel_layout.addWidget(self._preview_table)

        self._spacer = QWidget()
        self._spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        outer.addWidget(panel)
        outer.addWidget(self._spacer, stretch=1)

        self._btn_container = self._build_action_buttons()
        self._btn_container.hide()
        outer.addWidget(self._btn_container)

        self._outer = outer
        self._panel = panel

        return page

    def _build_historial_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._detail_panel = HistorialDetailPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._build_historial_list())
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)
        return tab

    def _build_historial_list(self) -> QWidget:
        container = QWidget()
        container.setMinimumWidth(180)

        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._history_inner = QWidget()
        self._history_layout = QVBoxLayout(self._history_inner)
        self._history_layout.setContentsMargins(8, 8, 8, 8)
        self._history_layout.setSpacing(6)

        self._selected_item: HistorialItemWidget | None = None

        self.refresh_history()

        scroll.setWidget(self._history_inner)
        vbox.addWidget(scroll)

        return container

    def refresh_history(self):
        """Limpia y vuelve a cargar el historial desde la base de datos."""
        # Limpiar layout
        while self._history_layout.count():
            child = self._history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                pass # El stretch se quita al final al reconstruir
        
        self._selected_item = None
        if hasattr(self, "_detail_panel"):
            self._detail_panel._show_empty()

        # Cargar datos
        try:
            history = fetch_history()
            if not history:
                lbl = QLabel("No hay registros en el historial.")
                lbl.setStyleSheet("color: #888; margin-top: 20px;")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._history_layout.addWidget(lbl)
            else:
                for entry in history:
                    item = HistorialItemWidget(entry, self._on_historial_item_click)
                    self._history_layout.addWidget(item)
            
            self._history_layout.addStretch()
        except Exception as e:
            lbl = QLabel(f"Error al conectar con la base de datos.")
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self._history_layout.addWidget(lbl)
            print(f"Error en refresh_history: {e}")

    def _on_historial_item_click(self, entry: HistorialEntry, widget: HistorialItemWidget):
        if self._selected_item:
            self._selected_item.set_selected(False)
        widget.set_selected(True)
        self._selected_item = widget
        self._detail_panel.show_entry(entry)

    def _build_form(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        grid.addWidget(_label("Tipo de cargue"),    0, 0)
        grid.addWidget(_label("Tipo de separador"), 0, 1)

        self._tipo_combo = QComboBox()
        self._tipo_combo.setEditable(True)
        self._tipo_combo.lineEdit().setPlaceholderText("Seleccione o filtre...")
        self._tipo_combo.addItems(TIPOS_CARGUE)
        self._tipo_combo.lineEdit().textEdited.connect(self._filter_tipo_combo)
        self._tipo_combo.currentTextChanged.connect(self._on_tipo_changed)
        grid.addWidget(self._tipo_combo, 1, 0)

        self._separador_combo = QComboBox()
        for label, _ in SEPARADORES:
            self._separador_combo.addItem(label)
        self._separador_combo.currentIndexChanged.connect(self._refresh_preview)
        grid.addWidget(self._separador_combo, 1, 1)

        return grid

    def _build_archivo_group(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)
        vbox.addWidget(_label("Archivo"))

        hbox = QHBoxLayout()
        self._archivo_input = QLineEdit()
        self._archivo_input.setPlaceholderText("Seleccione un archivo...")
        self._archivo_input.setReadOnly(True)
        hbox.addWidget(self._archivo_input)

        browse_btn = QPushButton("Examinar...")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_file)
        hbox.addWidget(browse_btn)

        vbox.addLayout(hbox)

        self._chk_cabecera = QCheckBox("El archivo tiene cabecera")
        self._chk_cabecera.setChecked(True)
        self._chk_cabecera.toggled.connect(self._refresh_preview)
        vbox.addWidget(self._chk_cabecera)

        return container

    def _build_action_buttons(self) -> QWidget:
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(16, 8, 16, 16)
        hbox.setSpacing(8)

        self._btn_cargar = QPushButton("Cargar archivo")
        self._btn_cargar.setFixedWidth(130)
        self._btn_cargar.clicked.connect(self._on_cargar)
        hbox.addWidget(self._btn_cargar)

        self._btn_cancelar = QPushButton("Cancelar")
        self._btn_cancelar.setFixedWidth(100)
        self._btn_cancelar.clicked.connect(self._on_cancelar)
        hbox.addWidget(self._btn_cancelar)

        hbox.addStretch()
        return container

    def _build_structure_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(_TABLE_HEADERS))
        table.setHorizontalHeaderLabels(_TABLE_HEADERS)
        table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(_TABLE_STYLE)

        header = table.horizontalHeader()
        header.setSectionResizeMode(_C_TITULO,     QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(_C_TIPO,       QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(_C_NOT_NULL,   QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(_C_RANGO_INI,  QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(_C_RANGO_FIN,  QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(_C_TIPO,      140)
        table.setColumnWidth(_C_NOT_NULL,   80)
        table.setColumnWidth(_C_RANGO_INI, 110)
        table.setColumnWidth(_C_RANGO_FIN, 110)

        return table

    def _build_preview_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.verticalHeader().setVisible(False)
        table.setMaximumHeight(220)
        table.setStyleSheet(_TABLE_STYLE)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return table

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _filter_tipo_combo(self, text: str):
        self._tipo_combo.blockSignals(True)
        self._tipo_combo.clear()
        filtered = [t for t in TIPOS_CARGUE if text.lower() in t.lower()]
        self._tipo_combo.addItems(filtered)
        self._tipo_combo.lineEdit().setText(text)
        self._tipo_combo.lineEdit().setCursorPosition(len(text))
        self._tipo_combo.blockSignals(False)
        self._tipo_combo.showPopup()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo",
            "",
            "Archivos de datos (*.csv *.txt *.xlsx *.xls);;Todos los archivos (*)",
        )
        if path:
            self._archivo_input.setText(path)
            self._refresh_table()
            self._refresh_preview()

    def _on_tipo_changed(self):
        self._refresh_table()
        self._refresh_preview()

    def _refresh_table(self):
        tipo = self._tipo_combo.currentText()
        archivo = self._archivo_input.text()
        columnas = ESTRUCTURAS.get(tipo)

        table_visible = bool(archivo and columnas)
        self._table_separator.setVisible(table_visible)
        self._table_label.setVisible(table_visible)
        self._table.setVisible(table_visible)

        any_visible = table_visible or bool(archivo)
        self._spacer.setVisible(not any_visible)
        self._outer.setStretch(self._outer.indexOf(self._panel), 1 if any_visible else 0)

        if not table_visible:
            self._btn_container.hide()
            return

        self._table.setRowCount(len(columnas))
        for row, col in enumerate(columnas):
            item = QTableWidgetItem(col.titulo)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, _C_TITULO, item)

            combo = _NoScrollComboBox()
            combo.addItems(TIPOS_DATO)
            idx = TIPOS_DATO.index(col.tipo_dato) if col.tipo_dato in TIPOS_DATO else 0
            combo.setCurrentIndex(idx)
            self._table.setCellWidget(row, _C_TIPO, combo)

            self._table.setCellWidget(row, _C_NOT_NULL, _centered_checkbox(col.not_null))

            self._table.setItem(row, _C_RANGO_INI,
                QTableWidgetItem("" if col.rango_inicial is None else str(col.rango_inicial)))
            self._table.setItem(row, _C_RANGO_FIN,
                QTableWidgetItem("" if col.rango_final is None else str(col.rango_final)))

        self._btn_container.show()

    def _refresh_preview(self):
        archivo = self._archivo_input.text()

        if not archivo:
            self._preview_separator.hide()
            self._preview_label.hide()
            self._preview_info_lbl.hide()
            self._preview_table.hide()
            return

        tipo = self._tipo_combo.currentText()
        preview_data = _DEMO_PREVIEW.get(tipo)

        self._preview_separator.show()
        self._preview_label.show()

        if not preview_data:
            self._preview_table.hide()
            self._preview_info_lbl.setText(
                "Seleccione el tipo de cargue para ver la vista previa."
                if not tipo else
                f"No hay vista previa disponible para «{tipo}»."
            )
            self._preview_info_lbl.show()
            self._spacer.hide()
            self._outer.setStretch(self._outer.indexOf(self._panel), 1)
            return

        self._preview_info_lbl.hide()

        headers, rows = preview_data
        tiene_cabecera = self._chk_cabecera.isChecked()

        if tiene_cabecera:
            display_headers = headers
            display_rows = rows
        else:
            # Sin cabecera: encabezados genéricos, la primera fila es dato
            n_cols = len(headers)
            display_headers = [f"col_{i + 1}" for i in range(n_cols)]
            display_rows = [headers] + list(rows)   # la cabecera original pasa a ser fila 1

        self._preview_table.setColumnCount(len(display_headers))
        self._preview_table.setHorizontalHeaderLabels(display_headers)
        self._preview_table.setRowCount(len(display_rows))

        # Resaltar encabezados que no coincidan con la estructura esperada
        columnas = ESTRUCTURAS.get(tipo)
        expected = {col.titulo for col in columnas} if columnas else set()

        if tiene_cabecera and expected:
            for c, h in enumerate(display_headers):
                item = self._preview_table.horizontalHeaderItem(c)
                if item and h not in expected:
                    item.setForeground(QBrush(QColor("#e74c3c")))

        for r, row in enumerate(display_rows):
            for c, val in enumerate(row):
                self._preview_table.setItem(r, c, QTableWidgetItem(val))

        self._preview_table.show()
        self._spacer.hide()
        self._outer.setStretch(self._outer.indexOf(self._panel), 1)

    def _on_cargar(self):
        novedades_view = NovedadesView(
            novedades=DEMO_NOVEDADES,
            on_continuar=self._on_novedades_continuar,
            on_cancelar=self._on_novedades_cancelar,
        )
        self._proc_stack.removeWidget(self._proc_stack.widget(1))
        self._proc_stack.addWidget(novedades_view)
        self._proc_stack.setCurrentIndex(1)

    def _on_novedades_continuar(self):
        self._volver_formulario()

    def _on_novedades_cancelar(self):
        self._volver_formulario()

    def _volver_formulario(self):
        self._proc_stack.setCurrentIndex(0)

    def _on_cancelar(self):
        self._tipo_combo.setCurrentIndex(0)
        self._separador_combo.setCurrentIndex(0)
        self._archivo_input.clear()
        self._chk_cabecera.setChecked(True)
        self._refresh_table()
        self._refresh_preview()

    # ── Propiedades públicas ──────────────────────────────────────────────────

    @property
    def tipo_cargue(self) -> Optional[str]:
        return self._tipo_combo.currentText() or None

    @property
    def separador(self) -> str:
        idx = self._separador_combo.currentIndex()
        return SEPARADORES[idx][1]

    @property
    def archivo_path(self) -> Optional[str]:
        return self._archivo_input.text() or None
