#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KCB Text2SQL 프로젝트 메인 실행 파일
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 백엔드 API 실행
if __name__ == "__main__":
    from backend.api.app import app
    
    # 환경 변수 설정 (기본값)
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    print("🚀 KCB Text2SQL 서버를 시작합니다...")
    print("📝 API 문서: http://localhost:5000")
    print("🌐 프론트엔드: http://localhost:3000")
    print("⏹️  서버를 중지하려면 Ctrl+C를 누르세요.")
    
    # Flask 앱 실행
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    ) 