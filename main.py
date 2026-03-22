import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

import database as db
from ui.main_window import MainWindow


def _light_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window,          QColor(255, 255, 255))
    p.setColor(QPalette.WindowText,      QColor(0,   0,   0))
    p.setColor(QPalette.Base,            QColor(255, 255, 255))
    p.setColor(QPalette.AlternateBase,   QColor(245, 245, 245))
    p.setColor(QPalette.Text,            QColor(0,   0,   0))
    p.setColor(QPalette.Button,          QColor(240, 240, 240))
    p.setColor(QPalette.ButtonText,      QColor(0,   0,   0))
    p.setColor(QPalette.Highlight,       QColor(74,  111, 165))
    p.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    return p


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("ALS Research Database")
    app.setStyle("Fusion")
    app.setPalette(_light_palette())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
