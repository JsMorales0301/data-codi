import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets")


def _lbl(text: str, pt: int = 10, bold: bool = False, color: str | None = None) -> QLabel:
    l = QLabel(text)
    f = QFont()
    f.setPointSize(pt)
    f.setBold(bold)
    l.setFont(f)
    if color:
        l.setStyleSheet(f"color: {color};")
    return l


class _ModuleCard(QFrame):
    MODULES = [
        ("Simulacro",               "Parametrización y generación\nde archivos para el simulacro."),
        ("Cargue",                  "Procesamiento e ingesta de\narchivos de datos electorales."),
    ]

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        layout.addWidget(_lbl(title, pt=11, bold=True))

        desc = _lbl(description, pt=9, color="#555")
        desc.setWordWrap(True)
        layout.addWidget(desc)


class HomeView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center = QWidget()
        center.setMaximumWidth(700)
        vbox = QVBoxLayout(center)
        vbox.setSpacing(0)
        vbox.setContentsMargins(40, 40, 40, 40)

        # Logo
        logo_path = os.path.normpath(os.path.join(_ASSETS_DIR, "logo-o.png"))
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_lbl = QLabel()
            logo_lbl.setPixmap(
                pixmap.scaledToHeight(90, Qt.TransformationMode.SmoothTransformation)
            )
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(logo_lbl)
            vbox.addSpacing(12)

        # Título
        title = _lbl("CODI", pt=32, bold=True, color="#1a1a2e")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        subtitle = _lbl(
            "Módulo de procesamiento de información electoral",
            pt=12, color="#555",
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(subtitle)

        vbox.addSpacing(12)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        vbox.addWidget(line)

        vbox.addSpacing(28)

        desc = _lbl(
            "Bienvenido. Usa el menú superior para navegar entre los módulos disponibles.",
            pt=10, color="#444",
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        vbox.addWidget(desc)

        vbox.addSpacing(32)

        # Tarjetas de módulos
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for title_text, desc_text in _ModuleCard.MODULES:
            cards_row.addWidget(_ModuleCard(title_text, desc_text))
        vbox.addLayout(cards_row)

        root.addWidget(center, alignment=Qt.AlignmentFlag.AlignCenter)
