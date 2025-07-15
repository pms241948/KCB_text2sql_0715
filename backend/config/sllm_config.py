#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sLLM (Small Language Model) 설정 파일
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class SLLMConfig:
    """sLLM 설정 클래스"""
    api_key: str
    model: str
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout: int = 30

class SLLMManager:
    """sLLM 관리 클래스"""
    
    def __init__(self):
        # sLLM 설정 로드
        self.sllm_config = self._load_sllm_config()
        self.main_config = self._load_main_config()
        
    def _load_sllm_config(self) -> SLLMConfig:
        """sLLM 설정 로드"""
        # sLLM 전용 API 키가 있으면 사용, 없으면 메인 API 키 사용
        sllm_api_key = os.getenv('OPENAI_SLLM_API_KEY', os.getenv('OPENAI_API_KEY'))
        sllm_model = os.getenv('OPENAI_SLLM_MODEL', 'gpt-3.5-turbo')
        
        return SLLMConfig(
            api_key=sllm_api_key,
            model=sllm_model,
            max_tokens=int(os.getenv('OPENAI_SLLM_MAX_TOKENS', '1000')),
            temperature=float(os.getenv('OPENAI_SLLM_TEMPERATURE', '0.1')),
            timeout=int(os.getenv('OPENAI_SLLM_TIMEOUT', '30'))
        )
    
    def _load_main_config(self) -> SLLMConfig:
        """메인 LLM 설정 로드"""
        return SLLMConfig(
            api_key=os.getenv('OPENAI_API_KEY'),
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '500')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            timeout=int(os.getenv('OPENAI_TIMEOUT', '30'))
        )
    
    def get_sllm_client(self):
        """sLLM 클라이언트 생성"""
        try:
            from openai import OpenAI
            return OpenAI(
                api_key=self.sllm_config.api_key,
                base_url=self.sllm_config.base_url
            )
        except ImportError:
            print("OpenAI 클라이언트를 사용할 수 없습니다.")
            return None
    
    def get_main_client(self):
        """메인 LLM 클라이언트 생성"""
        try:
            from openai import OpenAI
            return OpenAI(
                api_key=self.main_config.api_key,
                base_url=self.main_config.base_url
            )
        except ImportError:
            print("OpenAI 클라이언트를 사용할 수 없습니다.")
            return None
    
    def call_sllm(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """sLLM 호출"""
        client = self.get_sllm_client()
        if not client:
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.sllm_config.model,
                messages=messages,
                max_tokens=self.sllm_config.max_tokens,
                temperature=self.sllm_config.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"sLLM 호출 오류: {e}")
            return None
    
    def get_config_info(self) -> dict:
        """설정 정보 반환"""
        return {
            "sllm": {
                "model": self.sllm_config.model,
                "max_tokens": self.sllm_config.max_tokens,
                "temperature": self.sllm_config.temperature,
                "api_key_configured": bool(self.sllm_config.api_key),
                "separate_api_key": self.sllm_config.api_key != self.main_config.api_key
            },
            "main": {
                "model": self.main_config.model,
                "max_tokens": self.main_config.max_tokens,
                "temperature": self.main_config.temperature,
                "api_key_configured": bool(self.main_config.api_key)
            }
        }

# 전역 인스턴스
sllm_manager = SLLMManager()

# 사용 예시
if __name__ == "__main__":
    # 설정 정보 출력
    config_info = sllm_manager.get_config_info()
    print("sLLM 설정 정보:")
    print(f"  모델: {config_info['sllm']['model']}")
    print(f"  별도 API 키 사용: {config_info['sllm']['separate_api_key']}")
    print(f"  API 키 설정됨: {config_info['sllm']['api_key_configured']}")
    
    # 테스트 호출
    test_prompt = "다음 텍스트에서 SQL 키워드를 추출해주세요: '신용점수가 높은 고객을 조회하고 정렬해주세요'"
    result = sllm_manager.call_sllm(test_prompt, "당신은 SQL 키워드 추출 전문가입니다.")
    
    if result:
        print(f"\n테스트 결과: {result}")
    else:
        print("\n테스트 실패") 