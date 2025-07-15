#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유틸리티 함수 모듈
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config import config

def allowed_file(filename: str) -> bool:
    """허용된 파일 확장자인지 확인"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def get_file_info(filepath: str) -> Dict[str, Any]:
    """파일 정보를 반환"""
    stat = os.stat(filepath)
    return {
        'filename': os.path.basename(filepath),
        'size': stat.st_size,
        'upload_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'path': filepath
    }

def generate_sample_data() -> Dict[str, List[Dict]]:
    """샘플 데이터 생성"""
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

def parse_user_metadata() -> Dict[str, Any] | None:
    """업로드된 엑셀 파일을 파싱하여 메타데이터 dict로 변환"""
    if not os.path.exists(config.ACTIVE_META_FILE):
        return None
    
    try:
        with open(config.ACTIVE_META_FILE, 'r', encoding='utf-8') as f:
            filename = f.read().strip()
        
        path = os.path.join(config.USER_METADATA_DIR, filename)
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
        print(f"메타데이터 파싱 오류: {e}")
        return None

def call_local_llm(prompt: str, system_prompt: str = "당신은 자연어를 SQL로 변환하는 전문가입니다.") -> str | None:
    """로컬 LLM API 호출 함수"""
    try:
        import requests
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if config.LLM_API_KEY:
            headers['Authorization'] = f'Bearer {config.LLM_API_KEY}'
        
        payload = {
            "model": config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{config.LLM_BASE_URL}/v1/chat/completions",
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

def convert_question_to_sql_rule_based(question: str) -> str:
    """규칙 기반 SQL 변환 (폴백용)"""
    # 간단한 규칙 기반 변환
    question_lower = question.lower()
    
    if "고객" in question and "수" in question:
        return "SELECT COUNT(*) as customer_count FROM customers;"
    elif "신용점수" in question and "평균" in question:
        return "SELECT AVG(credit_score) as avg_credit_score FROM credit_scores;"
    elif "대출" in question and "합계" in question:
        return "SELECT SUM(loan_amount) as total_loan_amount FROM loan_history;"
    else:
        return "SELECT * FROM customers LIMIT 10;"

def create_directories():
    """필요한 디렉토리들을 생성"""
    directories = [
        config.UPLOAD_FOLDER,
        config.USER_METADATA_DIR,
        config.DICTIONARIES_DIR,
        os.path.join(config.DICTIONARIES_DIR, "backups"),
        config.CHROMADB_DIR
    ]
    
    # RAG 도메인별 디렉토리 생성
    for domain in config.RAG_DOMAINS.keys():
        directories.append(os.path.join(config.UPLOAD_FOLDER, domain))
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ 디렉토리 생성/확인: {directory}")

def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """JSON 데이터 구조 검증"""
    try:
        for key in required_keys:
            if key not in data:
                return False
        return True
    except Exception:
        return False

def safe_json_load(file_path: str) -> Dict[str, Any] | None:
    """안전한 JSON 파일 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON 파일 로드 오류 ({file_path}): {e}")
        return None

def safe_json_save(data: Dict[str, Any], file_path: str) -> bool:
    """안전한 JSON 파일 저장"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"JSON 파일 저장 오류 ({file_path}): {e}")
        return False 