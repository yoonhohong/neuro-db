from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QFileDialog, QMessageBox, QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

import database as db
from ui.patient_dialog import PatientDialog
from datetime import datetime


COL_HEADERS = [
    "Patient Name", "Hosp ID", "Sex", "Dx",
    "Date Dx", "Bwt (latest)", "FVC % (latest)",
    "ALSFRS-R (latest)", "Created", "Updated",
]
# DB 컬럼 대응
COL_KEYS = [
    "patient_name", "hosp_id", "sex", "dx",
    "date_dx", "_bwt", "_fvc", "_alsfrs",
    "created_at", "updated_at",
]


def _fmt_latest(value, date) -> str:
    if value is None:
        return "-"
    if date:
        return f"{value} ({date})"
    return str(value)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALS Research Database")
        self.resize(1280, 720)
        self._sort_col = 4   # Date Dx
        self._sort_asc = False
        self._all_rows: list[dict] = []
        self._displayed_ids: list[int] = []

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- 상단 툴바 ---
        toolbar = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("검색 (이름 / Hosp ID / Dx)...")
        self.search_box.setFixedHeight(32)
        self.search_box.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self.search_box, stretch=1)

        new_btn = QPushButton("+ 새 환자")
        new_btn.setFixedHeight(32)
        new_btn.setStyleSheet(
            "background: #4a6fa5; color: white; padding: 0 16px;"
            " border-radius: 4px; font-weight: bold;"
        )
        new_btn.clicked.connect(self._new_patient)
        toolbar.addWidget(new_btn)

        del_btn = QPushButton("환자 삭제")
        del_btn.setFixedHeight(32)
        del_btn.setStyleSheet(
            "background: #c0392b; color: white; padding: 0 16px;"
            " border-radius: 4px; font-weight: bold;"
        )
        del_btn.clicked.connect(self._delete_patient)
        toolbar.addWidget(del_btn)

        csv_btn = QPushButton("CSV 내보내기")
        csv_btn.setFixedHeight(32)
        csv_btn.setStyleSheet(
            "background: #6a994e; color: white; padding: 0 16px;"
            " border-radius: 4px; font-weight: bold;"
        )
        csv_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(csv_btn)

        layout.addLayout(toolbar)

        # --- 테이블 ---
        self.table = QTableWidget()
        self.table.setColumnCount(len(COL_HEADERS))
        self.table.setHorizontalHeaderLabels(COL_HEADERS)
        hdr = self.table.horizontalHeader()
        hdr.setFont(QFont("Arial", 15, QFont.Bold))
        # Patient Name: 남은 공간 모두 차지
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        # 나머지: 고정 너비
        fixed_widths = {
            1: 110,   # Hosp ID
            2: 50,    # Sex
            3: 70,    # Dx
            4: 80,    # Date Dx
            5: 140,   # Bwt (latest)
            6: 130,   # FVC % (latest)
            7: 140,   # ALSFRS-R (latest)
            8: 95,    # Created
            9: 95,    # Updated
        }
        for col, width in fixed_widths.items():
            hdr.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, width)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)  # 수동 정렬 사용
        self.table.setFont(QFont("Arial", 14))
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.table.cellDoubleClicked.connect(self._edit_patient)
        layout.addWidget(self.table)

        # --- 상태바 ---
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(self.status_lbl)

        # 검색 디바운스 타이머
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search)

    # ------------------------------------------------------------------ #

    def _refresh(self):
        search = self.search_box.text().strip()
        self._all_rows = db.get_all_patients(search)
        self._render_table(self._all_rows)

    def _on_search_changed(self):
        self._search_timer.start(250)

    def _apply_search(self):
        self._refresh()

    def _render_table(self, rows: list[dict]):
        # 정렬
        def sort_key(r):
            if COL_KEYS[self._sort_col].startswith("_"):
                # 시계열 최신값
                mapping = {"_bwt": "latest_bwt", "_fvc": "latest_fvc", "_alsfrs": "latest_alsfrs"}
                val = r.get(mapping.get(COL_KEYS[self._sort_col], ""), "")
            else:
                val = r.get(COL_KEYS[self._sort_col], "") or ""
            return val

        rows = sorted(rows, key=sort_key, reverse=not self._sort_asc)

        self._displayed_ids = [r["patient_id"] for r in rows]
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            def cell(text):
                item = QTableWidgetItem(str(text) if text else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                return item

            self.table.setItem(row_idx, 0, cell(row.get("patient_name", "")))
            self.table.setItem(row_idx, 1, cell(row.get("hosp_id", "")))
            self.table.setItem(row_idx, 2, cell(row.get("sex", "")))
            self.table.setItem(row_idx, 3, cell(row.get("dx", "")))
            self.table.setItem(row_idx, 4, cell(row.get("date_dx", "")))
            self.table.setItem(row_idx, 5, cell(
                _fmt_latest(row.get("latest_bwt"), row.get("latest_bwt_date"))
            ))
            fvc = row.get("latest_fvc")
            self.table.setItem(row_idx, 6, cell(
                _fmt_latest(f"{fvc}%" if fvc is not None else None, row.get("latest_fvc_date"))
            ))
            self.table.setItem(row_idx, 7, cell(
                _fmt_latest(row.get("latest_alsfrs"), row.get("latest_alsfrs_date"))
            ))
            # 날짜만 표시 (ISO timestamp → date)
            created = (row.get("created_at") or "")[:10]
            updated = (row.get("updated_at") or "")[:10]
            self.table.setItem(row_idx, 8, cell(created))
            self.table.setItem(row_idx, 9, cell(updated))

        arrow = "▲" if self._sort_asc else "▼"
        for col, hdr in enumerate(COL_HEADERS):
            label = f"{hdr} {arrow}" if col == self._sort_col else hdr
            self.table.horizontalHeaderItem(col).setText(label)

        count = len(rows)
        self.status_lbl.setText(f"총 {count}명")

    def _on_header_clicked(self, col: int):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = False
        self._render_table(self._all_rows)

    # ------------------------------------------------------------------ #

    def _new_patient(self):
        dlg = PatientDialog(parent=self)
        if dlg.exec():
            self._refresh()

    def _edit_patient(self, row: int, _col: int):
        if row >= len(self._displayed_ids):
            return
        patient_id = self._displayed_ids[row]
        dlg = PatientDialog(patient_id=patient_id, parent=self)
        if dlg.exec():
            self._refresh()

    def _delete_patient(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._displayed_ids):
            QMessageBox.warning(self, "선택 없음", "삭제할 환자를 먼저 선택하세요.")
            return
        patient_id = self._displayed_ids[row]
        name = (self.table.item(row, 0) or QTableWidgetItem("")).text()
        hosp_id = (self.table.item(row, 1) or QTableWidgetItem("")).text()
        confirm = QMessageBox.question(
            self, "환자 삭제",
            f"다음 환자를 삭제하시겠습니까?\n\n이름: {name}\nHosp ID: {hosp_id}\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                db.delete_patient(patient_id)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "삭제 오류", str(e))

    def _export_csv(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"neuro_db_export_{timestamp}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV 내보내기", default_name, "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            # 현재 표시된 환자만 내보내기
            ids = self._displayed_ids if self._displayed_ids else None
            db.export_to_csv(ids, path)
            QMessageBox.information(self, "완료", f"저장되었습니다:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
