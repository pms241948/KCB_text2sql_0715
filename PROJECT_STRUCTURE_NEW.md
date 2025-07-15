# KCB Text2SQL 프로젝트 구조 (개선된 버전)

## 📁 프로젝트 구조

```
KCB_text2sql_front/
├── 📁 backend/                    # 백엔드 관련 파일들
│   ├── 📁 api/                   # API 관련 파일들
│   │   ├── __init__.py
│   │   └── app.py               # 메인 Flask 애플리케이션
│   ├── 📁 services/              # 비즈니스 로직 서비스들
│   │   ├── __init__.py
│   │   ├── rag_service.py       # RAG 서비스
│   │   └── dynamic_dictionary_manager.py  # 동적 딕셔너리 관리
│   ├── 📁 preprocessing/         # 전처리 관련 모듈들
│   │   ├── __init__.py
│   │   ├── preprocessing_agent.py      # 한국어 전처리 에이전트
│   │   └── hybrid_preprocessing_agent.py  # 혼합 전처리 에이전트
│   ├── 📁 config/               # 설정 파일들
│   │   ├── __init__.py
│   │   ├── config.py            # 기본 설정
│   │   └── sllm_config.py       # sLLM 설정
│   ├── 📁 utils/                # 유틸리티 함수들
│   │   ├── __init__.py
│   │   └── utils.py             # 공통 유틸리티 함수
│   ├── requirements.txt         # Python 의존성
│   └── env.example              # 환경 변수 예시
├── 📁 frontend/                  # 프론트엔드 관련 파일들
│   ├── 📁 public/               # 정적 파일들
│   │   └── index.html
│   ├── 📁 src/                  # React 소스 코드
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   ├── index.css
│   │   ├── RagFileManager.js
│   │   ├── RagFileManager.css
│   │   ├── RagStats.js
│   │   └── RagStats.css
│   ├── package.json             # Node.js 의존성
│   └── package-lock.json
├── 📁 data/                     # 데이터 파일들
│   ├── 📁 dictionaries/         # 딕셔너리 파일들
│   │   ├── credit_terms.json    # 신용평가 도메인 용어
│   │   └── sql_patterns.json    # SQL 패턴
│   ├── 📁 rag_files/           # RAG 관련 파일들
│   │   ├── personal_credit/
│   │   ├── corporate_credit/
│   │   └── policy_regulation/
│   └── 📁 metadata/            # 메타데이터 파일들
│       ├── 고객_기본정보_20230701.xlsx
│       ├── 기업_매출_20230701.xlsx
│       └── 상품_재고_20230701.xlsx
├── 📁 database/                 # 데이터베이스 관련 파일들
│   └── chroma.sqlite3          # ChromaDB 데이터베이스
├── 📁 docker/                   # Docker 관련 파일들
│   ├── Dockerfile.backend      # 백엔드 Docker 이미지
│   ├── Dockerfile.frontend     # 프론트엔드 Docker 이미지
│   └── docker-compose.yml      # Docker Compose 설정
├── 📁 docs/                     # 문서 파일들
│   ├── README.md               # 프로젝트 설명서
│   ├── PROJECT_STRUCTURE.md    # 프로젝트 구조 문서
│   └── 📁 text2sql_image/      # 프로젝트 이미지들
├── main.py                     # 메인 실행 파일
├── start_backend.bat           # 백엔드 시작 스크립트 (Windows)
├── start_frontend.bat          # 프론트엔드 시작 스크립트 (Windows)
├── start.sh                    # 시작 스크립트 (Linux/Mac)
└── .gitignore                  # Git 무시 파일
```

## 🔄 주요 변경사항

### 1. 모듈화 및 패키지 구조
- **백엔드 모듈화**: `backend/` 폴더 아래에 기능별로 분리
  - `api/`: Flask 애플리케이션 및 API 엔드포인트
  - `services/`: 비즈니스 로직 서비스
  - `preprocessing/`: 전처리 관련 모듈
  - `config/`: 설정 파일들
  - `utils/`: 유틸리티 함수들

### 2. 데이터 구조 개선
- **데이터 분리**: `data/` 폴더로 모든 데이터 파일 통합
  - `dictionaries/`: JSON 기반 딕셔너리 파일들
  - `rag_files/`: RAG 문서 파일들
  - `metadata/`: 엑셀 메타데이터 파일들

### 3. 설정 및 실행 개선
- **메인 실행 파일**: `main.py`로 통합된 실행 포인트
- **Docker 구조**: `docker/` 폴더로 Docker 관련 파일 통합
- **문서화**: `docs/` 폴더로 모든 문서 통합

## 🚀 실행 방법

### 1. 전체 프로젝트 실행
```bash
# 메인 실행 파일 사용
python main.py
```

### 2. 개별 실행
```bash
# 백엔드만 실행
cd backend
python -m api.app

# 프론트엔드만 실행
cd frontend
npm install
npm start
```

### 3. Windows 배치 파일 사용
```cmd
# 백엔드 시작
start_backend.bat

# 프론트엔드 시작 (새 터미널에서)
start_frontend.bat
```

## 📋 Import 경로 변경사항

### 기존 → 새로운 경로
```python
# 기존
from config import config
from utils import allowed_file
from rag_service import get_rag_service
from preprocessing_agent import KoreanPreprocessingAgent
from dynamic_dictionary_manager import dictionary_manager

# 새로운 구조
from backend.config.config import config
from backend.utils.utils import allowed_file
from backend.services.rag_service import get_rag_service
from backend.preprocessing.preprocessing_agent import KoreanPreprocessingAgent
from backend.services.dynamic_dictionary_manager import dictionary_manager
```

## 🔧 설정 파일 경로

### 환경 변수
- **백엔드**: `backend/env.example` → `.env`로 복사하여 사용
- **프론트엔드**: `frontend/package.json`에서 설정

### 데이터베이스
- **ChromaDB**: `database/chroma.sqlite3`
- **딕셔너리**: `data/dictionaries/`
- **RAG 파일**: `data/rag_files/`

## 📊 성능 개선 효과

### 1. 모듈화 효과
- **코드 재사용성**: 기능별 모듈 분리로 재사용성 향상
- **유지보수성**: 명확한 구조로 유지보수 용이
- **테스트 용이성**: 각 모듈별 독립적 테스트 가능

### 2. 확장성
- **새로운 서비스 추가**: `services/` 폴더에 쉽게 추가
- **새로운 전처리 모듈**: `preprocessing/` 폴더에 추가
- **설정 관리**: `config/` 폴더로 중앙화된 설정 관리

### 3. 배포 개선
- **Docker 지원**: `docker/` 폴더로 컨테이너화 지원
- **환경 분리**: 개발/운영 환경 분리 용이
- **의존성 관리**: 각 모듈별 독립적 의존성 관리

## 🔄 마이그레이션 가이드

### 1. 기존 코드에서 새로운 구조로
```python
# 기존 app.py에서 import 수정
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.config.config import config
from backend.utils.utils import allowed_file
# ... 기타 import 수정
```

### 2. 파일 경로 수정
```python
# 기존 상대 경로 → 새로운 절대 경로
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rag_files')
USER_METADATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'metadata')
```

### 3. 실행 스크립트 수정
```bash
# 기존
python app.py

# 새로운 구조
python main.py
# 또는
cd backend && python -m api.app
```

## 📝 다음 단계

### 1. 테스트 및 검증
- [ ] 모든 API 엔드포인트 테스트
- [ ] 전처리 모듈 기능 검증
- [ ] RAG 서비스 동작 확인
- [ ] 딕셔너리 관리 기능 테스트

### 2. 성능 최적화
- [ ] 모듈별 성능 프로파일링
- [ ] 메모리 사용량 최적화
- [ ] 응답 시간 개선

### 3. 추가 기능 개발
- [ ] 로깅 시스템 개선
- [ ] 에러 핸들링 강화
- [ ] 모니터링 도구 추가

이 새로운 구조는 프로젝트의 확장성과 유지보수성을 크게 향상시킬 것입니다. 