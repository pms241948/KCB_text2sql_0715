from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import openai
import requests
import glob
import pandas as pd
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
except ImportError:
    openai_client = None  # 구버전 호환
from werkzeug.utils import secure_filename

# 설정 및 유틸리티 import
from config.config import config
from utils.utils import (
    allowed_file, get_file_info, generate_sample_data, parse_user_metadata,
    call_local_llm, convert_question_to_sql_rule_based, create_directories
)

# RAG 서비스 import
from services.rag_service import get_rag_service

# 한국어 전처리 에이전트 import (hybrid 방식 사용)
try:
    from preprocessing.hybrid_preprocessing_agent import hybrid_agent
    korean_preprocessing_agent = hybrid_agent
    KOREAN_PREPROCESSING_AVAILABLE = True
    print("✅ 한국어 전처리 에이전트(혼합 방식) 로드 성공")
except ImportError as e:
    print(f"❌ 한국어 전처리 에이전트 로드 실패: {e}")
    korean_preprocessing_agent = None
    KOREAN_PREPROCESSING_AVAILABLE = False



# 동적 딕셔너리 관리자 import
try:
    from services.dynamic_dictionary_manager import dictionary_manager
    DICTIONARY_MANAGER_AVAILABLE = True
    print("✅ 동적 딕셔너리 관리자 로드 성공")
except ImportError as e:
    print(f"❌ 동적 딕셔너리 관리자 로드 실패: {e}")
    dictionary_manager = None
    DICTIONARY_MANAGER_AVAILABLE = False


app = Flask(__name__)
CORS(app)

# LLM 설정
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
LLM_BASE_URL = os.getenv('LLM_BASE_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

# OpenAI API 설정 (기본값)
# openai.api_key = os.getenv('OPENAI_API_KEY') # 이제 openai_client 사용
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# RAG 파일 업로드 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rag_files')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'csv', 'json', 'md'}

# 도메인별 폴더 구조
RAG_DOMAINS = {
    'personal_credit': '개인 신용정보',
    'corporate_credit': '기업 신용정보',
    'policy_regulation': '평가 정책 및 규제'
}

# 업로드 폴더 생성
for domain in RAG_DOMAINS.keys():
    domain_path = os.path.join(UPLOAD_FOLDER, domain)
    os.makedirs(domain_path, exist_ok=True)

# 사용자 업로드 메타데이터 저장 경로
USER_METADATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'metadata')
ACTIVE_META_FILE = os.path.join(USER_METADATA_DIR, 'active.txt')

# 폴더 생성 보장
os.makedirs(USER_METADATA_DIR, exist_ok=True)

def allowed_file(filename):
    """허용된 파일 확장자인지 확인"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filepath):
    """파일 정보를 반환"""
    stat = os.stat(filepath)
    return {
        'filename': os.path.basename(filepath),
        'size': stat.st_size,
        'upload_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'path': filepath
    }

# 고객 메타데이터 (신용평가용)
CUSTOMER_METADATA = {
    "tables": {
        "customers": {
            "description": "고객 기본 정보 테이블",
            "columns": {
                "customer_id": {"type": "INTEGER", "description": "고객 고유 ID"},
                "name": {"type": "VARCHAR(100)", "description": "고객 이름"},
                "age": {"type": "INTEGER", "description": "고객 나이"},
                "gender": {"type": "VARCHAR(10)", "description": "성별 (M/F)"},
                "email": {"type": "VARCHAR(100)", "description": "이메일 주소"},
                "phone": {"type": "VARCHAR(20)", "description": "전화번호"},
                "address": {"type": "TEXT", "description": "주소"},
                "registration_date": {"type": "DATE", "description": "가입일"},
                "occupation": {"type": "VARCHAR(50)", "description": "직업"},
                "income_level": {"type": "VARCHAR(20)", "description": "소득 수준 (LOW/MEDIUM/HIGH)"}
            }
        },
        "credit_scores": {
            "description": "고객 신용점수 정보",
            "columns": {
                "customer_id": {"type": "INTEGER", "description": "고객 고유 ID (customers 테이블 참조)"},
                "credit_score": {"type": "INTEGER", "description": "신용점수 (300-850)"},
                "score_date": {"type": "DATE", "description": "점수 평가일"},
                "credit_bureau": {"type": "VARCHAR(50)", "description": "신용평가기관"},
                "risk_level": {"type": "VARCHAR(20)", "description": "위험도 (LOW/MEDIUM/HIGH)"}
            }
        },
        "loan_history": {
            "description": "대출 이력 정보",
            "columns": {
                "loan_id": {"type": "INTEGER", "description": "대출 고유 ID"},
                "customer_id": {"type": "INTEGER", "description": "고객 고유 ID (customers 테이블 참조)"},
                "loan_amount": {"type": "DECIMAL(15,2)", "description": "대출 금액"},
                "loan_type": {"type": "VARCHAR(50)", "description": "대출 유형 (MORTGAGE/PERSONAL/BUSINESS)"},
                "interest_rate": {"type": "DECIMAL(5,2)", "description": "이자율 (%)"},
                "loan_date": {"type": "DATE", "description": "대출 시작일"},
                "due_date": {"type": "DATE", "description": "만기일"},
                "status": {"type": "VARCHAR(20)", "description": "상태 (ACTIVE/PAID/DEFAULTED)"},
                "monthly_payment": {"type": "DECIMAL(10,2)", "description": "월 상환액"}
            }
        },
        "payment_history": {
            "description": "결제 이력 정보",
            "columns": {
                "payment_id": {"type": "INTEGER", "description": "결제 고유 ID"},
                "loan_id": {"type": "INTEGER", "description": "대출 ID (loan_history 테이블 참조)"},
                "payment_date": {"type": "DATE", "description": "결제일"},
                "payment_amount": {"type": "DECIMAL(10,2)", "description": "결제 금액"},
                "payment_type": {"type": "VARCHAR(20)", "description": "결제 유형 (ON_TIME/LATE/DEFAULT)"},
                "days_late": {"type": "INTEGER", "description": "연체 일수"}
            }
        },
        "employment_history": {
            "description": "고용 이력 정보",
            "columns": {
                "employment_id": {"type": "INTEGER", "description": "고용 이력 ID"},
                "customer_id": {"type": "INTEGER", "description": "고객 고유 ID (customers 테이블 참조)"},
                "company_name": {"type": "VARCHAR(100)", "description": "회사명"},
                "position": {"type": "VARCHAR(50)", "description": "직책"},
                "start_date": {"type": "DATE", "description": "입사일"},
                "end_date": {"type": "DATE", "description": "퇴사일 (NULL이면 재직중)"},
                "salary": {"type": "DECIMAL(12,2)", "description": "연봉"},
                "employment_type": {"type": "VARCHAR(20)", "description": "고용 형태 (FULL_TIME/PART_TIME/CONTRACT)"}
            }
        }
    }
}

# 샘플 데이터 생성
def generate_sample_data():
    sample_data = {
        "customers": [
            {"customer_id": 1, "name": "김철수", "age": 35, "gender": "M", "email": "kim@email.com", "phone": "010-1234-5678", "address": "서울시 강남구", "registration_date": "2020-01-15", "occupation": "엔지니어", "income_level": "HIGH"},
            {"customer_id": 2, "name": "이영희", "age": 28, "gender": "F", "email": "lee@email.com", "phone": "010-2345-6789", "address": "서울시 서초구", "registration_date": "2019-06-20", "occupation": "디자이너", "income_level": "MEDIUM"},
            {"customer_id": 3, "name": "박민수", "age": 42, "gender": "M", "email": "park@email.com", "phone": "010-3456-7890", "address": "부산시 해운대구", "registration_date": "2018-11-10", "occupation": "매니저", "income_level": "HIGH"},
            {"customer_id": 4, "name": "최지영", "age": 31, "gender": "F", "email": "choi@email.com", "phone": "010-4567-8901", "address": "대구시 수성구", "registration_date": "2021-03-05", "occupation": "교사", "income_level": "MEDIUM"},
            {"customer_id": 5, "name": "정현우", "age": 39, "gender": "M", "email": "jung@email.com", "phone": "010-5678-9012", "address": "인천시 연수구", "registration_date": "2017-09-12", "occupation": "의사", "income_level": "HIGH"}
        ],
        "credit_scores": [
            {"customer_id": 1, "credit_score": 750, "score_date": "2023-12-01", "credit_bureau": "NICE", "risk_level": "LOW"},
            {"customer_id": 2, "credit_score": 680, "score_date": "2023-12-01", "credit_bureau": "NICE", "risk_level": "MEDIUM"},
            {"customer_id": 3, "credit_score": 720, "score_date": "2023-12-01", "credit_bureau": "NICE", "risk_level": "LOW"},
            {"customer_id": 4, "credit_score": 620, "score_date": "2023-12-01", "credit_bureau": "NICE", "risk_level": "MEDIUM"},
            {"customer_id": 5, "credit_score": 800, "score_date": "2023-12-01", "credit_bureau": "NICE", "risk_level": "LOW"}
        ]
    }
    return sample_data

# 엑셀 메타데이터 파싱 함수

def parse_user_metadata():
    """업로드된 엑셀 파일을 파싱하여 메타데이터 dict로 변환"""
    if not os.path.exists(ACTIVE_META_FILE):
        return None
    try:
        with open(ACTIVE_META_FILE, 'r', encoding='utf-8') as f:
            filename = f.read().strip()
        path = os.path.join(USER_METADATA_DIR, filename)
        if not os.path.exists(path):
            return None
        df = pd.read_excel(path)
        # 기대 포맷: 테이블명, 컬럼명, 타입, 설명
        meta = {"tables": {}}
        for _, row in df.iterrows():
            table = str(row["테이블명"]).strip()
            col = str(row["컬럼명"]).strip()
            typ = str(row["타입"]).strip()
            desc = str(row["설명"]).strip() if "설명" in row else ""
            if table not in meta["tables"]:
                meta["tables"][table] = {"description": "", "columns": {}}
            meta["tables"][table]["columns"][col] = {"type": typ, "description": desc}
        return meta
    except Exception as e:
        print(f"엑셀 메타데이터 파싱 오류: {e}")
        return None

# get_metadata 엔드포인트 수정: 사용자 메타데이터 우선 반환
@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """데이터베이스 메타데이터를 반환합니다. (사용자 업로드 우선)"""
    try:
        user_meta = parse_user_metadata()
        if user_meta:
            print(f"사용자 메타데이터 반환: {len(user_meta.get('tables', {}))}개 테이블")
            return jsonify(user_meta)
        else:
            print("기본 메타데이터 반환")
            return jsonify(CUSTOMER_METADATA)
    except Exception as e:
        print(f"메타데이터 조회 오류: {e}")
        return jsonify(CUSTOMER_METADATA)

@app.route('/api/sample-data', methods=['GET'])
def get_sample_data():
    """샘플 데이터를 반환합니다."""
    return jsonify(generate_sample_data())

# 업로드 시 파일명 중복 방지 및 저장
@app.route('/api/metadata/upload', methods=['POST'])
def upload_metadata():
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.xlsx'):
        return jsonify({"error": "엑셀(xlsx) 파일만 업로드 가능합니다."}), 400
    try:
        # 파일명 중복 방지(타임스탬프)
        base = os.path.splitext(secure_filename(file.filename))[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_name = f"{base}_{timestamp}.xlsx"
        save_path = os.path.join(USER_METADATA_DIR, save_name)
        file.save(save_path)
        print(f"메타데이터 파일 저장됨: {save_path}")
        
        # 업로드 시 자동 적용
        with open(ACTIVE_META_FILE, 'w', encoding='utf-8') as f:
            f.write(save_name)
        print(f"활성 메타데이터 파일 설정됨: {save_name}")
        
        # 파싱 테스트
        parsed_meta = parse_user_metadata()
        if parsed_meta:
            print(f"메타데이터 파싱 성공: {len(parsed_meta.get('tables', {}))}개 테이블")
        else:
            print("메타데이터 파싱 실패")
            
        return jsonify({"message": "메타데이터 파일이 업로드 및 적용되었습니다.", "filename": save_name})
    except Exception as e:
        print(f"메타데이터 업로드 오류: {e}")
        return jsonify({"error": str(e)}), 500

# 메타데이터 파일 목록 조회
@app.route('/api/metadata/list', methods=['GET'])
def list_metadata():
    files = []
    for path in glob.glob(os.path.join(USER_METADATA_DIR, '*.xlsx')):
        stat = os.stat(path)
        files.append({
            'filename': os.path.basename(path),
            'size': stat.st_size,
            'upload_date': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    # 현재 적용중인 파일
    active = None
    if os.path.exists(ACTIVE_META_FILE):
        with open(ACTIVE_META_FILE, 'r', encoding='utf-8') as f:
            active = f.read().strip()
    return jsonify({'files': files, 'active': active})

# 메타데이터 파일 적용
@app.route('/api/metadata/apply', methods=['POST'])
def apply_metadata():
    data = request.get_json()
    filename = data.get('filename')
    path = os.path.join(USER_METADATA_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "파일이 존재하지 않습니다."}), 404
    with open(ACTIVE_META_FILE, 'w', encoding='utf-8') as f:
        f.write(filename)
    return jsonify({"message": "적용 완료", "filename": filename})

# 메타데이터 파일 삭제
@app.route('/api/metadata/delete/<filename>', methods=['DELETE'])
def delete_metadata(filename):
    path = os.path.join(USER_METADATA_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "파일이 존재하지 않습니다."}), 404
    try:
        os.remove(path)
        # 삭제한 파일이 active면 active 해제
        if os.path.exists(ACTIVE_META_FILE):
            with open(ACTIVE_META_FILE, 'r', encoding='utf-8') as f:
                active = f.read().strip()
            if active == filename:
                os.remove(ACTIVE_META_FILE)
        return jsonify({"message": "삭제 완료"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# convert_question_to_sql에서 메타데이터를 동적으로 사용하도록 수정
@app.route('/api/convert', methods=['POST'])
def convert_to_sql():
    """자연어 질문을 SQL로 변환합니다. (RAG 문서, 사용자 메타데이터 활용)"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        rag_domain = data.get('rag_domain', None)
        if not question:
            return jsonify({"error": "질문이 필요합니다."}), 400
        
        # 새로운 RAG 서비스를 사용하여 관련 문서 검색
        rag_context = rag_service.get_rag_context(question, rag_domain, top_k=5)
        
        # 메타데이터 동적 로딩
        user_meta = parse_user_metadata()
        meta = user_meta if user_meta else CUSTOMER_METADATA
        sql_query = convert_question_to_sql(question, rag_context, meta)
        
        # 전처리 에이전트 정보 추가 (혼합 방식 우선)
        preprocessing_info = {}
        
        # 혼합 전처리 에이전트 사용 (우선)
        if KOREAN_PREPROCESSING_AVAILABLE and korean_preprocessing_agent:
            try:
                preprocessed = korean_preprocessing_agent.preprocess_query(question)
                preprocessing_info = {
                    "agent_type": "hybrid",
                    "available": True,
                    "original_query": preprocessed["original_query"],
                    "normalized_query": preprocessed["normalized_query"],
                    "mapped_query": preprocessed["mapped_query"],
                    "entities": preprocessed["entities"],
                    "clauses": preprocessed["clauses"],
                    "reasoning_chain": preprocessed["reasoning_chain"],
                    "sql_mappings": preprocessed["sql_mappings"],
                    "preprocessing_metadata": preprocessed["preprocessing_metadata"],
                    "domain_terms_found": preprocessed["preprocessing_metadata"]["domain_terms_found"],
                    "clauses_count": preprocessed["preprocessing_metadata"]["clauses_count"],
                    "reasoning_steps": preprocessed["preprocessing_metadata"]["reasoning_steps"],
                    "sql_patterns_mapped": preprocessed["preprocessing_metadata"]["sql_patterns_mapped"]
                }
                print(f"🔧 혼합 전처리 에이전트 사용 - 도메인 용어: {preprocessed['preprocessing_metadata']['domain_terms_found']}개")
                print(f"📋 절(Clause): {preprocessed['preprocessing_metadata']['clauses_count']}개")
                
            except Exception as e:
                preprocessing_info = {
                    "agent_type": "hybrid",
                    "available": True,
                    "error": str(e)
                }
        
        # 기존 한국어 전처리 에이전트 사용 (fallback)
        elif KOREAN_PREPROCESSING_AVAILABLE and korean_preprocessing_agent:
            try:
                preprocessed = korean_preprocessing_agent.preprocess_query(question)
                preprocessing_info = {
                    "agent_type": "korean",
                    "available": True,
                    "clauses_count": len(preprocessed.clauses),
                    "sql_keywords": preprocessed.sql_keywords,
                    "entities_count": len(preprocessed.entities),
                    "normalized_query": preprocessed.normalized_query,
                    "clause_types": korean_preprocessing_agent.get_clause_summary(preprocessed)["clause_types"]
                }
            except Exception as e:
                preprocessing_info = {
                    "agent_type": "korean",
                    "available": True,
                    "error": str(e)
                }
        else:
            preprocessing_info = {
                "agent_type": "none",
                "available": False,
                "reason": "전처리 에이전트를 사용할 수 없습니다."
            }
        
        return jsonify({
            "question": question,
            "sql": sql_query,
            "timestamp": datetime.now().isoformat(),
            "rag_context_used": bool(rag_context),  # RAG 컨텍스트 사용 여부
            "preprocessing": preprocessing_info
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# RAG 서비스 초기화
rag_service = get_rag_service()

# 기존 문서들을 벡터 DB에 처리 (최초 1회만 실행)
def initialize_rag_database():
    """기존 RAG 문서들을 벡터 데이터베이스에 처리"""
    try:
        # 기존 문서 처리
        results = rag_service.process_all_existing_documents()
        print(f"RAG 데이터베이스 초기화 완료: {len(results)}개 문서 처리됨")
        return results
    except Exception as e:
        print(f"RAG 데이터베이스 초기화 실패: {e}")
        return []

# 앱 시작 시 RAG DB 초기화 (수동으로 실행하려면 주석 처리)
# initialize_rag_database()

# convert_question_to_sql 함수 시그니처 및 내부 수정

def call_local_llm(prompt, system_prompt="당신은 자연어를 SQL로 변환하는 전문가입니다."):
    """로컬 LLM API 호출 함수"""
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        if LLM_API_KEY:
            headers['Authorization'] = f'Bearer {LLM_API_KEY}'
        
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{LLM_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"로컬 LLM API 오류: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"로컬 LLM 호출 중 오류: {e}")
        return None

def convert_question_to_sql(question, rag_context=None, meta=None):
    """자연어 질문을 SQL로 변환하는 함수 (한국어 전처리 에이전트 + RAG context + 동적 메타데이터 활용)"""
    
    # 한국어 전처리 에이전트 사용 (가능한 경우)
    enhanced_prompt = None
    preprocessing_info = {}
    
    if KOREAN_PREPROCESSING_AVAILABLE and korean_preprocessing_agent:
        try:
            # 전처리 수행
            preprocessed = korean_preprocessing_agent.preprocess_query(question)
            
            # 향상된 프롬프트 생성
            enhanced_prompt = korean_preprocessing_agent.generate_enhanced_prompt(preprocessed)
            
            # 전처리 정보 저장
            preprocessing_info = {
                "clauses_count": len(preprocessed.clauses),
                "sql_keywords": preprocessed.sql_keywords,
                "entities_count": len(preprocessed.entities),
                "normalized_query": preprocessed.normalized_query
            }
            
            print(f"🇰🇷 한국어 전처리 에이전트 사용 - 추출된 절: {len(preprocessed.clauses)}개")
            print(f"🔑 SQL 키워드: {preprocessed.sql_keywords}")
            
        except Exception as e:
            print(f"❌ 한국어 전처리 에이전트 오류: {e}")
            enhanced_prompt = None
    
    # 로컬 LLM 사용 시
    if LLM_PROVIDER in ['ollama', 'enterprise'] and LLM_BASE_URL:
        try:
            # 메타데이터를 프롬프트용 텍스트로 변환
            if meta is None:
                meta = CUSTOMER_METADATA
            schema_info = "데이터베이스 스키마:\n"
            for tname, tinfo in meta["tables"].items():
                schema_info += f"- {tname} 테이블: "
                schema_info += ", ".join([f"{col}({cinfo['type']})" for col, cinfo in tinfo["columns"].items()]) + "\n"
            
            # 전처리된 프롬프트 사용 또는 기본 프롬프트 사용
            if enhanced_prompt:
                prompt = f"{schema_info}\n{enhanced_prompt}"
            else:
                prompt = f"{schema_info}\n"
                if rag_context:
                    prompt += f"[참고 문서]\n{rag_context}\n"
                prompt += (
                    f"다음 자연어 질문을 SQL 쿼리로 변환해주세요.\n"
                    f"질문: {question}\n\n"
                    "요구사항:\n"
                    "1. SQL만 출력하고 다른 설명은 하지 마세요\n"
                    "2. 적절한 JOIN을 사용하세요\n"
                    "3. WHERE 조건을 명확히 하세요\n"
                    "4. ORDER BY, GROUP BY, LIMIT 등을 적절히 사용하세요\n"
                    "5. 컬럼명은 정확히 사용하세요\n"
                )
            
            sql_query = call_local_llm(prompt)
            if sql_query and any(keyword in sql_query.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN']):
                return sql_query
            else:
                return convert_question_to_sql_rule_based(question)
                
        except Exception as e:
            print(f"로컬 LLM 변환 오류: {e}")
            return convert_question_to_sql_rule_based(question)
    
    # OpenAI API 사용 시
    if not os.getenv('OPENAI_API_KEY') or not openai_client:
        return convert_question_to_sql_rule_based(question)
    try:
        # 메타데이터를 프롬프트용 텍스트로 변환
        if meta is None:
            meta = CUSTOMER_METADATA
        schema_info = "데이터베이스 스키마:\n"
        for tname, tinfo in meta["tables"].items():
            schema_info += f"- {tname} 테이블: "
            schema_info += ", ".join([f"{col}({cinfo['type']})" for col, cinfo in tinfo["columns"].items()]) + "\n"
        
        # 전처리된 프롬프트 사용 또는 기본 프롬프트 사용
        if enhanced_prompt:
            prompt = f"{schema_info}\n{enhanced_prompt}"
        else:
            prompt = f"{schema_info}\n"
            if rag_context:
                prompt += f"[참고 문서]\n{rag_context}\n"
            prompt += (
                f"다음 자연어 질문을 SQL 쿼리로 변환해주세요.\n"
                f"질문: {question}\n\n"
                "요구사항:\n"
                "1. SQL만 출력하고 다른 설명은 하지 마세요\n"
                "2. 적절한 JOIN을 사용하세요\n"
                "3. WHERE 조건을 명확히 하세요\n"
                "4. ORDER BY, GROUP BY, LIMIT 등을 적절히 사용하세요\n"
                "5. 컬럼명은 정확히 사용하세요\n"
            )
        
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "당신은 자연어를 SQL로 변환하는 전문가입니다. 주어진 데이터베이스 스키마와 참고 문서를 기반으로 정확한 SQL 쿼리를 생성합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        sql_query = response.choices[0].message.content.strip()
        if any(keyword in sql_query.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN']):
            return sql_query
        else:
            return convert_question_to_sql_rule_based(question)
    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        return convert_question_to_sql_rule_based(question)

def convert_question_to_sql_rule_based(question):
    """규칙 기반 SQL 변환 (폴백용)"""
    question_lower = question.lower()

    # 기본적인 패턴 매칭을 통한 SQL 생성
    if "고객" in question and "목록" in question:
        return "SELECT * FROM customers;"

    elif "신용점수" in question and "높은" in question:
        return "SELECT c.name, cs.credit_score FROM customers c JOIN credit_scores cs ON c.customer_id = cs.customer_id ORDER BY cs.credit_score DESC;"

    elif "신용점수" in question and "낮은" in question:
        return "SELECT c.name, cs.credit_score FROM customers c JOIN credit_scores cs ON c.customer_id = cs.customer_id ORDER BY cs.credit_score ASC;"

    elif "나이" in question and "평균" in question:
        return "SELECT AVG(age) as average_age FROM customers;"

    elif "성별" in question and "분포" in question:
        return "SELECT gender, COUNT(*) as count FROM customers GROUP BY gender;"

    elif "소득" in question and "수준" in question:
        return "SELECT income_level, COUNT(*) as count FROM customers GROUP BY income_level;"

    elif "위험도" in question:
        return "SELECT cs.risk_level, COUNT(*) as count FROM credit_scores cs GROUP BY cs.risk_level;"

    elif "고객" in question and "수" in question:
        return "SELECT COUNT(*) as total_customers FROM customers;"

    elif "신용점수" in question and "평균" in question:
        return "SELECT AVG(credit_score) as average_credit_score FROM credit_scores;"

    elif "직업" in question and "별" in question:
        return "SELECT occupation, COUNT(*) as count FROM customers GROUP BY occupation;"

    elif "가입일" in question and "최근" in question:
        return "SELECT name, registration_date FROM customers ORDER BY registration_date DESC LIMIT 5;"

    else:
        # 기본 쿼리
        return "SELECT * FROM customers LIMIT 10;"

# RAG 파일 관리 API 엔드포인트들

@app.route('/api/rag/domains', methods=['GET'])
def get_rag_domains():
    """RAG 도메인 목록을 반환합니다."""
    return jsonify({
        'domains': RAG_DOMAINS,
        'allowed_extensions': list(ALLOWED_EXTENSIONS)
    })

@app.route('/api/rag/files/<domain>', methods=['GET'])
def get_rag_files(domain):
    """특정 도메인의 RAG 파일 목록을 반환합니다."""
    if domain not in RAG_DOMAINS:
        return jsonify({"error": "유효하지 않은 도메인입니다."}), 400
    
    domain_path = os.path.join(UPLOAD_FOLDER, domain)
    files = []
    
    if os.path.exists(domain_path):
        for filename in os.listdir(domain_path):
            filepath = os.path.join(domain_path, filename)
            if os.path.isfile(filepath):
                files.append(get_file_info(filepath))
    
    return jsonify({
        'domain': domain,
        'domain_name': RAG_DOMAINS[domain],
        'files': files
    })

@app.route('/api/rag/upload/<domain>', methods=['POST'])
def upload_rag_file(domain):
    """특정 도메인에 RAG 파일을 업로드합니다."""
    if domain not in RAG_DOMAINS:
        return jsonify({"error": "유효하지 않은 도메인입니다."}), 400
    
    if 'file' not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "파일이 선택되지 않았습니다."}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "허용되지 않는 파일 형식입니다."}), 400
    
    try:
        filename = secure_filename(file.filename)
        domain_path = os.path.join(UPLOAD_FOLDER, domain)
        
        # 중복 파일명 처리
        base_name, extension = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(domain_path, filename)):
            filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        filepath = os.path.join(domain_path, filename)
        file.save(filepath)
        
        # 새로운 RAG 서비스를 사용하여 문서 처리
        result = rag_service.process_document(filepath, domain, filename)
        
        if result['success']:
            return jsonify({
                'message': '파일이 성공적으로 업로드되고 벡터 데이터베이스에 처리되었습니다.',
                'file': get_file_info(filepath),
                'rag_processing': result
            })
        else:
            return jsonify({
                'message': '파일은 업로드되었지만 벡터 데이터베이스 처리에 실패했습니다.',
                'file': get_file_info(filepath),
                'rag_error': result['error']
            })
        
    except Exception as e:
        return jsonify({"error": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/rag/delete/<domain>/<filename>', methods=['DELETE'])
def delete_rag_file(domain, filename):
    """특정 도메인에서 RAG 파일을 삭제합니다."""
    if domain not in RAG_DOMAINS:
        return jsonify({"error": "유효하지 않은 도메인입니다."}), 400
    
    try:
        filepath = os.path.join(UPLOAD_FOLDER, domain, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
        
        # 새로운 RAG 서비스를 사용하여 벡터 DB에서도 삭제
        rag_result = rag_service.delete_document(domain, filename)
        
        # 파일 시스템에서 삭제
        os.remove(filepath)
        
        if rag_result['success']:
            return jsonify({
                'message': '파일이 성공적으로 삭제되었습니다.',
                'filename': filename,
                'rag_deletion': '성공'
            })
        else:
            return jsonify({
                'message': '파일은 삭제되었지만 벡터 데이터베이스에서 삭제에 실패했습니다.',
                'filename': filename,
                'rag_error': rag_result['error']
            })
        
    except Exception as e:
        return jsonify({"error": f"파일 삭제 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/rag/download/<domain>/<filename>', methods=['GET'])
def download_rag_file(domain, filename):
    """특정 도메인에서 RAG 파일을 다운로드합니다."""
    if domain not in RAG_DOMAINS:
        return jsonify({"error": "유효하지 않은 도메인입니다."}), 400
    
    try:
        filepath = os.path.join(UPLOAD_FOLDER, domain, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
        
        # 파일 내용을 읽어서 반환 (실제로는 send_file을 사용하는 것이 좋음)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'filename': filename,
            'content': content,
            'file_info': get_file_info(filepath)
        })
        
    except Exception as e:
        return jsonify({"error": f"파일 다운로드 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/rag/stats', methods=['GET'])
def get_rag_stats():
    """RAG 데이터베이스 통계 정보를 반환합니다."""
    try:
        domain = request.args.get('domain', None)
        stats = rag_service.get_document_stats(domain)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": f"통계 조회 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/rag/search', methods=['POST'])
def search_rag_documents():
    """RAG 문서에서 관련 청크를 검색합니다."""
    try:
        data = request.get_json()
        question = data.get('question', '')
        domain = data.get('domain', None)
        top_k = data.get('top_k', 5)
        
        if not question:
            return jsonify({"error": "검색 질문이 필요합니다."}), 400
        
        chunks = rag_service.retrieve_relevant_chunks(question, domain, top_k)
        
        return jsonify({
            'question': question,
            'domain': domain,
            'chunks': chunks,
            'total_found': len(chunks)
        })
        
    except Exception as e:
        return jsonify({"error": f"검색 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    """채팅 히스토리를 반환합니다."""
    # 실제로는 데이터베이스에서 가져와야 함
    return jsonify([])

@app.route('/api/rag/initialize', methods=['POST'])
def initialize_rag_manually():
    """RAG 데이터베이스를 수동으로 초기화합니다."""
    try:
        results = initialize_rag_database()
        return jsonify({
            "success": True,
            "message": f"RAG 데이터베이스 초기화 완료: {len(results)}개 문서 처리됨",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/preprocessing/status', methods=['GET'])
def get_preprocessing_status():
    """전처리 에이전트 상태 확인 API"""
    return jsonify({
        "korean_preprocessing_available": KOREAN_PREPROCESSING_AVAILABLE,
        "agent_loaded": korean_preprocessing_agent is not None,
        "domain_context": korean_preprocessing_agent.domain_context if korean_preprocessing_agent else None
    })

@app.route('/api/preprocessing/test', methods=['POST'])
def test_preprocessing():
    """전처리 에이전트 테스트 API (혼합 방식 우선)"""
    try:
        data = request.get_json()
        test_query = data.get('query', '')
        
        if not test_query:
            return jsonify({"error": "테스트 쿼리가 제공되지 않았습니다."}), 400
        
        result = {}
        
        # 혼합 전처리 에이전트 테스트 (우선)
        if KOREAN_PREPROCESSING_AVAILABLE and korean_preprocessing_agent:
            try:
                preprocessed = korean_preprocessing_agent.preprocess_query(test_query)
                result["hybrid_preprocessing"] = {
                    "available": True,
                    "original_query": preprocessed["original_query"],
                    "normalized_query": preprocessed["normalized_query"],
                    "mapped_query": preprocessed["mapped_query"],
                    "entities": preprocessed["entities"],
                    "clauses": preprocessed["clauses"],
                    "reasoning_chain": preprocessed["reasoning_chain"],
                    "sql_mappings": preprocessed["sql_mappings"],
                    "preprocessing_metadata": preprocessed["preprocessing_metadata"],
                    "domain_terms_found": preprocessed["preprocessing_metadata"]["domain_terms_found"],
                    "clauses_count": preprocessed["preprocessing_metadata"]["clauses_count"],
                    "reasoning_steps": preprocessed["preprocessing_metadata"]["reasoning_steps"],
                    "sql_patterns_mapped": preprocessed["preprocessing_metadata"]["sql_patterns_mapped"]
                }
            except Exception as e:
                result["hybrid_preprocessing"] = {
                    "available": True,
                    "error": str(e)
                }
        else:
            result["hybrid_preprocessing"] = {
                "available": False,
                "reason": "혼합 전처리 에이전트를 사용할 수 없습니다."
            }
        
        # 한국어 전처리 에이전트 테스트 (fallback)
        if KOREAN_PREPROCESSING_AVAILABLE and korean_preprocessing_agent:
            try:
                preprocessed = korean_preprocessing_agent.preprocess_query(test_query)
                result["korean_preprocessing"] = {
                    "available": True,
                    "original_query": preprocessed.original_query,
                    "normalized_query": preprocessed.normalized_query,
                    "clauses": [
                        {
                            "type": clause.type.value,
                            "content": clause.content,
                            "confidence": clause.confidence
                        } for clause in preprocessed.clauses
                    ],
                    "sql_keywords": preprocessed.sql_keywords,
                    "entities": preprocessed.entities,
                    "reasoning_steps": preprocessed.reasoning_steps,
                    "summary": korean_preprocessing_agent.get_clause_summary(preprocessed)
                }
            except Exception as e:
                result["korean_preprocessing"] = {
                    "available": True,
                    "error": str(e)
                }
        else:
            result["korean_preprocessing"] = {
                "available": False,
                "reason": "한국어 전처리 에이전트를 사용할 수 없습니다."
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 딕셔너리 관리 API 엔드포인트들
@app.route('/api/dictionary/status', methods=['GET'])
def get_dictionary_status():
    """딕셔너리 상태 확인 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({
            "available": False,
            "reason": "동적 딕셔너리 관리자를 사용할 수 없습니다."
        })
    
    stats = dictionary_manager.get_dictionary_stats()
    return jsonify({
        "available": True,
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/dictionary/reload', methods=['POST'])
def reload_dictionaries():
    """딕셔너리 재로드 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        result = dictionary_manager.reload_dictionaries()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/backup', methods=['POST'])
def backup_dictionaries():
    """딕셔너리 백업 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        result = dictionary_manager.backup_dictionaries()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/terms', methods=['GET'])
def get_credit_terms():
    """신용평가 도메인 용어 조회 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        return jsonify({
            "credit_terms": dictionary_manager.credit_terms,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/terms/search', methods=['POST'])
def search_credit_terms():
    """신용평가 도메인 용어 검색 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "검색어가 필요합니다."}), 400
        
        results = dictionary_manager.search_terms(query)
        return jsonify({
            "query": query,
            "results": results,
            "total_found": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/terms', methods=['POST'])
def add_credit_term():
    """신용평가 도메인 용어 추가 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        category = data.get('category', '')
        term = data.get('term', '')
        info = data.get('info', {})
        
        if not category or not term or not info:
            return jsonify({"error": "카테고리, 용어, 정보가 모두 필요합니다."}), 400
        
        result = dictionary_manager.add_credit_term(category, term, info)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/terms/<category>/<term>', methods=['PUT'])
def update_credit_term(category, term):
    """신용평가 도메인 용어 수정 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        info = data.get('info', {})
        
        if not info:
            return jsonify({"error": "수정할 정보가 필요합니다."}), 400
        
        result = dictionary_manager.update_credit_term(category, term, info)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/terms/<category>/<term>', methods=['DELETE'])
def delete_credit_term(category, term):
    """신용평가 도메인 용어 삭제 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        result = dictionary_manager.delete_credit_term(category, term)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/sql-patterns', methods=['GET'])
def get_sql_patterns():
    """SQL 패턴 조회 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        return jsonify({
            "sql_patterns": dictionary_manager.sql_patterns,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/sql-patterns', methods=['POST'])
def add_sql_pattern():
    """SQL 패턴 추가 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        category = data.get('category', '')
        korean = data.get('korean', '')
        sql = data.get('sql', '')
        
        if not category or not korean or not sql:
            return jsonify({"error": "카테고리, 한국어, SQL이 모두 필요합니다."}), 400
        
        result = dictionary_manager.add_sql_pattern(category, korean, sql)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/sql-patterns/<category>/<korean>', methods=['PUT'])
def update_sql_pattern(category, korean):
    """SQL 패턴 수정 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        sql = data.get('sql', '')
        
        if not sql:
            return jsonify({"error": "수정할 SQL이 필요합니다."}), 400
        
        result = dictionary_manager.update_sql_pattern(category, korean, sql)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/sql-patterns/<category>/<korean>', methods=['DELETE'])
def delete_sql_pattern(category, korean):
    """SQL 패턴 삭제 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        result = dictionary_manager.delete_sql_pattern(category, korean)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/export', methods=['GET'])
def export_dictionary():
    """딕셔너리 내보내기 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        format_type = request.args.get('format', 'json')
        result = dictionary_manager.export_dictionary(format_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dictionary/import', methods=['POST'])
def import_dictionary():
    """딕셔너리 가져오기 API"""
    if not DICTIONARY_MANAGER_AVAILABLE or not dictionary_manager:
        return jsonify({"error": "동적 딕셔너리 관리자를 사용할 수 없습니다."}), 400
    
    try:
        data = request.get_json()
        result = dictionary_manager.import_dictionary(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))
    app.run(debug=True, port=5000) 