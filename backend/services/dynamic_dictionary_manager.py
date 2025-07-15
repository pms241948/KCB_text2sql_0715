#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
동적 딕셔너리 관리 시스템
JSON 파일을 기반으로 딕셔너리를 동적으로 로드하고 관리
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil

class DynamicDictionaryManager:
    """동적 딕셔너리 관리 클래스"""
    
    def __init__(self, dictionaries_dir: str = None):
        if dictionaries_dir is None:
            # 상위 디렉토리의 data/dictionaries 폴더 사용
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.dictionaries_dir = os.path.join(current_dir, "data", "dictionaries")
        else:
            self.dictionaries_dir = dictionaries_dir
            
        self.credit_terms = {}
        self.sql_patterns = {}
        self.backup_dir = os.path.join(self.dictionaries_dir, "backups")
        
        # 디렉토리 생성
        os.makedirs(self.dictionaries_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 딕셔너리 로드
        self.load_all_dictionaries()
    
    def load_all_dictionaries(self):
        """모든 딕셔너리 파일 로드"""
        try:
            # 신용평가 도메인 용어 로드
            credit_terms_path = os.path.join(self.dictionaries_dir, "credit_terms.json")
            if os.path.exists(credit_terms_path):
                with open(credit_terms_path, 'r', encoding='utf-8') as f:
                    self.credit_terms = json.load(f)
                print(f"✅ 신용평가 도메인 용어 딕셔너리 로드 완료")
            else:
                print(f"⚠️ 신용평가 도메인 용어 딕셔너리 파일이 없습니다: {credit_terms_path}")
            
            # SQL 패턴 로드
            sql_patterns_path = os.path.join(self.dictionaries_dir, "sql_patterns.json")
            if os.path.exists(sql_patterns_path):
                with open(sql_patterns_path, 'r', encoding='utf-8') as f:
                    self.sql_patterns = json.load(f)
                print(f"✅ SQL 패턴 딕셔너리 로드 완료")
            else:
                print(f"⚠️ SQL 패턴 딕셔너리 파일이 없습니다: {sql_patterns_path}")
                
        except Exception as e:
            print(f"❌ 딕셔너리 로드 중 오류: {e}")
    
    def reload_dictionaries(self):
        """딕셔너리 재로드"""
        self.load_all_dictionaries()
        return {
            "credit_terms_loaded": bool(self.credit_terms),
            "sql_patterns_loaded": bool(self.sql_patterns),
            "timestamp": datetime.now().isoformat()
        }
    
    def backup_dictionaries(self):
        """현재 딕셔너리 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 신용평가 도메인 용어 백업
            if self.credit_terms:
                backup_path = os.path.join(self.backup_dir, f"credit_terms_{timestamp}.json")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.credit_terms, f, ensure_ascii=False, indent=2)
            
            # SQL 패턴 백업
            if self.sql_patterns:
                backup_path = os.path.join(self.backup_dir, f"sql_patterns_{timestamp}.json")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(self.sql_patterns, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 딕셔너리 백업 완료: {timestamp}")
            return {"success": True, "timestamp": timestamp}
            
        except Exception as e:
            print(f"❌ 딕셔너리 백업 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def save_credit_terms(self):
        """신용평가 도메인 용어 저장"""
        try:
            # 백업 생성
            self.backup_dictionaries()
            
            # 파일 저장
            file_path = os.path.join(self.dictionaries_dir, "credit_terms.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.credit_terms, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 신용평가 도메인 용어 딕셔너리 저장 완료")
            return {"success": True, "file_path": file_path}
            
        except Exception as e:
            print(f"❌ 딕셔너리 저장 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def save_sql_patterns(self):
        """SQL 패턴 저장"""
        try:
            # 백업 생성
            self.backup_dictionaries()
            
            # 파일 저장
            file_path = os.path.join(self.dictionaries_dir, "sql_patterns.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.sql_patterns, f, ensure_ascii=False, indent=2)
            
            print(f"✅ SQL 패턴 딕셔너리 저장 완료")
            return {"success": True, "file_path": file_path}
            
        except Exception as e:
            print(f"❌ 딕셔너리 저장 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def add_credit_term(self, category: str, term: str, info: Dict[str, Any]):
        """신용평가 도메인 용어 추가"""
        try:
            if category not in self.credit_terms:
                self.credit_terms[category] = {}
            
            self.credit_terms[category][term] = info
            self.save_credit_terms()
            
            print(f"✅ 신용평가 도메인 용어 추가 완료: {category}.{term}")
            return {"success": True, "term": term, "category": category}
            
        except Exception as e:
            print(f"❌ 용어 추가 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def update_credit_term(self, category: str, term: str, info: Dict[str, Any]):
        """신용평가 도메인 용어 수정"""
        try:
            if category not in self.credit_terms:
                return {"success": False, "error": f"카테고리가 존재하지 않습니다: {category}"}
            
            if term not in self.credit_terms[category]:
                return {"success": False, "error": f"용어가 존재하지 않습니다: {term}"}
            
            self.credit_terms[category][term] = info
            self.save_credit_terms()
            
            print(f"✅ 신용평가 도메인 용어 수정 완료: {category}.{term}")
            return {"success": True, "term": term, "category": category}
            
        except Exception as e:
            print(f"❌ 용어 수정 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_credit_term(self, category: str, term: str):
        """신용평가 도메인 용어 삭제"""
        try:
            if category not in self.credit_terms:
                return {"success": False, "error": f"카테고리가 존재하지 않습니다: {category}"}
            
            if term not in self.credit_terms[category]:
                return {"success": False, "error": f"용어가 존재하지 않습니다: {term}"}
            
            deleted_info = self.credit_terms[category].pop(term)
            self.save_credit_terms()
            
            print(f"✅ 신용평가 도메인 용어 삭제 완료: {category}.{term}")
            return {"success": True, "term": term, "category": category, "deleted_info": deleted_info}
            
        except Exception as e:
            print(f"❌ 용어 삭제 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def add_sql_pattern(self, category: str, korean: str, sql: str):
        """SQL 패턴 추가"""
        try:
            if category not in self.sql_patterns:
                self.sql_patterns[category] = {}
            
            self.sql_patterns[category][korean] = sql
            self.save_sql_patterns()
            
            print(f"✅ SQL 패턴 추가 완료: {category}.{korean} → {sql}")
            return {"success": True, "korean": korean, "sql": sql, "category": category}
            
        except Exception as e:
            print(f"❌ SQL 패턴 추가 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def update_sql_pattern(self, category: str, korean: str, sql: str):
        """SQL 패턴 수정"""
        try:
            if category not in self.sql_patterns:
                return {"success": False, "error": f"카테고리가 존재하지 않습니다: {category}"}
            
            if korean not in self.sql_patterns[category]:
                return {"success": False, "error": f"패턴이 존재하지 않습니다: {korean}"}
            
            old_sql = self.sql_patterns[category][korean]
            self.sql_patterns[category][korean] = sql
            self.save_sql_patterns()
            
            print(f"✅ SQL 패턴 수정 완료: {category}.{korean} → {sql} (이전: {old_sql})")
            return {"success": True, "korean": korean, "old_sql": old_sql, "new_sql": sql, "category": category}
            
        except Exception as e:
            print(f"❌ SQL 패턴 수정 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_sql_pattern(self, category: str, korean: str):
        """SQL 패턴 삭제"""
        try:
            if category not in self.sql_patterns:
                return {"success": False, "error": f"카테고리가 존재하지 않습니다: {category}"}
            
            if korean not in self.sql_patterns[category]:
                return {"success": False, "error": f"패턴이 존재하지 않습니다: {korean}"}
            
            deleted_sql = self.sql_patterns[category].pop(korean)
            self.save_sql_patterns()
            
            print(f"✅ SQL 패턴 삭제 완료: {category}.{korean} → {deleted_sql}")
            return {"success": True, "korean": korean, "deleted_sql": deleted_sql, "category": category}
            
        except Exception as e:
            print(f"❌ SQL 패턴 삭제 중 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def get_term_info(self, term: str) -> Optional[Dict]:
        """용어 정보 조회"""
        for category, terms in self.credit_terms.items():
            for key, info in terms.items():
                if term == key or term in info.get("synonyms", []):
                    return {
                        "category": category,
                        "term": key,
                        "info": info
                    }
        return None
    
    def get_sql_mapping(self, term: str) -> str:
        """SQL 매핑 조회"""
        term_info = self.get_term_info(term)
        if term_info:
            return term_info["info"].get("sql_mapping", term)
        return term
    
    def get_sql_pattern(self, category: str, korean: str) -> Optional[str]:
        """SQL 패턴 조회"""
        if category in self.sql_patterns and korean in self.sql_patterns[category]:
            return self.sql_patterns[category][korean]
        return None
    
    def search_terms(self, query: str) -> List[Dict]:
        """용어 검색"""
        results = []
        query_lower = query.lower()
        
        for category, terms in self.credit_terms.items():
            for key, info in terms.items():
                # 정확한 매칭
                if query_lower == key.lower():
                    results.append({
                        "category": category,
                        "term": key,
                        "match_type": "exact",
                        "info": info
                    })
                # 부분 매칭
                elif query_lower in key.lower() or key.lower() in query_lower:
                    results.append({
                        "category": category,
                        "term": key,
                        "match_type": "partial",
                        "info": info
                    })
                # 동의어 매칭
                elif "synonyms" in info:
                    for synonym in info["synonyms"]:
                        if query_lower == synonym.lower():
                            results.append({
                                "category": category,
                                "term": key,
                                "match_type": "synonym",
                                "info": info
                            })
                            break
        
        return results
    
    def get_dictionary_stats(self) -> Dict:
        """딕셔너리 통계 정보"""
        stats = {
            "credit_terms": {},
            "sql_patterns": {},
            "total_terms": 0,
            "total_patterns": 0
        }
        
        # 신용평가 도메인 용어 통계
        for category, terms in self.credit_terms.items():
            stats["credit_terms"][category] = len(terms)
            stats["total_terms"] += len(terms)
        
        # SQL 패턴 통계
        for category, patterns in self.sql_patterns.items():
            stats["sql_patterns"][category] = len(patterns)
            stats["total_patterns"] += len(patterns)
        
        return stats
    
    def export_dictionary(self, format: str = "json") -> Dict:
        """딕셔너리 내보내기"""
        if format.lower() == "json":
            return {
                "credit_terms": self.credit_terms,
                "sql_patterns": self.sql_patterns,
                "export_timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": f"지원하지 않는 형식입니다: {format}"}
    
    def import_dictionary(self, data: Dict) -> Dict:
        """딕셔너리 가져오기"""
        try:
            # 백업 생성
            self.backup_dictionaries()
            
            # 데이터 가져오기
            if "credit_terms" in data:
                self.credit_terms = data["credit_terms"]
                self.save_credit_terms()
            
            if "sql_patterns" in data:
                self.sql_patterns = data["sql_patterns"]
                self.save_sql_patterns()
            
            print(f"✅ 딕셔너리 가져오기 완료")
            return {"success": True, "import_timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            print(f"❌ 딕셔너리 가져오기 중 오류: {e}")
            return {"success": False, "error": str(e)}

# 전역 인스턴스
dictionary_manager = DynamicDictionaryManager()

# 사용 예시
if __name__ == "__main__":
    # 딕셔너리 상태 확인
    stats = dictionary_manager.get_dictionary_stats()
    print(f"📊 딕셔너리 통계: {stats}")
    
    # 용어 검색 테스트
    search_results = dictionary_manager.search_terms("신용")
    print(f"🔍 '신용' 검색 결과: {len(search_results)}개")
    for result in search_results:
        print(f"  {result['term']} ({result['match_type']}) - {result['category']}")
    
    # 새로운 용어 추가 테스트
    new_term_info = {
        "synonyms": ["테스트용어", "테스트"],
        "sql_mapping": "test_field",
        "table": "test_table",
        "data_type": "VARCHAR"
    }
    result = dictionary_manager.add_credit_term("test_category", "테스트용어", new_term_info)
    print(f"➕ 새 용어 추가: {result}")
    
    # SQL 패턴 추가 테스트
    result = dictionary_manager.add_sql_pattern("test_agg", "테스트집계", "TEST_AGG")
    print(f"➕ 새 SQL 패턴 추가: {result}") 