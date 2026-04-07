"""
Demo Opción 2 — Plotly HTML dentro de QWebEngineView
Ejecutar: uv run python demos/demo_plotly.py
"""
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

TOTAL_KITS = 125_260

MOCK_PLANTAS = [
    # (tarjeta, planta, segmentos [(ini,fin),...], total_asignado)
    ("SENADO",      "PLN01", [(1,18000),(22000,41000),(45000,52772)],    68_975),
    ("SENADO",      "PLN08", [(70000,95000),(100000,115000),(118000,124529)], 59_602),
    ("SENADO IND",  "PLN01", [(1,35000),(38000,66734)],                  91_178),
    ("SENADO IND",  "PLN05", [(88000,105000),(108000,121331)],           36_659),
    ("CAMARA",      "PLN01", [],                                         80_000),
    ("CAMARA IND",  "PLN04", [(50000,80000),(85000,108346)],            111_166),
    ("CAMARA AFR",  "PLN01", [(1,25000),(28000,57230)],                  59_211),
    ("CAMARA AFR",  "PLN05", [(60000,75000),(78000,92837)],              54_305),
    ("CAMARA AFR",  "PLN06", [(95000,99507)],                           103_445),
    ("CONSULTAS",   "PLN03", [],                                         45_000),
]

RFID_DATA = [
    ("Lista chequeo",       [(1,18000),(20000,47000),(50000,65000)],    65_000),
    ("Lateral Izq.",        [(1,15000),(18000,44000),(47000,64800)],    64_800),
    ("Lateral Posterior",   [(1,15000),(18000,44000),(47000,64800)],    64_800),
    ("Caja Interna",        [(1,20000),(23000,50000),(53000,69145)],    69_145),
    ("S. Material NO útil", [(1,12000),(16000,38000),(41000,53145)],    53_145),
    ("S. Claveros",         [(1,18000),(22000,45000),(48000,65995)],    65_995),
    ("S. Delegados",        [(1,30000),(35000,70000),(75000,103015)],  103_015),
    ("Trans. Disc.",        [(1,1268)],                                   1_268),
]

ESTANDAR_DATA = [
    ("Certificados Elec.", [(1,8000),(10000,20000)],     20_000),
    ("Caja Kit",           [(1,12000),(15000,32500)],    32_500),
    ("Sobre A",            [(1,1945)],                    1_945),
    ("Sobre C",            [(1,1945)],                    1_945),
    ("Sobre D",            [(1,10000),(12000,27545)],    27_545),
    ("Sobre G",            [(1,1945)],                    1_945),
    ("Cartuchera",         [(1,1945)],                    1_945),
    ("Caja Kit Municipal", [],                              114),
    ("Señalización",       [],                              114),
]


def _barras_gantt(filas, col_impreso="#4CAF50", col_pendiente="#D9D9D9"):
    """
    Genera trazas de Plotly para barras segmentadas tipo Gantt horizontal.
    Cada fila: (label, segmentos, total_asignado)
    """
    traces = []
    y_labels = []

    for label, segs, total_asig in reversed(filas):
        impresos = sum(f - i for i, f in segs)
        pct = round(impresos / TOTAL_KITS * 100, 1)
        y_label = f"{label}  <b>{impresos:,}</b> ({pct}%)"
        y_labels.append(y_label)

        # Fondo completo gris (pendiente)
        traces.append(go.Bar(
            x=[TOTAL_KITS], y=[y_label],
            orientation='h',
            marker_color=col_pendiente,
            showlegend=False,
            hoverinfo='skip',
        ))

        # Segmentos impresos (verde)
        for ini, fin in segs:
            w = fin - ini
            traces.append(go.Bar(
                x=[w], y=[y_label],
                orientation='h',
                base=ini,
                marker_color=col_impreso,
                showlegend=False,
                hovertemplate=f"<b>{label}</b><br>Kit {ini:,} → {fin:,}<br>Cantidad: {w:,}<extra></extra>",
            ))

    return traces


def build_html():
    filas_plantas = [(f"{t} / {p}", segs, asig) for t, p, segs, asig in MOCK_PLANTAS]

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.45, 0.30, 0.25],
        subplot_titles=["Tarjetas por Planta", "Impresión RFID", "Impresión Estándar (Actas / Kits)"],
        vertical_spacing=0.07,
    )

    for trace in _barras_gantt(filas_plantas):
        fig.add_trace(trace, row=1, col=1)

    for trace in _barras_gantt(RFID_DATA, col_impreso="#2196F3"):
        fig.add_trace(trace, row=2, col=1)

    for trace in _barras_gantt(ESTANDAR_DATA, col_impreso="#FF9800"):
        fig.add_trace(trace, row=3, col=1)

    fig.update_layout(
        title=dict(text="Tablero de Producción  —  Plotly + WebEngineView", font_size=16),
        barmode='overlay',
        height=950,
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        margin=dict(l=180, r=80, t=80, b=40),
        font=dict(family="Segoe UI, Arial", size=11),
    )

    for row in [1, 2, 3]:
        fig.update_xaxes(range=[0, TOTAL_KITS], tickformat=",", row=row, col=1,
                         title_text=f"Kit 1 → {TOTAL_KITS:,}")
        fig.update_yaxes(tickfont_size=10, row=row, col=1)

    return fig.to_html(include_plotlyjs='cdn', full_html=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo — Opción 2: Plotly + WebEngineView")
        self.setMinimumSize(1100, 800)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web = QWebEngineView()
        self.web.setHtml(build_html())
        layout.addWidget(self.web)

        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
