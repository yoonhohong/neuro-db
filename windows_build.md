# Windows 빌드 및 배포 가이드

## 환경

- Python 3.14.3
- PyInstaller 6.19.0
- PySide6 6.10.2

## 코드 받기

**처음 빌드하는 경우 (저장소가 아직 없을 때):**
```powershell
cd C:\Users\BRMH\Hong
git clone https://github.com/yoonhohong/neuro-db.git
cd neuro-db
```

**이미 clone된 저장소가 있고 최신 코드로 업데이트할 때:**
```powershell
cd C:\Users\BRMH\Hong\neuro-db
git pull origin main
```

## 빌드 방법

**가상환경 생성 (처음 한 번만):**
```powershell
python -m venv .venv
```

**가상환경 활성화 (매번):**
```powershell
.venv\Scripts\Activate.ps1
```
활성화되면 프롬프트 앞에 `(.venv)`가 붙습니다. 끌 때는 `deactivate`.

**의존성 설치 및 빌드:**
```powershell
python -m pip install -r requirements.txt
python -m PyInstaller build.spec
```

결과물: `dist\ALS Research Database.exe` (단일 실행 파일, 약 44MB)

## 배포 파일 만들기

```powershell
Compress-Archive -Path "dist\ALS Research Database.exe" -DestinationPath "dist\ALS Research Database_Windows.zip" -Force
```

## GitHub Releases 업로드

```powershell
# 새 릴리즈 생성 시
gh release create v1.0.0 "dist\ALS Research Database_Windows.zip" --title "ALS Research Database v1.0.0" --notes "릴리즈 노트"

# 기존 릴리즈에 파일 추가 시
gh release upload v1.0.0 "dist\ALS Research Database_Windows.zip"
```

## 참고

- `pip` 단독 명령은 동작하지 않으므로 반드시 `python -m pip` 사용
- `.venv\Scripts\Activate.ps1` 실행 시 "이 시스템에서 스크립트 실행이 금지되어 있습니다" 오류가 나면, PowerShell을 관리자 권한으로 열어 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 실행 후 다시 시도
- GitHub 계정: yoonhohong
- 릴리즈 페이지: https://github.com/yoonhohong/neuro-db/releases
