# Changelog

버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다 (MAJOR.MINOR.PATCH).
- MAJOR: DB 스키마가 깨지거나 마이그레이션 없이 호환 안 되는 변경
- MINOR: 새 기능·파싱 규칙 추가 (하위 호환)
- PATCH: 버그 수정만

## [1.2.0] - 2026-09-08

### 추가
- 환자 목록: 모든 컬럼을 마우스로 드래그해 폭 조절 가능. Patient Name 컬럼이 나머지 컬럼이 차지하고 남는 공간을 자동으로 채워, 컬럼을 조절해도 전체 폭 합계는 항상 창 너비와 같게 유지됨

### 변경
- UI: 환자 목록 헤더/본문 폰트 크기 축소, Date Dx·ALSFRS-R(latest) 컬럼 폭 확대

### 수정 (버그)
- 환자 목록에서 Bwt/FVC/ALSFRS-R(latest) 컬럼 정렬 시, 해당 값이 없는 환자가 섞여 있으면 앱이 종료되던 문제 수정
- CSV 내보내기: 검색 필터 결과가 0건일 때 필터를 무시하고 전체 환자를 내보내던 문제 수정 (이제 내보낸 환자 수를 안내 메시지로 표시)
- Windows 빌드: conda/miniconda 기반 Python으로 빌드할 경우 sqlite3.dll이 실행 파일에 누락되어 앱이 아예 실행되지 않던 문제 수정 (`ImportError: DLL load failed while importing _sqlite3`)

### 참고
- DB 스키마 변경 없음 (기존 데이터 그대로 호환)

## [1.1.0] - 2026-09-08

### 변경
- Sex: Male/male/m/M/남자/남/남성 → M, Female 계열 → F로 통일 인식
- Dx: 옵션 제한 없이 입력한 텍스트 그대로 저장
- Onset_region/LMN/UMN/EMG: Bulbar/Cervical/Thoracic/Respiratory/Lumbar 등 단어 입력도 인식 (BCTL 문자 코드와 병행)
- Pseudobulbar affect/Dementia: Yes/Present/No/Absent/Indeterminate/Unknown 등 별칭 인식
- 파싱 결과 화면: Remarks를 별도 섹션으로 분리, 날짜 순서(Onset→Entry→Dx) 정리, BCTL 표시를 문자 코드로 단순화, Bwt/FVC 표시에서 단위(kg/%) 제거
- UI: 환자 목록·편집 화면 라벨 및 폰트 크기 조정

### 수정 (버그)
- Bwt/FVC/ALSFRS-R: 값에 kg/% 같은 단위가 붙으면 파싱이 안 되던 문제 수정
- Pseudobulbar affect/Dementia: 템플릿의 "(at entry)" 표기 때문에 값이 전혀 저장되지 않던 문제 수정

### 참고
- DB 스키마 변경 없음 (기존 데이터 그대로 호환)

## [1.0.0] - 2026-03-22

- 최초 배포 (환자 목록/검색/정렬/삭제, 텍스트 템플릿 파싱, CSV 내보내기, macOS/Windows 빌드)
