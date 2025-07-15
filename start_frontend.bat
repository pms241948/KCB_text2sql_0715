@echo off
echo ========================================
echo KCB Text2SQL Frontend Starting...
echo ========================================
echo 프론트엔드(React) 서버 실행
echo 반드시 백엔드(start_backend.bat)가 먼저 실행된 후 사용하세요!

REM 프론트엔드 디렉토리로 이동
cd /d "%~dp0frontend"

REM React 앱 실행 (새 cmd 창에서)
start "React Frontend" cmd /k "npm install && npm start" 