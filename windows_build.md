# Windows 빌드 및 배포 가이드

## 환경

- Python 3.14.3
- PyInstaller 6.19.0
- PySide6 6.10.2

## 빌드 방법

```powershell
cd C:\Users\BRMH\Hong\neuro-db

# 의존성 설치
python -m pip install -r requirements.txt

# 빌드
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
- GitHub 계정: yoonhohong
- 릴리즈 페이지: https://github.com/yoonhohong/neuro-db/releases
