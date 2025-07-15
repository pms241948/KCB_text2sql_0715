import React from 'react';
import { ChevronDown, ChevronRight, Code, Database, Search, Brain, Layers, Target, FileText, Hash, Calendar, User, TrendingUp } from 'lucide-react';
import './PreprocessingViewer.css';

const PreprocessingViewer = ({ preprocessingData, isVisible, onClose }) => {
  const [expandedSections, setExpandedSections] = React.useState({
    normalization: true,
    entities: true,
    clauses: true,
    reasoning: true,
    sqlMappings: true
  });

  // 안전한 렌더링을 위한 헬퍼 함수
  const safeRender = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (!isVisible || !preprocessingData) return null;

  const { 
    original_query, 
    normalized_query, 
    mapped_query, 
    entities, 
    clauses, 
    reasoning_chain, 
    sql_mappings,
    preprocessing_metadata 
  } = preprocessingData;

  const renderEntity = (entity, index) => {
    const getEntityIcon = (type) => {
      switch (type) {
        case 'credit_score': return <Hash size={14} />;
        case 'customer_type': return <User size={14} />;
        case 'risk_level': return <TrendingUp size={14} />;
        case 'date_range': return <Calendar size={14} />;
        default: return <Target size={14} />;
      }
    };

    return (
      <div key={index} className="entity-item">
        <div className="entity-header">
          {getEntityIcon(entity.type || 'domain')}
          <span className="entity-term">{entity.term || entity.value}</span>
          {entity.category && <span className="entity-category">{entity.category}</span>}
        </div>
        {entity.sql_mapping && (
          <div className="entity-mapping">
            <span className="mapping-label">SQL 매핑:</span>
            <code>{entity.sql_mapping}</code>
          </div>
        )}
        {entity.table && (
          <div className="entity-table">
            <span className="table-label">테이블:</span>
            <code>{entity.table}</code>
          </div>
        )}
      </div>
    );
  };

  const renderClause = (clause, index) => {
    // confidence 값 안전하게 처리
    const confidence = clause.confidence;
    const confidenceText = confidence !== null && confidence !== undefined && !isNaN(confidence) 
      ? `${Math.round(confidence * 100)}%` 
      : 'N/A';

    return (
      <div key={index} className="clause-item">
        <div className="clause-header">
          <span className="clause-type">{safeRender(clause.type)}</span>
          <span className="clause-confidence">{confidenceText}</span>
        </div>
        <div className="clause-content">
          {safeRender(clause.content)}
        </div>
        {clause.keywords && clause.keywords.length > 0 && (
          <div className="clause-keywords">
            <span className="keywords-label">키워드:</span>
            {clause.keywords.map((keyword, idx) => (
              <span key={idx} className="keyword-tag">{safeRender(keyword)}</span>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderReasoningStep = (step, index) => {
    return (
      <div key={index} className="reasoning-step">
        <div className="step-number">{index + 1}</div>
        <div className="step-content">
          {safeRender(step)}
        </div>
      </div>
    );
  };

  return (
    <div className="preprocessing-viewer">
      <div className="preprocessing-header">
        <h3>🔧 자연어 전처리 과정</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      <div className="preprocessing-content">
        {/* 원본 질문 */}
        <div className="section">
          <div className="section-header">
            <FileText size={16} />
            <span>원본 질문</span>
          </div>
                  <div className="section-content">
          <div className="original-query">
            {safeRender(original_query)}
          </div>
        </div>
        </div>

        {/* 텍스트 정규화 */}
        <div className="section">
          <div 
            className="section-header clickable"
            onClick={() => toggleSection('normalization')}
          >
            {expandedSections.normalization ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Layers size={16} />
            <span>텍스트 정규화</span>
          </div>
          {expandedSections.normalization && (
            <div className="section-content">
              <div className="normalization-item">
                <span className="label">정규화된 질문:</span>
                <div className="normalized-text">
                  {safeRender(normalized_query)}
                </div>
              </div>
              <div className="normalization-item">
                <span className="label">도메인 매핑된 질문:</span>
                <div className="mapped-text">
                  {safeRender(mapped_query)}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 엔티티 추출 */}
        <div className="section">
          <div 
            className="section-header clickable"
            onClick={() => toggleSection('entities')}
          >
            {expandedSections.entities ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Target size={16} />
            <span>엔티티 추출 ({preprocessing_metadata?.domain_terms_found || 0}개)</span>
          </div>
          {expandedSections.entities && (
            <div className="section-content">
              {entities?.domain_terms && entities.domain_terms.length > 0 && (
                <div className="entity-group">
                  <h4>도메인 용어</h4>
                  <div className="entity-list">
                    {entities.domain_terms.map(renderEntity)}
                  </div>
                </div>
              )}
              {entities?.numeric_values && entities.numeric_values.length > 0 && (
                <div className="entity-group">
                  <h4>숫자 값</h4>
                  <div className="entity-list">
                    {entities.numeric_values.map(renderEntity)}
                  </div>
                </div>
              )}
              {entities?.customer_types && entities.customer_types.length > 0 && (
                <div className="entity-group">
                  <h4>고객 유형</h4>
                  <div className="entity-list">
                    {entities.customer_types.map((type, idx) => (
                      <div key={idx} className="entity-item">
                        <User size={14} />
                        <span>{type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 절 분석 */}
        <div className="section">
          <div 
            className="section-header clickable"
            onClick={() => toggleSection('clauses')}
          >
            {expandedSections.clauses ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Search size={16} />
            <span>절 분석 ({preprocessing_metadata?.clauses_count || 0}개)</span>
          </div>
          {expandedSections.clauses && (
            <div className="section-content">
              <div className="clause-list">
                {clauses?.map(renderClause)}
              </div>
            </div>
          )}
        </div>

        {/* 추론 과정 */}
        <div className="section">
          <div 
            className="section-header clickable"
            onClick={() => toggleSection('reasoning')}
          >
            {expandedSections.reasoning ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Brain size={16} />
            <span>추론 과정 ({preprocessing_metadata?.reasoning_steps || 0}단계)</span>
          </div>
          {expandedSections.reasoning && (
            <div className="section-content">
              <div className="reasoning-chain">
                {reasoning_chain?.map(renderReasoningStep)}
              </div>
            </div>
          )}
        </div>

        {/* SQL 패턴 매핑 */}
        <div className="section">
          <div 
            className="section-header clickable"
            onClick={() => toggleSection('sqlMappings')}
          >
            {expandedSections.sqlMappings ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Code size={16} />
            <span>SQL 패턴 매핑 ({preprocessing_metadata?.sql_patterns_mapped || 0}개)</span>
          </div>
          {expandedSections.sqlMappings && (
            <div className="section-content">
              <div className="sql-mappings">
                {sql_mappings && Object.entries(sql_mappings).map(([pattern, mapping], index) => (
                  <div key={index} className="sql-mapping-item">
                    <div className="mapping-pattern">
                      <span className="pattern-label">패턴:</span>
                      <code>{pattern}</code>
                    </div>
                    <div className="mapping-result">
                      <span className="result-label">매핑:</span>
                      <code>
                        {safeRender(mapping)}
                      </code>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 전처리 통계 */}
        <div className="section">
          <div className="section-header">
            <Database size={16} />
            <span>전처리 통계</span>
          </div>
          <div className="section-content">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">도메인 용어</span>
                <span className="stat-value">{preprocessing_metadata?.domain_terms_found || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">절 개수</span>
                <span className="stat-value">{preprocessing_metadata?.clauses_count || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">추론 단계</span>
                <span className="stat-value">{preprocessing_metadata?.reasoning_steps || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">SQL 패턴</span>
                <span className="stat-value">{preprocessing_metadata?.sql_patterns_mapped || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreprocessingViewer; 