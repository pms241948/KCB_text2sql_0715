#!/bin/bash
# Text2SQL 프로젝트 통합 실행 스크립트 (Mac/Linux)
echo "[Text2SQL] 환경 준비 및 서버 실행"

# 1. 가상환경 생성 및 활성화
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2. 백엔드 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 3. 프론트엔드 패키지 설치
npm install

# 4. 백엔드 실행 (백그라운드)
nohup bash -c "source .venv/bin/activate && python app.py" > backend.log 2>&1 &

# 5. 프론트엔드 실행 (백그라운드)
nohup npm start > frontend.log 2>&1 &

# 6. 브라우저 자동 오픈
sleep 3
if which xdg-open > /dev/null; then
  xdg-open http://localhost:3000
elif which open > /dev/null; then
  open http://localhost:3000
fi

echo "서버가 실행되었습니다!" 