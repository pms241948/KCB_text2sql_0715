import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Database, Code, User, Bot, FolderOpen, Upload, Trash2, CheckCircle, BarChart3, Settings } from 'lucide-react';
import './App.css';
import RagFileManager from './RagFileManager';
import RagStats from './RagStats';
import PreprocessingViewer from './PreprocessingViewer';

const RAG_DOMAINS = [
  { value: '', label: '전체 도메인' },
  { value: 'personal_credit', label: '개인 신용정보' },
  { value: 'corporate_credit', label: '기업 신용정보' },
  { value: 'policy_regulation', label: '평가 정책 및 규제' },
];

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [showMetadata, setShowMetadata] = useState(false);
  const [showRagManager, setShowRagManager] = useState(false);
  const [showRagStats, setShowRagStats] = useState(false);
  const [selectedRagDomain, setSelectedRagDomain] = useState('');
  const [showMetadataUpload, setShowMetadataUpload] = useState(false);
  const [metadataUploadMsg, setMetadataUploadMsg] = useState('');
  const [metadataFiles, setMetadataFiles] = useState([]);
  const [activeMeta, setActiveMeta] = useState('');
  const [showPreprocessing, setShowPreprocessing] = useState(false);
  const [preprocessingData, setPreprocessingData] = useState(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 메타데이터 로드
    loadMetadata();
    
    // 환영 메시지 추가
    setMessages([
      {
        id: 1,
        type: 'bot',
        content: '안녕하세요! 고객 데이터 분석을 위한 Text2SQL 도구입니다. 자연어로 질문하시면 SQL 쿼리로 변환해드립니다.',
        timestamp: new Date().toISOString()
      },
      {
        id: 2,
        type: 'bot',
        content: '예시 질문: "신용점수가 높은 고객 목록을 보여줘", "고객들의 평균 나이는?", "성별별 고객 분포는?"',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  const loadMetadata = async () => {
    try {
      const response = await axios.get('/api/metadata');
      setMetadata(response.data);
    } catch (error) {
      console.error('메타데이터 로드 실패:', error);
    }
  };

  // 메타데이터 파일 목록 불러오기
  const loadMetadataFiles = async () => {
    try {
      const res = await axios.get('/api/metadata/list');
      setMetadataFiles(res.data.files || []);
      setActiveMeta(res.data.active || '');
    } catch (e) {
      setMetadataFiles([]);
      setActiveMeta('');
    }
  };
  useEffect(() => { loadMetadataFiles(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post('/api/convert', {
        question: inputValue,
        rag_domain: selectedRagDomain || undefined
      });

      // 전처리 데이터 저장
      if (response.data.preprocessing) {
        setPreprocessingData(response.data.preprocessing);
      }

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.data.sql,
        timestamp: new Date().toISOString(),
        sql: response.data.sql,
        preprocessing: response.data.preprocessing
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  // 메타데이터 업로드 핸들러
  const handleMetadataUpload = async (e) => {
    e.preventDefault();
    if (!fileInputRef.current.files[0]) return;
    const formData = new FormData();
    formData.append('file', fileInputRef.current.files[0]);
    try {
      const res = await axios.post('/api/metadata/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMetadataUploadMsg('메타데이터 업로드 및 적용 성공!');
      setShowMetadataUpload(false);
      loadMetadataFiles();
    } catch (err) {
      setMetadataUploadMsg('업로드 실패: ' + (err.response?.data?.error || err.message));
    }
  };

  // 메타데이터 적용
  const handleApplyMeta = async (filename) => {
    try {
      await axios.post('/api/metadata/apply', { filename });
      setMetadataUploadMsg('적용 완료!');
      loadMetadataFiles();
    } catch (err) {
      setMetadataUploadMsg('적용 실패: ' + (err.response?.data?.error || err.message));
    }
  };

  // 메타데이터 삭제
  const handleDeleteMeta = async (filename) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;
    try {
      await axios.delete(`/api/metadata/delete/${filename}`);
      setMetadataUploadMsg('삭제 완료!');
      loadMetadataFiles();
    } catch (err) {
      setMetadataUploadMsg('삭제 실패: ' + (err.response?.data?.error || err.message));
    }
  };

  // 데이터베이스 스키마 버튼 클릭 시마다 최신 메타데이터 불러오기
  const handleShowMetadata = async () => {
    if (!showMetadata) {
      try {
        const response = await axios.get('/api/metadata');
        setMetadata(response.data);
      } catch (error) {
        setMetadata(null);
      }
    }
    setShowMetadata(!showMetadata);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Text2SQL - 고객 데이터 분석</h1>
          <div className="header-buttons">
            <button 
              className="header-button"
              onClick={() => setShowRagManager(true)}
            >
              <FolderOpen size={20} />
              RAG 파일 관리
            </button>
            <button 
              className="header-button"
              onClick={() => setShowRagStats(true)}
            >
              <BarChart3 size={20} />
              RAG 통계
            </button>
            <button 
              className="header-button"
              onClick={handleShowMetadata}
            >
              <Database size={20} />
              데이터베이스 스키마
            </button>
            <button 
              className="header-button"
              onClick={() => setShowPreprocessing(true)}
              disabled={!preprocessingData}
            >
              <Settings size={20} />
              전처리 과정
            </button>
          </div>
        </div>
      </header>

      <div className="main-container">
        {showMetadata && metadata && (
          <div className="metadata-panel">
            <h3>데이터베이스 스키마</h3>
            <div className="metadata-content">
              {Object.entries(metadata.tables).map(([tableName, tableInfo]) => (
                <div key={tableName} className="table-info">
                  <h4>{tableName}</h4>
                  <p className="table-description">{tableInfo.description}</p>
                  <table className="schema-table" style={{ marginBottom: 16, borderCollapse: 'collapse', width: '100%' }}>
                    <thead>
                      <tr style={{ background: '#f0f0f0' }}>
                        <th style={{ padding: 4, border: '1px solid #ddd' }}>컬럼명</th>
                        <th style={{ padding: 4, border: '1px solid #ddd' }}>타입</th>
                        <th style={{ padding: 4, border: '1px solid #ddd' }}>설명</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(tableInfo.columns).map(([colName, colInfo]) => (
                        <tr key={colName}>
                          <td style={{ padding: 4, border: '1px solid #ddd' }}>{colName}</td>
                          <td style={{ padding: 4, border: '1px solid #ddd' }}>{colInfo.type}</td>
                          <td style={{ padding: 4, border: '1px solid #ddd' }}>{colInfo.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="chat-container">
          <div className="messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-avatar">
                  {message.type === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div className="message-content">
                  <div className="message-text">{message.content}</div>
                  {message.sql && (
                    <div className="sql-block">
                      <div className="sql-header">
                        <Code size={16} />
                        <span>생성된 SQL</span>
                        <button 
                          className="copy-button"
                          onClick={() => copyToClipboard(message.sql)}
                        >
                          복사
                        </button>
                      </div>
                      <pre className="sql-code">{message.sql}</pre>
                    </div>
                  )}
                  {message.preprocessing && (
                    <div className="preprocessing-summary">
                      <div className="summary-header">
                        <Settings size={14} />
                        <span>전처리 요약</span>
                      </div>
                      <div className="summary-stats">
                        <span className="stat">도메인 용어: {message.preprocessing.domain_terms_found || 0}개</span>
                        <span className="stat">절 분석: {message.preprocessing.clauses_count || 0}개</span>
                        <span className="stat">추론 단계: {message.preprocessing.reasoning_steps || 0}단계</span>
                      </div>
                    </div>
                  )}
                  <div className="message-timestamp">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message bot">
                <div className="message-avatar">
                  <Bot size={20} />
                </div>
                <div className="message-content">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 상단 메뉴에 메타데이터 업로드/관리 */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 8 }}>
            <div style={{ fontWeight: 600 }}>메타데이터 관리</div>
            <button onClick={() => setShowMetadataUpload(true)} style={{ marginRight: 8 }}>
              <Upload size={16} style={{ marginRight: 4 }} /> 메타데이터 업로드
            </button>
          </div>
          {/* 메타데이터 파일 목록 */}
          <div style={{ padding: 8, background: '#f8f8f8', borderBottom: '1px solid #eee' }}>
            {metadataFiles.length === 0 && <div style={{ color: '#888' }}>업로드된 메타데이터 파일이 없습니다.</div>}
            {metadataFiles.map(f => (
              <div key={f.filename} style={{ display: 'flex', alignItems: 'center', marginBottom: 4, background: activeMeta === f.filename ? '#e0f7fa' : 'transparent', borderRadius: 4, padding: 4 }}>
                <span style={{ fontWeight: activeMeta === f.filename ? 700 : 400 }}>{f.filename}</span>
                <span style={{ fontSize: 12, color: '#888', marginLeft: 8 }}>{new Date(f.upload_date).toLocaleString()}</span>
                {activeMeta === f.filename && <CheckCircle size={16} color="#009688" style={{ marginLeft: 8 }} title="적용중" />}
                <button style={{ marginLeft: 12 }} onClick={() => handleApplyMeta(f.filename)} disabled={activeMeta === f.filename}>적용</button>
                <button style={{ marginLeft: 4 }} onClick={() => handleDeleteMeta(f.filename)}><Trash2 size={16} /></button>
              </div>
            ))}
          </div>
          {/* 메타데이터 업로드 모달/폼 */}
          {showMetadataUpload && (
            <div style={{ background: '#fff', border: '1px solid #ccc', padding: 20, position: 'fixed', top: 80, left: '50%', transform: 'translateX(-50%)', zIndex: 1000 }}>
              <h3>엑셀(xlsx) 메타데이터 업로드</h3>
              <form onSubmit={handleMetadataUpload}>
                <input type="file" accept=".xlsx" ref={fileInputRef} required />
                <button type="submit" style={{ marginLeft: 8 }}>업로드</button>
                <button type="button" style={{ marginLeft: 8 }} onClick={() => setShowMetadataUpload(false)}>취소</button>
              </form>
              <div style={{ marginTop: 8, fontSize: 13, color: '#888' }}>
                예시 포맷: 테이블명 | 컬럼명 | 타입 | 설명 (헤더 필수)
              </div>
            </div>
          )}
          {/* 업로드 결과 메시지 */}
          {metadataUploadMsg && (
            <div style={{ background: '#e0ffe0', color: '#222', padding: 8, margin: 8, borderRadius: 4 }}>{metadataUploadMsg}</div>
          )}
          <form className="input-form" onSubmit={handleSubmit}>
            {/* RAG 도메인 선택 드롭다운 */}
            <select
              value={selectedRagDomain}
              onChange={e => setSelectedRagDomain(e.target.value)}
              style={{ marginRight: 8 }}
            >
              {RAG_DOMAINS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="자연어로 질문을 입력하세요..."
              disabled={isLoading}
              className="message-input"
            />
            <button 
              type="submit" 
              disabled={isLoading || !inputValue.trim()}
              className="send-button"
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
      
      {/* RAG 파일 관리 모달 */}
      <RagFileManager 
        isOpen={showRagManager} 
        onClose={() => setShowRagManager(false)} 
      />
      
      {/* RAG 통계 모달 */}
      <RagStats 
        isOpen={showRagStats} 
        onClose={() => setShowRagStats(false)} 
      />
      
      {/* 전처리 과정 뷰어 */}
      <PreprocessingViewer 
        preprocessingData={preprocessingData}
        isVisible={showPreprocessing}
        onClose={() => setShowPreprocessing(false)}
      />
    </div>
  );
}

export default App; 