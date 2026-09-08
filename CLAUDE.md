# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

다기관 ALS(루게릭병) 연구용 standalone 데스크톱 앱. 병원 간 데이터 공유 없이 각 기관이 독립적으로 운용하는 로컬 SQLite DB 앱.

**기술 스택:** Python 3.11+, PySide6, SQLite, PyInstaller

## 개발 명령어

```bash
# 가상환경 (이미 .venv 존재)
source .venv/bin/activate
pip install -r requirements.txt

# 앱 실행
python main.py

# 빌드 (macOS/Windows 겸용 spec, sys.platform 분기)
pyinstaller build.spec
# 결과물: dist/ALS Research Database.app (macOS) / dist/ALS Research Database.exe (Windows)
```

자동화된 테스트/린트는 구성되어 있지 않다. 파서 로직 변경 시 `python main.py`로 직접 입력 → 저장 → 재편집 왕복을 확인할 것.

DB 파일 위치는 `database.get_db_path()`가 결정한다: `~/Documents/neuro-db/neuro_db.sqlite` (Windows는 `%USERPROFILE%` 기준). 리셋하려면 이 파일을 삭제하면 된다(다음 실행 시 `init_db()`가 재생성).

## 아키텍처

### 텍스트 템플릿 ↔ DB 왕복 파싱 (핵심 설계)

이 앱의 데이터 입력은 폼 위젯이 아니라 **자유 텍스트 템플릿**이다. `PatientDialog`(`ui/patient_dialog.py`)는 좌측에 텍스트 에디터, 우측에 파싱 결과 미리보기 패널을 스플리터로 배치한다:

- `parser.TEMPLATE`: 빈 템플릿 문자열 (신규 환자 입력 시 기본값)
- `parser.parse_template(text) -> dict`: 템플릿 텍스트를 파싱해 DB insert/update에 쓸 dict 생성
- `parser.format_patient_as_template(patient_dict) -> dict`: DB row를 다시 편집 가능한 템플릿 텍스트로 역변환 (편집 시 사용)

파싱 규칙(템플릿 주석에 명시): 단일 선택 항목은 값 하나만 남기고 나머지 삭제, BCTL 항목(Onset/LMN/UMN/EMG)은 해당 문자만 남김, 날짜는 `YYYY-MM`(이벤트) 또는 `YYYY-MM-DD`(검사/시료), 시계열 값은 `"값 (YYYY-MM) > 값 (YYYY-MM)"` 형식.

새 필드를 추가할 때는 4곳을 동시에 수정해야 한다: `parser.TEMPLATE`(템플릿 라인) → `parser.parse_template`(파싱 로직) → `parser.format_patient_as_template`(역변환) → `database.PATIENT_FIELDS`/스키마(`init_db`). 하나라도 누락하면 편집 왕복 시 데이터가 유실된다.

### DB 스키마

`patients` 테이블 하나에 대부분의 필드가 평탄화되어 있고(BCTL 항목은 `onset_b`, `onset_c` 등 boolean 컬럼으로 분해), 시계열 데이터만 별도 테이블로 분리되어 있다:

- `body_weight` (premorbid 체중 포함, `is_premorbid` 플래그로 구분)
- `fvc_records`
- `alsfrs_records`

시계열 저장은 `database._insert_timeseries()`에서 매번 해당 patient_id의 기존 행을 전부 `DELETE` 후 재삽입하는 방식이다(개별 UPDATE 없음) — 편집 시 파싱된 전체 리스트로 덮어쓴다는 뜻.

스키마 마이그레이션은 `init_db()` 안에서 `PRAGMA table_info`로 컬럼 존재 여부를 확인하고 없으면 `ALTER TABLE ADD COLUMN`하는 방식으로 처리한다(예: `date_entry`). 별도 마이그레이션 프레임워크는 없다.

### UI 흐름

- `ui/main_window.py`: 환자 목록 테이블. 검색은 250ms 디바운스(`QTimer`), 정렬은 컬럼 헤더 클릭으로 토글(수동 정렬, `QTableWidget.setSortingEnabled`는 미사용). 시계열 컬럼(Bwt/FVC/ALSFRS-R)은 `get_all_patients()`가 서브쿼리로 계산한 최신값을 표시.
- `ui/patient_dialog.py`: 신규/편집 겸용 다이얼로그. `ParsePreviewWidget`이 파싱된 dict를 사람이 읽을 수 있는 섹션별 키-값 목록으로 렌더링(저장 전 검증용). 저장 시 `_validate()`가 필수 필드(이름/Hosp ID/Dx)만 확인 — 나머지는 자유 입력이라 서버 측 강한 검증은 없음.

CSV 내보내기(`database.export_to_csv`)는 시계열을 `bwt_1_kg`, `bwt_1_date`, `bwt_2_kg`... 식으로 넓게 펼쳐서(wide format) 한 줄에 담는다.
