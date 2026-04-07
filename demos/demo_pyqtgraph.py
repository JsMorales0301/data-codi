"""
Demo Opción 3 — PyQtGraph
Ejecutar: uv run python demos/demo_pyqtgraph.py
"""
import sys
import numpy as np
import pyqtgraph as pg
from pyqtgraph import mkBrush, mkPen

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

TOTAL_KITS = 125_260

MOCK_PLANTAS = [
    ("SENADO / PLN01",     [(1,18000),(22000,41000),(45000,52772)],    68_975),
    ("SENADO / PLN08",     [(70000,95000),(100000,115000),(118000,124529)], 59_602),
    ("SENADO IND / PLN01", [(1,35000),(38000,66734)],                  91_178),
    ("SENADO IND / PLN05", [(88000,105000),(108000,121331)],           36_659),
    ("CAMARA / PLN01",     [],                                         80_000),
    ("CAMARA IND / PLN04", [(50000,80000),(85000,108346)],            111_166),
    ("CAMARA AFR / PLN01", [(1,25000),(28000,57230)],                  59_211),
    ("CAMARA AFR / PLN05", [(60000,75000),(78000,92837)],              54_305),
    ("CAMARA AFR / PLN06", [(95000,99507)],                           103_445),
    ("CONSULTAS / PLN03",  [],                                         45_000),
]

RFID_DATA = [
    ("Lista chequeo",       [(1,18000),(20000,47000),(50000,65000)],    65_000),
    ("Lateral Izq.",        [(1,15000),(18000,44000),(47000,64800)],    64_800),
    ("Caja Interna",        [(1,20000),(23000,50000),(53000,69145)],    69_145),
    ("S. Claveros",         [(1,18000),(22000,45000),(48000,65995)],    65_995),
    ("S. Delegados",        [(1,30000),(35000,70000),(75000,103015)],  103_015),
]

ESTANDAR_DATA = [
    ("Certificados Elec.", [(1,8000),(10000,20000)],     20_000),
    ("Caja Kit",           [(1,12000),(15000,32500)],    32_500),
    ("Sobre D",            [(1,10000),(12000,27545)],    27_545),
    ("Sobre A",            [(1,1945)],                    1_945),
    ("Caja Kit Municipal", [],                              114),
]


def _lbl(text, pt=9, bold=False, color="#222"):
    l = QLabel(text)
    f = QFont(); f.setPointSize(pt); f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color: {color};")
    return l


def build_chart(filas, title, color_impreso=(76, 175, 80), height=None):
    """Genera un PlotWidget con barras horizontales segmentadas."""
    pg.setConfigOptions(antialias=True)

    n = len(filas)
    plot = pg.PlotWidget(background="#fafafa")
    plot.setMenuEnabled(False)
    plot.showGrid(x=True, y=False, alpha=0.3)
    plot.setXRange(0, TOTAL_KITS, padding=0.01)
    plot.setYRange(-0.5, n - 0.5, padding=0.05)
    plot.getAxis('bottom').setStyle(tickTextOffset=4)
    plot.getAxis('bottom').setLabel(f"Kit 1 → {TOTAL_KITS:,}")

    labels = [f[0] for f in reversed(filas)]
    ticks = [(i, labels[i]) for i in range(n)]
    plot.getAxis('left').setTicks([ticks])
    plot.getAxis('left').setStyle(tickTextOffset=6)

    BAR_H = 0.6

    for idx, (label, segs, _) in enumerate(reversed(filas)):
        y_pos = idx

        # Barra fondo gris
        rect = pg.BarGraphItem(
            x0=0, x1=TOTAL_KITS,
            y=y_pos, height=BAR_H,
            brush=mkBrush(210, 210, 210, 200),
            pen=mkPen(None),
        )
        plot.addItem(rect)

        # Segmentos impresos
        for ini, fin in segs:
            seg = pg.BarGraphItem(
                x0=ini, x1=fin,
                y=y_pos, height=BAR_H,
                brush=mkBrush(*color_impreso, 220),
                pen=mkPen(None),
            )
            plot.addItem(seg)

    if height:
        plot.setFixedHeight(height)

    title_lbl = _lbl(title, pt=10, bold=True, color="#1a1a2e")
    wrapper = QWidget()
    v = QVBoxLayout(wrapper)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(4)
    v.addWidget(title_lbl)
    v.addWidget(plot)
    return wrapper


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo — Opción 3: PyQtGraph")
        self.setMinimumSize(1100, 800)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)

        root.addWidget(_lbl("Tablero de Producción  —  PyQtGraph", pt=13, bold=True, color="#1a1a2e"))
        root.addWidget(_lbl(f"Eje compartido: Kit 1 → Kit {TOTAL_KITS:,}", pt=8, color="#888"))

        # Plantas
        root.addWidget(build_chart(
            MOCK_PLANTAS,
            "TARJETAS POR PLANTA",
            color_impreso=(76, 175, 80),
            height=280,
        ))

        # RFID + Estándar lado a lado
        cols = QHBoxLayout()
        cols.addWidget(build_chart(
            RFID_DATA,
            "IMPRESIÓN RFID",
            color_impreso=(33, 150, 243),
            height=220,
        ))
        cols.addWidget(build_chart(
            ESTANDAR_DATA,
            "IMPRESIÓN ESTÁNDAR",
            color_impreso=(255, 152, 0),
            height=220,
        ))
        root.addLayout(cols)

        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
