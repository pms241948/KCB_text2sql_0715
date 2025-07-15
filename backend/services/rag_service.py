import os
import json
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.embeddings.base import Embeddings
from openai import OpenAI
import requests
import numpy as np
from typing import List, Dict, Optional
import pickle
from datetime import datetime

class EnterpriseEmbeddings(Embeddings):
    """기업/공급업체 임베딩 서비스 클래스"""
    
    def __init__(self, base_url: str, model: str, api_key: str = None):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩"""
        embeddings = []
        for text in texts:
            embedding = self.embed_query(text)
            if embedding:
                embeddings.append(embedding)
            else:
                # 에러 시 0으로 채운 벡터 반환
                embeddings.append([0.0] * 384)  # 기본 차원
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """단일 쿼리 임베딩"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            payload = {
                "model": self.model,
                "input": text
            }
            
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                print(f"기업 임베딩 API 오류: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"기업 임베딩 호출 중 오류: {e}")
            return None

class RAGService:
    def __init__(self, persist_directory=None):
        """RAG 서비스 초기화"""
        if persist_directory is None:
            # 상위 디렉토리의 database/chromadb 폴더 사용
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.persist_directory = os.path.join(current_dir, "database", "chromadb")
        else:
            self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # LLM 설정
        self.llm_provider = os.getenv('LLM_PROVIDER', 'openai')
        self.llm_base_url = os.getenv('LLM_BASE_URL')
        self.llm_api_key = os.getenv('LLM_API_KEY')
        
        # OpenAI 클라이언트 초기화 (기본값)
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 임베딩 모델 설정
        self.embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
        self.embedding_base_url = os.getenv('EMBEDDING_BASE_URL')
        
        # 임베딩 모델 초기화
        self.embeddings = self._init_embeddings()
        
        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 컬렉션 초기화
        self.collection = self.client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 도메인별 컬렉션도 생성
        self.domain_collections = {}
        self._init_domain_collections()
    
    def _init_embeddings(self):
        """임베딩 모델 초기화"""
        try:
            if self.embedding_provider == 'openai':
                # OpenAI 임베딩 사용
                return OpenAIEmbeddings(
                    model=self.embedding_model,
                    openai_api_key=os.getenv('OPENAI_API_KEY')
                )
            elif self.embedding_provider == 'local':
                # 로컬 임베딩 모델 사용 (sentence-transformers)
                return HuggingFaceEmbeddings(
                    model_name=self.embedding_model,
                    model_kwargs={'device': 'cpu'},  # GPU 사용 시 'cuda'로 변경
                    encode_kwargs={'normalize_embeddings': True}
                )
            elif self.embedding_provider == 'enterprise':
                # 기업/공급업체 임베딩 서비스 사용
                return EnterpriseEmbeddings(
                    base_url=self.embedding_base_url,
                    model=self.embedding_model,
                    api_key=os.getenv('EMBEDDING_API_KEY')
                )
            else:
                # 기본값으로 OpenAI 임베딩 사용
                print(f"알 수 없는 임베딩 프로바이더: {self.embedding_provider}, OpenAI 임베딩을 사용합니다.")
                return OpenAIEmbeddings(
                    model="text-embedding-ada-002",
                    openai_api_key=os.getenv('OPENAI_API_KEY')
                )
        except Exception as e:
            print(f"임베딩 모델 초기화 오류: {e}")
            # 폴백으로 OpenAI 임베딩 사용
            return OpenAIEmbeddings(
                model="text-embedding-ada-002",
                openai_api_key=os.getenv('OPENAI_API_KEY')
            )
    
    def call_local_llm(self, prompt, system_prompt="당신은 문서 분석 전문가입니다."):
        """로컬 LLM API 호출 함수"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.llm_api_key:
                headers['Authorization'] = f'Bearer {self.llm_api_key}'
            
            payload = {
                "model": os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.llm_base_url}/v1/chat/completions",
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
    
    def _init_domain_collections(self):
        """도메인별 컬렉션 초기화"""
        domains = ['personal_credit', 'corporate_credit', 'policy_regulation']
        for domain in domains:
            self.domain_collections[domain] = self.client.get_or_create_collection(
                name=f"rag_{domain}",
                metadata={"hnsw:space": "cosine"}
            )
    
    def process_document(self, filepath: str, domain: str, filename: str) -> Dict:
        """문서를 처리하여 벡터 데이터베이스에 저장"""
        try:
            # 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 텍스트 청킹
            chunks = self.text_splitter.split_text(content)
            
            # 청크별 메타데이터 생성
            metadatas = []
            documents = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{domain}_{filename}_{i}"
                metadata = {
                    "domain": domain,
                    "filename": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "filepath": filepath,
                    "processed_at": datetime.now().isoformat()
                }
                
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append(metadata)
            
            # 임베딩 생성 및 저장
            if documents:
                # 전체 컬렉션에 저장
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # 도메인별 컬렉션에도 저장
                if domain in self.domain_collections:
                    self.domain_collections[domain].add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
            
            return {
                "success": True,
                "filename": filename,
                "domain": domain,
                "chunks_created": len(chunks),
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename,
                "domain": domain
            }
    
    def retrieve_relevant_chunks(self, question: str, domain: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """질문과 관련된 문서 청크들을 검색"""
        try:
            # 질문 임베딩 생성
            question_embedding = self.embeddings.embed_query(question)
            
            # 검색할 컬렉션 선택
            collection = self.domain_collections.get(domain, self.collection) if domain else self.collection
            
            # 유사도 검색
            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # 결과 포맷팅
            chunks = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    chunks.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": 1 - distance,  # 코사인 유사도로 변환
                        "rank": i + 1
                    })
            
            return chunks
            
        except Exception as e:
            print(f"청크 검색 중 오류: {e}")
            return []
    
    def get_rag_context(self, question: str, domain: Optional[str] = None, top_k: int = 5) -> str:
        """질문에 대한 RAG 컨텍스트 생성"""
        chunks = self.retrieve_relevant_chunks(question, domain, top_k)
        
        if not chunks:
            return ""
        
        # 컨텍스트 구성
        context_parts = []
        for chunk in chunks:
            metadata = chunk['metadata']
            content = chunk['content']
            similarity = chunk['similarity_score']
            
            context_part = f"[{metadata['domain']}:{metadata['filename']} - 청크 {metadata['chunk_index']+1}/{metadata['total_chunks']} - 유사도: {similarity:.3f}]\n{content}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def delete_document(self, domain: str, filename: str) -> Dict:
        """특정 문서의 모든 청크를 삭제"""
        try:
            # 메타데이터로 문서 필터링
            where_clause = {
                "domain": domain,
                "filename": filename
            }
            
            # 전체 컬렉션에서 삭제
            self.collection.delete(where=where_clause)
            
            # 도메인별 컬렉션에서도 삭제
            if domain in self.domain_collections:
                self.domain_collections[domain].delete(where=where_clause)
            
            return {
                "success": True,
                "message": f"{filename} 문서가 성공적으로 삭제되었습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_document_stats(self, domain: Optional[str] = None) -> Dict:
        """문서 통계 정보 반환"""
        try:
            collection = self.domain_collections.get(domain, self.collection) if domain else self.collection
            
            # 컬렉션 정보 조회
            count = collection.count()
            
            # 도메인별 통계
            if domain:
                return {
                    "domain": domain,
                    "total_chunks": count,
                    "collection_name": collection.name
                }
            else:
                # 전체 통계
                domain_stats = {}
                for domain_name, domain_collection in self.domain_collections.items():
                    domain_stats[domain_name] = domain_collection.count()
                
                return {
                    "total_chunks": count,
                    "domain_stats": domain_stats
                }
                
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def process_all_existing_documents(self, rag_folder: str = None):
        if rag_folder is None:
            # 상위 디렉토리의 data/rag_files 폴더 사용
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            rag_folder = os.path.join(current_dir, "data", "rag_files")
        """기존 RAG 폴더의 모든 문서를 처리"""
        domains = ['personal_credit', 'corporate_credit', 'policy_regulation']
        results = []
        
        for domain in domains:
            domain_path = os.path.join(rag_folder, domain)
            if os.path.exists(domain_path):
                for filename in os.listdir(domain_path):
                    filepath = os.path.join(domain_path, filename)
                    if os.path.isfile(filepath) and filename.endswith('.txt'):
                        result = self.process_document(filepath, domain, filename)
                        results.append(result)
        
        return results

# 전역 RAG 서비스 인스턴스
rag_service = None

def get_rag_service():
    """RAG 서비스 인스턴스 반환 (싱글톤 패턴)"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service 