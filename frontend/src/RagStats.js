import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart3, Database, FileText, TrendingUp, X } from 'lucide-react';
import './RagStats.css';

const RagStats = ({ isOpen, onClose }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadStats();
    }
  }, [isOpen, selectedDomain]);

  const loadStats = async () => {
    setLoading(true);
    setError('');
    
    try {
      const url = selectedDomain 
        ? `/api/rag/stats?domain=${selectedDomain}`
        : '/api/rag/stats';
      
      const response = await axios.get(url);
      setStats(response.data);
    } catch (error) {
      console.error('통계 로드 실패:', error);
      setError('통계 정보를 불러오는데 실패했습니다.');
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return num.toLocaleString('ko-KR');
  };

  if (!isOpen) return null;

  return (
    <div className="rag-stats-overlay">
      <div className="rag-stats">
        <div className="stats-header">
          <h2>
            <BarChart3 size={24} />
            RAG 데이터베이스 통계
          </h2>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="stats-content">
          {/* 도메인 선택 */}
          <div className="domain-selector">
            <label>도메인 선택:</label>
            <select 
              value={selectedDomain} 
              onChange={(e) => setSelectedDomain(e.target.value)}
            >
              <option value="">전체 도메인</option>
              <option value="personal_credit">개인 신용정보</option>
              <option value="corporate_credit">기업 신용정보</option>
              <option value="policy_regulation">평가 정책 및 규제</option>
            </select>
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* 로딩 상태 */}
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              통계를 불러오는 중...
            </div>
          )}

          {/* 통계 정보 */}
          {stats && !loading && (
            <div className="stats-info">
              {selectedDomain ? (
                // 특정 도메인 통계
                <div className="domain-stats">
                  <div className="stat-card">
                    <div className="stat-icon">
                      <Database size={24} />
                    </div>
                    <div className="stat-content">
                      <h3>도메인</h3>
                      <p className="stat-value">{stats.domain}</p>
                    </div>
                  </div>
                  
                  <div className="stat-card">
                    <div className="stat-icon">
                      <FileText size={24} />
                    </div>
                    <div className="stat-content">
                      <h3>총 청크 수</h3>
                      <p className="stat-value">{formatNumber(stats.total_chunks)}</p>
                    </div>
                  </div>
                  
                  <div className="stat-card">
                    <div className="stat-icon">
                      <TrendingUp size={24} />
                    </div>
                    <div className="stat-content">
                      <h3>컬렉션</h3>
                      <p className="stat-value">{stats.collection_name}</p>
                    </div>
                  </div>
                </div>
              ) : (
                // 전체 통계
                <div className="overall-stats">
                  <div className="stat-card main">
                    <div className="stat-icon">
                      <Database size={32} />
                    </div>
                    <div className="stat-content">
                      <h3>전체 청크 수</h3>
                      <p className="stat-value large">{formatNumber(stats.total_chunks)}</p>
                    </div>
                  </div>
                  
                  <div className="domain-breakdown">
                    <h3>도메인별 청크 수</h3>
                    <div className="domain-stats-grid">
                      {Object.entries(stats.domain_stats || {}).map(([domain, count]) => (
                        <div key={domain} className="domain-stat-item">
                          <div className="domain-name">
                            {domain === 'personal_credit' && '개인 신용정보'}
                            {domain === 'corporate_credit' && '기업 신용정보'}
                            {domain === 'policy_regulation' && '평가 정책 및 규제'}
                          </div>
                          <div className="domain-count">{formatNumber(count)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 새로고침 버튼 */}
          <div className="stats-actions">
            <button 
              className="refresh-button"
              onClick={loadStats}
              disabled={loading}
            >
              새로고침
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RagStats; 