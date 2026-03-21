import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import database as db
from ui.main_window import MainWindow


def main():
    db.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("ALS Research Database")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
