#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
규칙 기반 + 딕셔너리 혼합 전처리 에이전트
신용평가 도메인 특화 자연어 전처리
"""

import re
import jieba
from typing import Dict, List, Tuple, Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.dynamic_dictionary_manager import dictionary_manager

class HybridPreprocessingAgent:
    """규칙 기반 + 딕셔너리 혼합 전처리 에이전트"""
    
    def __init__(self):
        self.dict_manager = dictionary_manager
        self._init_processing_rules()
        self._init_sql_patterns()
        self._init_entity_extractors()
    
    def _init_processing_rules(self):
        """전처리 규칙 초기화"""
        self.processing_rules = {
            # 문장 정규화 규칙
            "normalization": {
                "whitespace": r'\s+',
                "punctuation": r'[^\w\s가-힣]',
                "numbers": r'(\d+)',
                "currency": r'(\d+)(원|달러|엔|위안)',
                "percentage": r'(\d+)%',
                "date_patterns": [
                    r'(\d{4})년(\d{1,2})월(\d{1,2})일',
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',
                    r'(\d{1,2})월(\d{1,2})일'
                ]
            },
            
            # 도메인 특화 패턴
            "domain_patterns": {
                "credit_score_range": r'신용점수\s*(\d+)\s*이상',
                "risk_level": r'위험도\s*(낮음|보통|높음)',
                "loan_amount": r'대출금액\s*(\d+)원',
                "overdue_days": r'연체일수\s*(\d+)일',
                "customer_type": r'(개인|기업|소상공인)고객',
                "vip_customer": r'VIP\s*고객',
                "managed_customer": r'관리\s*고객'
            },
            
            # 조건부 표현 패턴
            "conditional_patterns": {
                "if_then": r'만약\s*(.+?)\s*이면\s*(.+?)\s*이다',
                "when": r'(.+?)\s*일\s*때\s*(.+?)',
                "and_condition": r'(.+?)\s*그리고\s*(.+?)',
                "or_condition": r'(.+?)\s*또는\s*(.+?)',
                "not_condition": r'(.+?)\s*아닌\s*(.+?)'
            }
        }
    
    def _init_sql_patterns(self):
        """SQL 패턴 매핑 - 동적 딕셔너리에서 로드"""
        self.sql_patterns = self.dict_manager.sql_patterns
    
    def _init_entity_extractors(self):
        """엔티티 추출기 초기화"""
        self.entity_extractors = {
            "credit_score": self._extract_credit_score,
            "risk_level": self._extract_risk_level,
            "loan_amount": self._extract_loan_amount,
            "customer_type": self._extract_customer_type,
            "date_range": self._extract_date_range,
            "numeric_range": self._extract_numeric_range
        }
    
    def preprocess_query(self, query: str) -> Dict:
        """메인 전처리 함수"""
        try:
            # 1단계: 기본 정규화
            normalized_query = self._normalize_text(query)
            
            # 2단계: 도메인 특화 딕셔너리 매핑
            mapped_query = self._apply_domain_mapping(normalized_query)
            
            # 3단계: 엔티티 추출
            entities = self._extract_entities(normalized_query)
            
            # 4단계: 절(Clause) 추출
            clauses = self._extract_clauses(normalized_query)
            
            # 5단계: Chain of Thought 추론
            reasoning_chain = self._generate_reasoning_chain(normalized_query, entities, clauses)
            
            # 6단계: SQL 패턴 매핑
            sql_mappings = self._map_sql_patterns(normalized_query)
            
            return {
                "original_query": query,
                "normalized_query": normalized_query,
                "mapped_query": mapped_query,
                "entities": entities,
                "clauses": clauses,
                "reasoning_chain": reasoning_chain,
                "sql_mappings": sql_mappings,
                "preprocessing_metadata": {
                    "domain_terms_found": len(entities.get("domain_terms", [])),
                    "clauses_count": len(clauses),
                    "reasoning_steps": len(reasoning_chain),
                    "sql_patterns_mapped": len(sql_mappings)
                }
            }
            
        except Exception as e:
            return {
                "error": f"전처리 중 오류 발생: {str(e)}",
                "original_query": query
            }
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 공백 정규화
        text = re.sub(self.processing_rules["normalization"]["whitespace"], ' ', text)
        
        # 특수문자 처리 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?()]', '', text)
        
        # 숫자 패턴 정규화
        text = re.sub(r'(\d+)원', r'\1 원', text)
        text = re.sub(r'(\d+)%', r'\1 퍼센트', text)
        
        return text.strip()
    
    def _apply_domain_mapping(self, text: str) -> str:
        """도메인 특화 딕셔너리 매핑 적용"""
        mapped_text = text
        
        # 신용평가 도메인 용어 매핑
        for category, terms in self.dict_manager.credit_terms.items():
            for term, info in terms.items():
                if term in mapped_text:
                    mapped_text = mapped_text.replace(term, info["sql_mapping"])
                
                # 동의어 매핑
                for synonym in info.get("synonyms", []):
                    if synonym in mapped_text:
                        mapped_text = mapped_text.replace(synonym, info["sql_mapping"])
        
        return mapped_text
    
    def _extract_entities(self, text: str) -> Dict:
        """엔티티 추출"""
        entities = {
            "domain_terms": [],
            "numeric_values": [],
            "date_values": [],
            "customer_types": [],
            "risk_levels": [],
            "credit_scores": []
        }
        
        # 도메인 용어 추출
        for category, terms in self.dict_manager.credit_terms.items():
            for term, info in terms.items():
                if term in text or any(syn in text for syn in info.get("synonyms", [])):
                    entities["domain_terms"].append({
                        "term": term,
                        "category": category,
                        "sql_mapping": info.get("sql_mapping", term),
                        "table": info.get("table", "")
                    })
        
        # 숫자 값 추출
        numeric_patterns = [
            r'(\d+)원',
            r'(\d+)%',
            r'(\d+)일',
            r'(\d+)개월',
            r'(\d+)년'
        ]
        
        for pattern in numeric_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities["numeric_values"].append({
                    "value": match,
                    "pattern": pattern,
                    "type": "currency" if "원" in pattern else "percentage" if "%" in pattern else "duration"
                })
        
        # 고객 유형 추출
        customer_types = ["개인고객", "기업고객", "소상공인", "VIP고객", "관리고객"]
        for customer_type in customer_types:
            if customer_type in text:
                entities["customer_types"].append(customer_type)
        
        # 위험도 레벨 추출
        risk_levels = ["낮음", "보통", "높음", "매우낮음", "매우높음"]
        for risk_level in risk_levels:
            if risk_level in text:
                entities["risk_levels"].append(risk_level)
        
        return entities
    
    def _extract_clauses(self, text: str) -> List[Dict]:
        """절(Clause) 추출"""
        clauses = []
        processed_clauses = set()  # 중복 방지
        
        # 1단계: 명확한 구분자로 분리 (우선순위 높음)
        primary_patterns = [
            r'([^.!?]+[.!?])',  # 마침표, 느낌표, 물음표로 끝나는 문장
            r'([^그리고]+그리고[^그리고]+)',  # 그리고로 연결된 절
            r'([^또는]+또는[^또는]+)',  # 또는로 연결된 절
            r'([^이고]+이고[^이고]+)',  # 이고로 연결된 절
            r'([^이거나]+이거나[^이거나]+)',  # 이거나로 연결된 절
            r'([^하며]+하며[^하며]+)',  # 며로 연결된 절
        ]
        
        # 2단계: 보조 구분자로 분리 (우선순위 낮음)
        secondary_patterns = [
            r'([^,]+)',  # 쉼표로 구분
        ]
        
        # 우선순위 높은 패턴부터 처리
        for pattern in primary_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clause_text = match.strip()
                if len(clause_text) > 3 and clause_text not in processed_clauses:
                    clause_info = self._analyze_clause(clause_text)
                    if clause_info:
                        clauses.append(clause_info)
                        processed_clauses.add(clause_text)
        
        # 만약 절이 추출되지 않았다면, 수동으로 복합문 분리 시도
        if not clauses:
            clauses = self._manual_clause_split(text.strip())
        
        return clauses
    
    def _manual_clause_split(self, text: str) -> List[Dict]:
        """수동 절 분리 (복합문 처리)"""
        clauses = []
        
        # 한국어 연결어 패턴
        connectors = [
            '그리고', '또는', '이거나', '이고', '하며', '면서', '하지만', '그런데',
            '또한', '또한', '또한', '또한', '또한', '또한', '또한', '또한'
        ]
        
        # 연결어로 분리
        parts = [text]
        for connector in connectors:
            new_parts = []
            for part in parts:
                if connector in part:
                    split_parts = part.split(connector)
                    for i, split_part in enumerate(split_parts):
                        if split_part.strip():
                            new_parts.append(split_part.strip())
                        if i < len(split_parts) - 1:  # 마지막 부분이 아니면 연결어 추가
                            new_parts.append(connector)
                else:
                    new_parts.append(part)
            parts = new_parts
        
        # 각 부분을 절로 분석
        for part in parts:
            if len(part.strip()) > 2:  # 의미있는 길이만
                clause_info = self._analyze_clause(part.strip())
                if clause_info:
                    clauses.append(clause_info)
        
        return clauses
    
    def _analyze_clause(self, clause: str) -> Optional[Dict]:
        """절 분석"""
        # jieba로 형태소 분석
        words = list(jieba.cut(clause))
        
        # 도메인 용어 포함 여부 확인
        domain_terms = []
        for word in words:
            term_info = self.dict_manager.get_term_info(word)
            if term_info:
                domain_terms.append(term_info)
        
        # 절 유형 분석
        clause_type = self._identify_clause_type(clause)
        
        # 조건부 표현 확인
        conditional_type = None
        if "만약" in clause:
            conditional_type = "if_then"
        elif "일 때" in clause:
            conditional_type = "when"
        elif "그리고" in clause:
            conditional_type = "and"
        elif "또는" in clause:
            conditional_type = "or"
        
        # SQL 패턴 확인
        sql_patterns = []
        for pattern_type, patterns in self.sql_patterns.items():
            for korean, sql in patterns.items():
                if korean in clause:
                    sql_patterns.append({
                        "korean": korean,
                        "sql": sql,
                        "type": pattern_type
                    })
        
        # 신뢰도 계산
        confidence = self._calculate_confidence(clause, domain_terms, sql_patterns)
        
        # 프론트엔드 호환성을 위한 구조 변환
        return {
            "type": clause_type,
            "confidence": confidence,
            "content": clause,
            "keywords": [term["term"] for term in domain_terms] if domain_terms else [],
            "clause": clause,
            "words": words,
            "domain_terms": domain_terms,
            "conditional_type": conditional_type,
            "sql_patterns": sql_patterns,
            "length": len(clause)
        }
    
    def _identify_clause_type(self, clause: str) -> str:
        """절 유형 식별"""
        clause_lower = clause.lower()
        
        if "?" in clause or "는?" in clause or "을?" in clause:
            return "question"
        elif any(word in clause_lower for word in ["평균", "평균값", "avg"]):
            return "aggregation_avg"
        elif any(word in clause_lower for word in ["합계", "총합", "sum"]):
            return "aggregation_sum"
        elif any(word in clause_lower for word in ["개수", "건수", "count"]):
            return "aggregation_count"
        elif any(word in clause_lower for word in ["최대", "최고", "max"]):
            return "aggregation_max"
        elif any(word in clause_lower for word in ["최소", "최저", "min"]):
            return "aggregation_min"
        elif any(word in clause_lower for word in ["조건", "만약", "일 때"]):
            return "condition"
        elif any(word in clause_lower for word in ["그리고", "또는", "and", "or"]):
            return "logical"
        else:
            return "general"
    
    def _calculate_confidence(self, clause: str, domain_terms: List, sql_patterns: List) -> float:
        """절 분석 신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도
        
        # 도메인 용어가 있으면 신뢰도 증가
        if domain_terms:
            confidence += 0.2
        
        # SQL 패턴이 있으면 신뢰도 증가
        if sql_patterns:
            confidence += 0.2
        
        # 절 길이가 적절하면 신뢰도 증가
        if 5 <= len(clause) <= 50:
            confidence += 0.1
        
        return min(confidence, 1.0)  # 최대 1.0
    
    def _generate_reasoning_chain(self, query: str, entities: Dict, clauses: List[Dict]) -> List[str]:
        """Chain of Thought 추론 생성"""
        reasoning_steps = []
        
        # 1단계: 질문 유형 파악
        question_type = self._identify_question_type(query)
        reasoning_steps.append(f"질문 유형: {question_type}")
        
        # 2단계: 도메인 용어 분석
        if entities["domain_terms"]:
            terms_summary = ", ".join([term["term"] for term in entities["domain_terms"]])
            reasoning_steps.append(f"도메인 용어 발견: {terms_summary}")
        
        # 3단계: 조건 분석
        conditions = []
        for clause in clauses:
            if clause["conditional_type"]:
                conditions.append(f"{clause['clause']} ({clause['conditional_type']})")
        
        if conditions:
            reasoning_steps.append(f"조건부 표현: {'; '.join(conditions)}")
        
        # 4단계: SQL 패턴 매핑
        sql_patterns = []
        for clause in clauses:
            for pattern in clause["sql_patterns"]:
                sql_patterns.append(f"{pattern['korean']} → {pattern['sql']}")
        
        if sql_patterns:
            reasoning_steps.append(f"SQL 패턴: {'; '.join(sql_patterns)}")
        
        # 5단계: 추론 결과
        reasoning_steps.append("추론 완료: 자연어를 SQL로 변환할 준비가 되었습니다.")
        
        return reasoning_steps
    
    def _identify_question_type(self, query: str) -> str:
        """질문 유형 파악"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["몇", "개수", "건수", "수량"]):
            return "COUNT_QUERY"
        elif any(word in query_lower for word in ["합계", "총합", "합"]):
            return "SUM_QUERY"
        elif any(word in query_lower for word in ["평균", "평균값"]):
            return "AVG_QUERY"
        elif any(word in query_lower for word in ["최대", "최고"]):
            return "MAX_QUERY"
        elif any(word in query_lower for word in ["최소", "최저"]):
            return "MIN_QUERY"
        elif any(word in query_lower for word in ["목록", "리스트", "조회"]):
            return "SELECT_QUERY"
        else:
            return "GENERAL_QUERY"
    
    def _map_sql_patterns(self, text: str) -> Dict:
        """SQL 패턴 매핑"""
        mappings = {
            "aggregation": [],
            "comparison": [],
            "ordering": []
        }
        
        for pattern_type, patterns in self.sql_patterns.items():
            for korean, sql in patterns.items():
                if korean in text:
                    mappings[pattern_type].append({
                        "korean": korean,
                        "sql": sql,
                        "context": self._extract_context(text, korean)
                    })
        
        return mappings
    
    def _extract_context(self, text: str, keyword: str) -> str:
        """키워드 주변 문맥 추출"""
        try:
            index = text.index(keyword)
            start = max(0, index - 20)
            end = min(len(text), index + len(keyword) + 20)
            return text[start:end].strip()
        except ValueError:
            return ""
    
    def _extract_credit_score(self, text: str) -> List[Dict]:
        """신용점수 추출"""
        patterns = [
            r'신용점수\s*(\d+)',
            r'크레딧스코어\s*(\d+)',
            r'(\d+)\s*점'
        ]
        
        scores = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                score = int(match)
                if 300 <= score <= 850:
                    scores.append({
                        "value": score,
                        "type": "credit_score",
                        "range": self._get_score_range(score)
                    })
        
        return scores
    
    def _get_score_range(self, score: int) -> str:
        """점수 범위 분류"""
        if score >= 800:
            return "매우높음"
        elif score >= 750:
            return "높음"
        elif score >= 650:
            return "보통"
        elif score >= 550:
            return "낮음"
        else:
            return "매우낮음"
    
    def _extract_risk_level(self, text: str) -> List[str]:
        """위험도 레벨 추출"""
        risk_levels = []
        korean_risk_levels = ["매우낮음", "낮음", "보통", "높음", "매우높음"]
        
        for level in korean_risk_levels:
            if level in text:
                risk_levels.append(level)
        
        return risk_levels
    
    def _extract_loan_amount(self, text: str) -> List[Dict]:
        """대출금액 추출"""
        patterns = [
            r'대출금액\s*(\d+)원',
            r'(\d+)원\s*대출',
            r'대출\s*(\d+)원'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                amounts.append({
                    "value": int(match),
                    "type": "loan_amount",
                    "unit": "원"
                })
        
        return amounts
    
    def _extract_customer_type(self, text: str) -> List[str]:
        """고객 유형 추출"""
        customer_types = []
        type_patterns = {
            "개인고객": ["개인", "개인고객", "개인신용"],
            "기업고객": ["기업", "기업고객", "기업신용"],
            "소상공인": ["소상공인", "소상공인고객"],
            "VIP고객": ["VIP", "VIP고객", "우수고객"],
            "관리고객": ["관리", "관리고객", "주의고객"]
        }
        
        for customer_type, patterns in type_patterns.items():
            if any(pattern in text for pattern in patterns):
                customer_types.append(customer_type)
        
        return customer_types
    
    def _extract_date_range(self, text: str) -> List[Dict]:
        """날짜 범위 추출"""
        date_patterns = [
            r'(\d{4})년(\d{1,2})월(\d{1,2})일',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})월(\d{1,2})일'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    dates.append({
                        "year": match[0],
                        "month": match[1],
                        "day": match[2],
                        "type": "full_date"
                    })
                elif len(match) == 2:
                    dates.append({
                        "month": match[0],
                        "day": match[1],
                        "type": "month_day"
                    })
        
        return dates
    
    def _extract_numeric_range(self, text: str) -> List[Dict]:
        """숫자 범위 추출"""
        range_patterns = [
            r'(\d+)\s*이상\s*(\d+)이하',
            r'(\d+)\s*부터\s*(\d+)까지',
            r'(\d+)\s*~\s*(\d+)',
            r'(\d+)\s*-\s*(\d+)'
        ]
        
        ranges = []
        for pattern in range_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                ranges.append({
                    "min": int(match[0]),
                    "max": int(match[1]),
                    "type": "numeric_range"
                })
        
        return ranges

# 전역 인스턴스
hybrid_agent = HybridPreprocessingAgent()

# 사용 예시
if __name__ == "__main__":
    # 테스트 쿼리들
    test_queries = [
        "신용점수 750 이상인 개인고객의 대출금액 합계를 조회해주세요",
        "위험도가 높은 기업고객 중 연체일수가 30일 이상인 고객 수를 알려주세요",
        "VIP고객의 평균 신용점수와 일반고객의 평균 신용점수를 비교해주세요",
        "소득수준이 보통이고 신용점수가 650 이상인 고객 목록을 조회해주세요"
    ]
    
    print("🔧 규칙 기반 + 딕셔너리 혼합 전처리 에이전트 테스트\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"📝 테스트 쿼리 {i}: {query}")
        result = hybrid_agent.preprocess_query(query)
        
        if "error" not in result:
            print(f"✅ 정규화된 쿼리: {result['normalized_query']}")
            print(f"🔗 매핑된 쿼리: {result['mapped_query']}")
            print(f"🏷️ 도메인 용어: {len(result['entities']['domain_terms'])}개")
            print(f"📋 절(Clause): {len(result['clauses'])}개")
            print(f"🧠 추론 단계: {len(result['reasoning_chain'])}단계")
            print(f"🔧 SQL 패턴: {len(result['sql_mappings']['aggregation'] + result['sql_mappings']['comparison'] + result['sql_mappings']['ordering'])}개")
            print()
        else:
            print(f"❌ 오류: {result['error']}")
            print() 