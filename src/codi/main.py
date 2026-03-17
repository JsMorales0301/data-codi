import sys

from PySide6.QtWidgets import QApplication

from codi.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Codi")
    app.setApplicationVersion("0.1.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
