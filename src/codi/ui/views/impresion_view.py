"""Vista Tablero de Producción de Impresión."""
from __future__ import annotations

import bisect

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QPainter
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from codi.core.impresion_service import (
    DetalleElemento,
    DatosTablero,
    GrupoTarjeta,
    cargar_datos,
    cargar_detalle,
)

TOTAL_KITS = 125_260

COLOR_IMPRESO   = QColor("#4CAF50")
COLOR_PENDIENTE = QColor("#E0E0E0")
COLOR_RFID      = QColor("#2196F3")
COLOR_ESTANDAR  = QColor("#FF9800")
BAR_H      = 14   # RFID / Estándar
BAR_H_CARD =  8   # barra resumen del card
BAR_H_FILA =  9   # barra por planta dentro del card
REFRESH_MS = 30 * 60 * 1_000   # 30 min
CARDS_POR_FILA = 3


# ── Worker ─────────────────────────────────────────────────────────────────────

class _DataWorker(QThread):
    data_ready = Signal(object)   # DatosTablero
    error      = Signal(str)

    def run(self):
        try:
            datos = cargar_datos()
            self.data_ready.emit(datos)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


# ── Barras ─────────────────────────────────────────────────────────────────────

class _BarraSimple(QWidget):
    """Barra de progreso simple (0–total) para el resumen del card."""
    def __init__(self, valor: int, total: int, color: QColor, parent=None):
        super().__init__(parent)
        self._ratio = valor / total if total else 0.0
        self._color = color
        self.setFixedHeight(BAR_H_CARD)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _):
        p = QPainter(self)
        W = self.width()
        p.fillRect(0, 0, W, BAR_H_CARD, COLOR_PENDIENTE)
        p.fillRect(0, 0, max(int(self._ratio * W), 0), BAR_H_CARD, self._color)


class _BarraSegmentada(QWidget):
    """Barra segmentada con eje global 1–125 260 y tooltip por intervalo."""
    def __init__(self, segmentos: list, color: QColor, bar_h: int = BAR_H, parent=None):
        super().__init__(parent)
        self._segs      = segmentos
        self._color     = color
        self._bar_h     = bar_h
        self._intervals = self._build_intervals(segmentos)
        self._ini_vals  = [iv[0] for iv in self._intervals]
        self._last_idx  = -2
        self.setFixedHeight(bar_h + 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    @staticmethod
    def _build_intervals(segs: list) -> list[tuple[int, int, bool]]:
        intervals: list[tuple[int, int, bool]] = []
        cursor = 0
        for ini, fin in sorted(segs):
            if cursor < ini:
                intervals.append((cursor, ini - 1, False))
            intervals.append((ini, fin, True))
            cursor = fin + 1
        if cursor <= TOTAL_KITS:
            intervals.append((cursor, TOTAL_KITS, False))
        return intervals

    def _interval_at(self, kit: int) -> int:
        idx = bisect.bisect_right(self._ini_vals, kit) - 1
        if 0 <= idx < len(self._intervals) and self._intervals[idx][1] >= kit:
            return idx
        return -1

    def paintEvent(self, _):
        p = QPainter(self)
        W = self.width()
        p.fillRect(0, 1, W, self._bar_h, COLOR_PENDIENTE)
        for ini, fin in self._segs:
            x  = int(ini / TOTAL_KITS * W)
            x2 = int(fin / TOTAL_KITS * W)
            p.fillRect(x, 1, max(x2 - x, 1), self._bar_h, self._color)

    def mouseMoveEvent(self, e):
        kit = max(0, min(int(e.position().x() / self.width() * TOTAL_KITS), TOTAL_KITS))
        idx = self._interval_at(kit)
        if idx == self._last_idx:
            return
        self._last_idx = idx
        if idx < 0:
            QToolTip.hideText()
            return
        ini, fin, impreso = self._intervals[idx]
        cantidad = fin - ini + 1
        estado = "Impreso" if impreso else "Pendiente"
        QToolTip.showText(
            QCursor.pos(),
            f"{estado}: Kit {ini:,} → {fin:,}   ({cantidad:,} kits)",
            self,
        )

    def leaveEvent(self, _):
        self._last_idx = -2
        QToolTip.hideText()


# ── Helpers UI ─────────────────────────────────────────────────────────────────

def _lbl(text: str, pt: int = 9, bold: bool = False, color: str = "#222") -> QLabel:
    l = QLabel(text)
    f = QFont()
    f.setPointSize(pt)
    f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color: {color};")
    return l


def _sep() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("color: #e0e0e0;")
    return line


def _fila_barra(
    nombre: str,
    segmentos: list,
    kits_impresos: int,
    total_asignado: int,
    color: QColor,
    nombre_width: int = 120,
) -> QWidget:
    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 1, 0, 1)
    h.setSpacing(6)

    nombre_lbl = _lbl(nombre, pt=8, color="#555")
    nombre_lbl.setFixedWidth(nombre_width)
    nombre_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    h.addWidget(nombre_lbl)

    barra = _BarraSegmentada(segmentos, color)
    h.addWidget(barra, stretch=1)

    tick = " ✓" if total_asignado and kits_impresos >= total_asignado else ""
    cnt_txt = f"{kits_impresos:,} / {total_asignado:,}{tick}" if total_asignado else f"{kits_impresos:,}"
    cnt_lbl = _lbl(cnt_txt, pt=8, color="#333")
    cnt_lbl.setFixedWidth(160)
    h.addWidget(cnt_lbl)
    return row


# ── Worker de detalle ──────────────────────────────────────────────────────────

class _DetalleWorker(QThread):
    data_ready = Signal(object)   # DetalleElemento
    error      = Signal(str)

    def __init__(self, prefijo: str, titulo: str, tabla: str, parent=None):
        super().__init__(parent)
        self._prefijo = prefijo
        self._titulo  = titulo
        self._tabla   = tabla

    def run(self):
        try:
            det = cargar_detalle(self._prefijo, self._titulo, self._tabla)
            self.data_ready.emit(det)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


# ── Diálogo de detalle ─────────────────────────────────────────────────────────

class _DetalleDialog(QDialog):
    def __init__(self, grupo: GrupoTarjeta, tabla: str, parent=None):
        super().__init__(parent)
        self._grupo = grupo
        self._tabla = tabla
        self.setWindowTitle(grupo.titulo)
        self.setMinimumWidth(580)
        self.setModal(False)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # Título
        root.addWidget(_lbl(self._grupo.titulo, pt=12, bold=True, color="#1a1a2e"))

        # Barra resumen grande
        total_imp  = sum(f.kits_impresos for f in self._grupo.plantas)
        total_asig = sum(f.total_asignado for f in self._grupo.plantas)
        pct        = round(total_imp / total_asig * 100, 1) if total_asig else 0.0
        completo   = total_asig > 0 and total_imp >= total_asig
        tick       = " ✓" if completo else ""
        pct_color  = "#2c6e2c" if completo else "#555"

        barra = _BarraSimple(total_imp, total_asig, COLOR_IMPRESO)
        barra.setFixedHeight(12)
        root.addWidget(barra)

        sub = QHBoxLayout()
        sub.addWidget(_lbl(f"{total_imp:,} / {total_asig:,} kits", pt=8, color="#555"))
        sub.addStretch()
        sub.addWidget(_lbl(f"{pct}%{tick}", pt=9, bold=True, color=pct_color))
        root.addLayout(sub)

        root.addWidget(_sep())

        # Stats — se llenará al cargar
        self._stats_grid = QGridLayout()
        self._stats_grid.setHorizontalSpacing(16)
        self._stats_grid.setVerticalSpacing(5)
        root.addLayout(self._stats_grid)

        self._status_lbl = _lbl("Cargando estadísticas…", pt=8, color="#888")
        root.addWidget(self._status_lbl)

        root.addWidget(_sep())

        # Plantas
        root.addWidget(_lbl("PLANTAS", pt=8, bold=True, color="#1a1a2e"))
        for fila in self._grupo.plantas:
            segs   = [(b.ini, b.fin) for b in fila.bloques]
            pct_p  = round(fila.kits_impresos / fila.total_asignado * 100, 1) if fila.total_asignado else 0.0
            tick_p = " ✓" if fila.total_asignado and fila.kits_impresos >= fila.total_asignado else ""

            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 1, 0, 1)
            h.setSpacing(6)

            pl = _lbl(fila.planta, pt=8, color="#555")
            pl.setFixedWidth(40)
            pl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            h.addWidget(pl)

            h.addWidget(_BarraSegmentada(segs, COLOR_IMPRESO, bar_h=10), stretch=1)

            cnt_color = "#2c6e2c" if tick_p else "#333"
            cnt = _lbl(
                f"{fila.kits_impresos:,} / {fila.total_asignado:,}  {pct_p}%{tick_p}",
                pt=8, color=cnt_color,
            )
            cnt.setFixedWidth(172)
            h.addWidget(cnt)
            root.addWidget(row)

    def _load(self):
        self._worker = _DetalleWorker(
            self._grupo.prefijo, self._grupo.titulo, self._tabla, self
        )
        self._worker.data_ready.connect(self._on_data)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_data(self, det: DetalleElemento):
        self._status_lbl.setVisible(False)
        g = self._stats_grid

        def _stat(row, label, value, value_color="#222"):
            g.addWidget(_lbl(label, pt=8, color="#888"), row, 0)
            g.addWidget(_lbl(value, pt=8, bold=True, color=value_color), row, 1)

        fmt_dt = lambda dt: dt.strftime("%d %b %Y  %H:%M") if dt else "—"

        _stat(0, "Primera impresión",  fmt_dt(det.fecha_inicio))
        _stat(1, "Última impresión",   fmt_dt(det.fecha_ultimo))
        _stat(2, "Kits reimpresos",
              f"{det.reimpresos:,}",
              "#c0392b" if det.reimpresos else "#2c6e2c")
        _stat(3, "Errores",
              f"{det.errores:,}" if det.errores else "Ninguno",
              "#c0392b" if det.errores else "#2c6e2c")
        _stat(4, "Impresoras",
              ", ".join(det.impresoras) if det.impresoras else "—")
        _stat(5, "Usuarios",           f"{det.n_usuarios:,}")

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"Error: {msg}")
        self._status_lbl.setStyleSheet("color: #c0392b;")


# ── Card de tarjeta (clickable) ────────────────────────────────────────────────

class _CardTarjeta(QFrame):
    clicked = Signal(object)   # GrupoTarjeta

    def __init__(self, grupo: GrupoTarjeta, parent=None):
        super().__init__(parent)
        self._grupo = grupo
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #d4d4d4; border-radius: 6px; }"
            "QFrame:hover { border: 1px solid #999; background: #f7f7f7; }"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(grupo)

    def _build(self, grupo: GrupoTarjeta):
        total_imp  = sum(f.kits_impresos for f in grupo.plantas)
        total_asig = sum(f.total_asignado for f in grupo.plantas)
        pct        = round(total_imp / total_asig * 100, 1) if total_asig else 0.0
        completo   = total_asig > 0 and total_imp >= total_asig

        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.setSpacing(4)
        hdr.addWidget(_lbl(grupo.titulo, pt=9, bold=True, color="#1a1a2e"), stretch=1)
        tick = " ✓" if completo else ""
        hdr.addWidget(_lbl(f"{pct}%{tick}", pt=9, bold=True,
                           color="#2c6e2c" if completo else "#555"))
        v.addLayout(hdr)

        v.addWidget(_BarraSimple(total_imp, total_asig, COLOR_IMPRESO))
        v.addWidget(_lbl(f"{total_imp:,} / {total_asig:,} kits", pt=7, color="#888"))
        v.addWidget(_sep())

        for fila in grupo.plantas:
            segs   = [(b.ini, b.fin) for b in fila.bloques]
            pct_p  = round(fila.kits_impresos / fila.total_asignado * 100, 1) if fila.total_asignado else 0.0
            tick_p = " ✓" if fila.total_asignado and fila.kits_impresos >= fila.total_asignado else ""

            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 1, 0, 1)
            h.setSpacing(5)

            pl = _lbl(fila.planta, pt=8, color="#555")
            pl.setFixedWidth(40)
            pl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            h.addWidget(pl)
            h.addWidget(_BarraSegmentada(segs, COLOR_IMPRESO, bar_h=BAR_H_FILA), stretch=1)
            cnt = _lbl(
                f"{fila.kits_impresos:,} / {fila.total_asignado:,}  {pct_p}%{tick_p}",
                pt=7, color="#2c6e2c" if tick_p else "#333",
            )
            cnt.setFixedWidth(148)
            h.addWidget(cnt)
            v.addWidget(row)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._grupo)
        super().mousePressEvent(e)


# ── Vista principal ────────────────────────────────────────────────────────────

class ImpresionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: _DataWorker | None = None
        self._build_skeleton()

        self._timer = QTimer(self)
        self._timer.setInterval(REFRESH_MS)
        self._timer.timeout.connect(self._refresh)

    # ── Esqueleto ─────────────────────────────────────────────────────────────

    def _build_skeleton(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # Cabecera
        hdr = QHBoxLayout()
        hdr.setSpacing(12)
        self._title_lbl = _lbl("Tablero de Producción", pt=13, bold=True, color="#1a1a2e")
        hdr.addWidget(self._title_lbl)
        hdr.addStretch()
        self._ts_lbl = _lbl("", pt=8, color="#888")
        hdr.addWidget(self._ts_lbl)
        self._refresh_btn = QPushButton("↻ Actualizar")
        self._refresh_btn.setFixedWidth(110)
        self._refresh_btn.clicked.connect(self._refresh)
        hdr.addWidget(self._refresh_btn)
        root.addLayout(hdr)

        # Estado
        self._status_lbl = _lbl("Cargando datos…", pt=9, color="#888")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._status_lbl)

        # Contenido
        self._content = QWidget()
        self._content.setVisible(False)
        cl = QVBoxLayout(self._content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        # Sección cards de tarjetas
        cl.addWidget(_lbl("TARJETAS POR PLANTA", pt=10, bold=True, color="#1a1a2e"))
        cl.addWidget(_sep())

        self._scroll_tarjetas = QScrollArea()
        self._scroll_tarjetas.setWidgetResizable(True)
        self._scroll_tarjetas.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_tarjetas.setMinimumHeight(280)

        self._cards_container = QWidget()
        self._cards_grid = QGridLayout(self._cards_container)
        self._cards_grid.setSpacing(10)
        self._cards_grid.setContentsMargins(0, 4, 0, 4)
        self._scroll_tarjetas.setWidget(self._cards_container)
        cl.addWidget(self._scroll_tarjetas, stretch=1)

        cl.addSpacing(8)

        # Sección RFID + Estándar
        cols = QHBoxLayout()
        cols.setSpacing(20)

        self._rfid_w = QWidget()
        self._rfid_v = QVBoxLayout(self._rfid_w)
        self._rfid_v.setContentsMargins(0, 0, 0, 0)
        self._rfid_v.setSpacing(2)
        self._rfid_v.addWidget(_lbl("IMPRESIÓN RFID", pt=10, bold=True, color="#1a1a2e"))
        self._rfid_v.addWidget(_sep())
        self._rfid_v.addStretch()
        cols.addWidget(self._rfid_w)

        self._est_w = QWidget()
        self._est_v = QVBoxLayout(self._est_w)
        self._est_v.setContentsMargins(0, 0, 0, 0)
        self._est_v.setSpacing(2)
        self._est_v.addWidget(_lbl("IMPRESIÓN ESTÁNDAR", pt=10, bold=True, color="#1a1a2e"))
        self._est_v.addWidget(_sep())
        self._est_v.addStretch()
        cols.addWidget(self._est_w)

        cl.addLayout(cols)
        root.addWidget(self._content, stretch=1)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if self._worker is None or not self._worker.isRunning():
            self._refresh()
        if not self._timer.isActive():
            self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _refresh(self):
        if self._worker and self._worker.isRunning():
            return
        self._refresh_btn.setEnabled(False)
        self._status_lbl.setText("Cargando datos…")
        self._status_lbl.setStyleSheet("color: #888;")
        self._status_lbl.setVisible(True)
        self._content.setVisible(False)

        self._worker = _DataWorker(self)
        self._worker.data_ready.connect(self._on_data)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_data(self, datos: DatosTablero):
        self._poblar(datos)
        self._ts_lbl.setText(f"Actualizado: {datos.timestamp.strftime('%d/%m/%Y %H:%M')}")
        self._status_lbl.setVisible(False)
        self._content.setVisible(True)
        self._refresh_btn.setEnabled(True)

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"Error al cargar datos: {msg}")
        self._status_lbl.setStyleSheet("color: #c0392b;")
        self._refresh_btn.setEnabled(True)

    # ── Poblar ────────────────────────────────────────────────────────────────

    def _poblar(self, datos: DatosTablero):
        # Limpiar grid de cards
        while self._cards_grid.count():
            item = self._cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._limpiar_layout(self._rfid_v, keep_first=2)
        self._limpiar_layout(self._est_v, keep_first=2)

        # Cards de tarjetas en grid
        for i, grupo in enumerate(datos.tarjetas):
            card = _CardTarjeta(grupo)
            card.clicked.connect(self._abrir_detalle)
            self._cards_grid.addWidget(card, i // CARDS_POR_FILA, i % CARDS_POR_FILA)

        # Empujar cards hacia arriba si hay filas incompletas
        total_rows = (len(datos.tarjetas) + CARDS_POR_FILA - 1) // CARDS_POR_FILA
        self._cards_grid.setRowStretch(total_rows, 1)

        # RFID
        for elem in datos.rfid:
            segs = [(b.ini, b.fin) for b in elem.bloques]
            self._rfid_v.insertWidget(
                self._rfid_v.count() - 1,
                _fila_barra(elem.titulo, segs, elem.kits_impresos, 0, COLOR_RFID),
            )

        # Estándar
        for elem in datos.estandar:
            segs = [(b.ini, b.fin) for b in elem.bloques]
            self._est_v.insertWidget(
                self._est_v.count() - 1,
                _fila_barra(elem.titulo, segs, elem.kits_impresos, 0, COLOR_ESTANDAR),
            )

    def _abrir_detalle(self, grupo: GrupoTarjeta):
        dlg = _DetalleDialog(grupo, tabla="impresion.imp_trfid", parent=self)
        dlg.show()

    @staticmethod
    def _limpiar_layout(layout: QVBoxLayout, keep_first: int = 0):
        while layout.count() > keep_first:
            item = layout.takeAt(keep_first)
            if item.widget():
                item.widget().deleteLater()
