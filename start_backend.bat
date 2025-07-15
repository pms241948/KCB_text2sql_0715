@echo off
echo ========================================
echo KCB Text2SQL Backend Server Starting...
echo ========================================

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo Python을 설치한 후 다시 시도해주세요.
    pause
    exit /b 1
)

echo ✅ Python 설치 확인 완료

REM 백엔드 디렉토리로 이동 (절대 경로 사용)
cd /d "%~dp0backend"

REM 가상환경 확인 및 생성
if not exist ".venv" (
    echo 🔧 가상환경을 생성합니다...
    python -m venv .venv
)

REM 가상환경 활성화
echo 🔧 가상환경을 활성화합니다...
call .venv\Scripts\activate

REM pip 업그레이드
echo 🔧 pip를 업그레이드합니다...
python -m pip install --upgrade pip

REM 의존성 설치
echo 🔧 필요한 패키지들을 설치합니다...
pip install -r requirements.txt

REM 환경 변수 파일 확인
if not exist ".env" (
    echo ⚠️ .env 파일이 없습니다. env.example을 복사합니다...
    copy env.example .env
    echo 📝 .env 파일에서 API 키를 설정해주세요.
)

echo 🚀 백엔드 서버를 시작합니다...
echo 📝 API 문서: http://localhost:5000
echo ⏹️  서버를 중지하려면 Ctrl+C를 누르세요.

REM Flask 앱 실행
python -m api.app

pause 