from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, QEvent

from codi.ui.views.home_view import HomeView
from codi.ui.views.parametrizacion_view import ParametrizacionView
from codi.ui.views.generacion_archivos_view import GeneracionArchivosView
from codi.ui.views.cargue_view import CargueView
from codi.ui.views.impresion_view import ImpresionView


class _MenuHoverFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseMove:
            action = watched.actionAt(event.pos())
            if action:
                watched.setActiveAction(action)
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codi")
        self.setMinimumSize(800, 600)
        self._setup_views()
        self._setup_menu()

    def _setup_views(self):
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home_view = HomeView()
        self._parametrizacion_view = ParametrizacionView()
        self._generacion_archivos_view = GeneracionArchivosView()
        self._cargue_view = CargueView()
        self._impresion_view = ImpresionView()

        self._stack.addWidget(self._home_view)
        self._stack.addWidget(self._parametrizacion_view)
        self._stack.addWidget(self._generacion_archivos_view)
        self._stack.addWidget(self._cargue_view)
        self._stack.addWidget(self._impresion_view)

    def _setup_menu(self):
        menu_bar = self.menuBar()
        menu_bar.setMouseTracking(True)
        menu_bar.installEventFilter(_MenuHoverFilter(self))

        home_action = QAction("Inicio", self)
        home_action.triggered.connect(
            lambda: self._stack.setCurrentWidget(self._home_view)
        )
        menu_bar.addAction(home_action)

        simulacro_menu = menu_bar.addMenu("Simulacro")

        parametrizacion_action = QAction("Parametrización", self)
        parametrizacion_action.triggered.connect(
            lambda: self._stack.setCurrentWidget(self._parametrizacion_view)
        )
        simulacro_menu.addAction(parametrizacion_action)

        gen_archivos_action = QAction("Generación de archivos", self)
        gen_archivos_action.triggered.connect(
            lambda: self._stack.setCurrentWidget(self._generacion_archivos_view)
        )
        simulacro_menu.addAction(gen_archivos_action)

        cargue_action = QAction("Cargue", self)
        cargue_action.triggered.connect(
            lambda: self._stack.setCurrentWidget(self._cargue_view)
        )
        menu_bar.addAction(cargue_action)

        impresion_menu = menu_bar.addMenu("Impresión")

        tablero_action = QAction("Tablero de Producción", self)
        tablero_action.triggered.connect(
            lambda: self._stack.setCurrentWidget(self._impresion_view)
        )
        impresion_menu.addAction(tablero_action)
