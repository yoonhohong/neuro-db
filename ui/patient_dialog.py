from PySide6.QtWidgets import (
    QDialog, QSplitter, QTextEdit, QScrollArea, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

import database as db
import parser as ps


class ParsePreviewWidget(QScrollArea):
    """파싱 결과를 키-값 목록으로 표시하는 우측 패널."""

    SECTION_KEYS = {
        "기본 정보": [
            ("patient_name", "Patient Name"),
            ("hosp_id", "Hosp ID"),
            ("sex", "Sex"),
            ("age_at_dx", "Age at Dx"),
            ("dx", "Dx"),
            ("dx_others", "Dx (others)"),
            ("date_onset", "Date Onset"),
            ("date_dx", "Date Dx"),
            ("date_entry", "Date Entry"),
        ],
        "임상 소견": [
            ("onset_bctl", "Onset Region"),
            ("lmn_bctl", "LMN"),
            ("umn_bctl", "UMN"),
            ("emg_bctl", "EMG"),
            ("pseudobulbar_affect", "Pseudobulbar Affect"),
            ("dementia", "Dementia"),
        ],
        "약물": [
            ("riluzole_start", "Riluzole Start"),
            ("riluzole_end", "Riluzole End"),
            ("edaravone_start", "Edaravone Start"),
            ("edaravone_end", "Edaravone End"),
        ],
        "경과": [
            ("progression_onset2dx", "Progression (onset→dx)"),
            ("progression_afterdx", "Progression (after dx)"),
        ],
        "임상 지표": [
            ("height_cm", "Height (cm)"),
            ("body_weight", "Body Weight"),
            ("fvc_records", "FVC (%)"),
            ("alsfrs_records", "ALSFRS-R"),
            ("gastrostomy_date", "Gastrostomy"),
            ("niv_date", "NIV"),
            ("tracheostomy_date", "Tracheostomy"),
            ("death_date", "Death"),
        ],
        "검사": [
            ("brain_mri", "Brain MRI"),
            ("spine_mri", "Spine MRI"),
            ("genetic_test", "Genetic Test"),
            ("cognitive_test", "Cognitive Test"),
            ("chest_ct", "Chest CT"),
            ("abdomen_ct", "Abdomen CT"),
        ],
        "시료": [
            ("buffy_coat", "Buffy Coat"),
            ("plasma", "Plasma"),
            ("serum", "Serum"),
            ("csf", "CSF"),
        ],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.setSpacing(2)
        self.setWidget(self._container)

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _bctl_display(self, parsed, prefix):
        parts = []
        mapping = [("b", "Bulbar"), ("c", "Cervical"), ("t", "Thoracic"), ("l", "Lumbar")]
        for key, label in mapping:
            if parsed.get(f"{prefix}_{key}"):
                parts.append(label)
        if parsed.get(f"{prefix}_none"):
            parts.append("None")
        if prefix == "emg" and parsed.get("emg_not_checked"):
            parts.append("NotChecked")
        return ", ".join(parts) if parts else "-"

    def _timeseries_display(self, records, value_key, unit=""):
        if not records:
            return "-"
        parts = [f"{r[value_key]}{unit} ({r['date']})" for r in records if r.get("date")]
        bwt_pm = next((r for r in records if r.get("is_premorbid")), None)
        if bwt_pm:
            parts = [f"{bwt_pm['weight_kg']} (premorbid)"] + parts
        return " → ".join(parts) if parts else "-"

    def update_preview(self, parsed: dict, errors: list[str]):
        self._clear()

        # 오류/경고
        if errors:
            for err in errors:
                lbl = QLabel(f"⚠  {err}")
                lbl.setStyleSheet("color: #cc6600; background: #fff8e7; padding: 3px; border-radius: 3px;")
                lbl.setWordWrap(True)
                self._layout.addWidget(lbl)
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            self._layout.addWidget(sep)

        for section, keys in self.SECTION_KEYS.items():
            # 섹션 헤더
            hdr = QLabel(section)
            hdr.setStyleSheet(
                "font-weight: bold; color: white; background: #4a6fa5;"
                " padding: 3px 6px; border-radius: 3px;"
            )
            self._layout.addWidget(hdr)

            for key, label in keys:
                if key == "onset_bctl":
                    val = self._bctl_display(parsed, "onset")
                elif key == "lmn_bctl":
                    val = self._bctl_display(parsed, "lmn")
                elif key == "umn_bctl":
                    val = self._bctl_display(parsed, "umn")
                elif key == "emg_bctl":
                    val = self._bctl_display(parsed, "emg")
                elif key == "body_weight":
                    val = self._timeseries_display(parsed.get("body_weight", []), "weight_kg", " kg")
                elif key == "fvc_records":
                    val = self._timeseries_display(parsed.get("fvc_records", []), "fvc_percent", "%")
                elif key == "alsfrs_records":
                    val = self._timeseries_display(parsed.get("alsfrs_records", []), "score")
                else:
                    raw = parsed.get(key)
                    val = str(raw) if raw is not None and raw != "" else "-"

                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(4, 1, 4, 1)
                row_layout.setSpacing(8)

                key_lbl = QLabel(f"{label}:")
                key_lbl.setFixedWidth(160)
                key_lbl.setStyleSheet("color: #555; font-size: 12px;")
                key_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                val_lbl = QLabel(val)
                val_lbl.setWordWrap(True)
                val_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                if val == "-":
                    val_lbl.setStyleSheet("color: #aaa; font-size: 12px;")
                else:
                    val_lbl.setStyleSheet("color: #111; font-size: 12px; font-weight: bold;")

                row_layout.addWidget(key_lbl)
                row_layout.addWidget(val_lbl)
                self._layout.addWidget(row)

        self._layout.addStretch()


def _validate(parsed: dict) -> list[str]:
    errors = []
    if not parsed.get("patient_name"):
        errors.append("Patient Name 미입력")
    if not parsed.get("hosp_id"):
        errors.append("Hosp ID 미입력")
    if not parsed.get("dx"):
        errors.append("Dx 미입력")
    return errors


class PatientDialog(QDialog):
    def __init__(self, patient_id: int | None = None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self._parsed: dict | None = None

        title = "새 환자 입력" if patient_id is None else "환자 편집"
        self.setWindowTitle(title)
        self.resize(1100, 750)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # 스플리터: 좌(텍스트) / 우(미리보기)
        splitter = QSplitter(Qt.Horizontal)

        # 좌: 텍스트 에디터
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        editor_lbl = QLabel("텍스트 입력 (템플릿을 채워넣거나 붙여넣기)")
        editor_lbl.setStyleSheet("color: #555; font-size: 13px; font-weight: bold;")
        left_layout.addWidget(editor_lbl)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Courier New", 12))
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText("여기에 텍스트를 입력하거나 붙여넣기 하세요...")
        left_layout.addWidget(self.editor)

        parse_btn = QPushButton("파싱")
        parse_btn.setStyleSheet(
            "background: #4a6fa5; color: white; padding: 6px 20px;"
            " border-radius: 4px; font-weight: bold;"
        )
        parse_btn.clicked.connect(self._do_parse)
        left_layout.addWidget(parse_btn, alignment=Qt.AlignRight)

        splitter.addWidget(left)

        # 우: 미리보기
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_lbl = QLabel("파싱 결과 미리보기")
        preview_lbl.setStyleSheet("color: #555; font-size: 13px; font-weight: bold;")
        right_layout.addWidget(preview_lbl)

        self.preview = ParsePreviewWidget()
        right_layout.addWidget(self.preview)
        splitter.addWidget(right)

        splitter.setSizes([580, 480])
        main_layout.addWidget(splitter)

        # 하단 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("저장")
        save_btn.setStyleSheet(
            "background: #2e7d32; color: white; padding: 6px 24px;"
            " border-radius: 4px; font-weight: bold;"
        )
        save_btn.clicked.connect(self._do_save)

        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet("padding: 6px 20px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

    def _load_data(self):
        if self.patient_id is None:
            self.editor.setPlainText(ps.TEMPLATE)
        else:
            patient = db.get_patient_by_id(self.patient_id)
            if patient:
                self.editor.setPlainText(ps.format_patient_as_template(patient))
                self._do_parse()

    def _do_parse(self):
        text = self.editor.toPlainText()
        self._parsed = ps.parse_template(text)
        errors = _validate(self._parsed)
        self.preview.update_preview(self._parsed, errors)

    def _do_save(self):
        self._do_parse()
        if self._parsed is None:
            return

        errors = _validate(self._parsed)
        if errors:
            QMessageBox.warning(
                self, "입력 오류",
                "다음 항목을 확인해 주세요:\n" + "\n".join(f"• {e}" for e in errors),
            )
            return

        try:
            if self.patient_id is None:
                db.insert_patient(self._parsed)
            else:
                db.update_patient(self.patient_id, self._parsed)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", str(e))
