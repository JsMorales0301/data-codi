"""
Demo Opción 1 — QPainter nativo (PySide6 puro)
Ejecutar: uv run python demos/demo_qpainter.py
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QCursor

TOTAL_KITS = 125_260

# Datos simulados: lista de (inicio, fin) bloques impresos
MOCK_DATA = {
    "SENADO": [
        ("PLN01", [(1, 18_000), (22_000, 41_000), (45_000, 52_772)], 68_975),
        ("PLN08", [(70_000, 95_000), (100_000, 115_000), (118_000, 124_529)], 59_602),
    ],
    "SENADO IND": [
        ("PLN01", [(1, 35_000), (38_000, 66_734)], 91_178),
        ("PLN05", [(88_000, 105_000), (108_000, 121_331)], 36_659),
    ],
    "CAMARA": [
        ("PLN01", [], 80_000),
    ],
    "CAMARA IND": [
        ("PLN04", [(50_000, 80_000), (85_000, 108_346)], 111_166),
    ],
    "CAMARA AFR": [
        ("PLN01", [(1, 25_000), (28_000, 57_230)], 59_211),
        ("PLN05", [(60_000, 75_000), (78_000, 92_837)], 54_305),
        ("PLN06", [(95_000, 99_507)], 103_445),
    ],
    "CONSULTAS": [
        ("PLN03", [], 45_000),
    ],
}

RFID_DATA = [
    ("Lista chequeo",      [(1, 18_000), (20_000, 47_000), (50_000, 65_000)],   65_000),
    ("Lateral Izq.",       [(1, 15_000), (18_000, 44_000), (47_000, 64_800)],   64_800),
    ("Lateral Posterior",  [(1, 15_000), (18_000, 44_000), (47_000, 64_800)],   64_800),
    ("Caja Interna",       [(1, 20_000), (23_000, 50_000), (53_000, 69_145)],   69_145),
    ("S. Material NO útil",[(1, 12_000), (16_000, 38_000), (41_000, 53_145)],   53_145),
    ("S. Claveros",        [(1, 18_000), (22_000, 45_000), (48_000, 65_995)],   65_995),
    ("S. Delegados",       [(1, 30_000), (35_000, 70_000), (75_000, 103_015)], 103_015),
    ("Trans. Disc.",       [(1, 1_268)],                                          1_268),
]

ESTANDAR_DATA = [
    ("Certificados Elec.", [(1, 8_000), (10_000, 20_000)],                       20_000),
    ("Caja Kit",           [(1, 12_000), (15_000, 32_500)],                      32_500),
    ("Sobre A",            [(1, 1_945)],                                          1_945),
    ("Sobre C",            [(1, 1_945)],                                          1_945),
    ("Sobre D",            [(1, 10_000), (12_000, 27_545)],                      27_545),
    ("Sobre G",            [(1, 1_945)],                                          1_945),
    ("Cartuchera",         [(1, 1_945)],                                          1_945),
    ("Caja Kit Municipal", [],                                                      114),
    ("Señalización",       [],                                                      114),
]

COLOR_IMPRESO  = QColor("#4CAF50")
COLOR_PENDIENTE= QColor("#D9D9D9")
COLOR_HEADER   = QColor("#1a1a2e")
COLOR_SUBHEAD  = QColor("#2c3e6b")
BAR_H = 14


class BarraSegmentada(QWidget):
    def __init__(self, segmentos, total_asignado, parent=None):
        super().__init__(parent)
        self.segmentos = segmentos
        self.total_asignado = total_asignado
        self.setFixedHeight(BAR_H + 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), BAR_H
        p.fillRect(0, 1, W, H, COLOR_PENDIENTE)
        for ini, fin in self.segmentos:
            x  = int((ini  / TOTAL_KITS) * W)
            x2 = int((fin  / TOTAL_KITS) * W)
            p.fillRect(x, 1, max(x2 - x, 1), H, COLOR_IMPRESO)

    def mouseMoveEvent(self, e):
        kit = int((e.position().x() / self.width()) * TOTAL_KITS)
        estado = "impreso" if any(i <= kit <= f for i, f in self.segmentos) else "pendiente"
        from PySide6.QtWidgets import QToolTip
        QToolTip.showText(QCursor.pos(), f"Kit ~{kit:,} — {estado}")


def _lbl(text, pt=9, bold=False, color="#222"):
    l = QLabel(text)
    f = QFont(); f.setPointSize(pt); f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color: {color};")
    return l


def _fila_barra(nombre, segmentos, total_asig, total_global=TOTAL_KITS):
    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 1, 0, 1)
    h.setSpacing(6)

    lbl_nombre = _lbl(nombre, pt=8, color="#555")
    lbl_nombre.setFixedWidth(72)
    lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    h.addWidget(lbl_nombre)

    barra = BarraSegmentada(segmentos, total_asig)
    h.addWidget(barra, stretch=1)

    impresos = sum(f - i for i, f in segmentos)
    tick = "✓" if impresos >= total_asig else ""
    lbl_cnt = _lbl(f"{impresos:,} / {total_asig:,} {tick}", pt=8, color="#333")
    lbl_cnt.setFixedWidth(150)
    h.addWidget(lbl_cnt)
    return row


def _separador():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("color: #e0e0e0;")
    return line


class TableroView(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(0)

        # Título
        root.addWidget(_lbl("Tablero de Producción  —  QPainter nativo", pt=13, bold=True, color="#1a1a2e"))
        root.addWidget(_lbl(f"Eje compartido: Kit 1 → Kit {TOTAL_KITS:,}", pt=8, color="#888"))
        root.addSpacing(10)

        # ── SECCIÓN PLANTAS (scroll) ──────────────────────────────────
        root.addWidget(_lbl("TARJETAS POR PLANTA", pt=10, bold=True, color="#1a1a2e"))
        root.addWidget(_separador())
        root.addSpacing(4)

        scroll_plantas = QScrollArea()
        scroll_plantas.setWidgetResizable(True)
        scroll_plantas.setFrameShape(QFrame.Shape.NoFrame)
        scroll_plantas.setFixedHeight(300)

        contenedor = QWidget()
        vbox = QVBoxLayout(contenedor)
        vbox.setSpacing(2)
        vbox.setContentsMargins(0, 0, 0, 0)

        for tarjeta, plantas in MOCK_DATA.items():
            vbox.addWidget(_lbl(tarjeta, pt=9, bold=True, color="#2c3e6b"))
            for planta, segs, total_asig in plantas:
                vbox.addWidget(_fila_barra(planta, segs, total_asig))
            vbox.addSpacing(4)

        vbox.addStretch()
        scroll_plantas.setWidget(contenedor)
        root.addWidget(scroll_plantas)

        root.addSpacing(12)

        # ── SECCIÓN RFID + ESTÁNDAR ───────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(20)

        # RFID
        rfid_w = QWidget()
        rfid_v = QVBoxLayout(rfid_w)
        rfid_v.setContentsMargins(0, 0, 0, 0)
        rfid_v.setSpacing(2)
        rfid_v.addWidget(_lbl("IMPRESIÓN RFID", pt=10, bold=True, color="#1a1a2e"))
        rfid_v.addWidget(_separador())
        rfid_v.addSpacing(4)
        for nombre, segs, meta in RFID_DATA:
            rfid_v.addWidget(_fila_barra(nombre, segs, meta))
        rfid_v.addStretch()
        cols.addWidget(rfid_w)

        # Estándar
        est_w = QWidget()
        est_v = QVBoxLayout(est_w)
        est_v.setContentsMargins(0, 0, 0, 0)
        est_v.setSpacing(2)
        est_v.addWidget(_lbl("IMPRESIÓN ESTÁNDAR (Actas / Kits)", pt=10, bold=True, color="#1a1a2e"))
        est_v.addWidget(_separador())
        est_v.addSpacing(4)
        for nombre, segs, meta in ESTANDAR_DATA:
            est_v.addWidget(_fila_barra(nombre, segs, meta))
        est_v.addStretch()
        cols.addWidget(est_w)

        root.addLayout(cols)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo — Opción 1: QPainter nativo")
        self.setMinimumSize(1000, 700)
        self.setCentralWidget(TableroView())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
