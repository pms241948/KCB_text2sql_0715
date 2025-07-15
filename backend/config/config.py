#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 관리 모듈
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """애플리케이션 설정 클래스"""
    
    # Flask 설정
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # LLM 설정
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # RAG 설정
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'rag_files')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'csv', 'json', 'md'}
    
    # RAG 도메인 설정
    RAG_DOMAINS = {
        'personal_credit': '개인 신용정보',
        'corporate_credit': '기업 신용정보',
        'policy_regulation': '평가 정책 및 규제'
    }
    
    # 메타데이터 설정
    USER_METADATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'metadata')
    ACTIVE_META_FILE = os.path.join(USER_METADATA_DIR, 'active.txt')
    
    # 딕셔너리 설정
    DICTIONARIES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'dictionaries')
    
    # ChromaDB 설정
    CHROMADB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'chromadb')
    
    # 기본 메타데이터 (신용평가용)
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

# 전역 설정 인스턴스
config = Config() 