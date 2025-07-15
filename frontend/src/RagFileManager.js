import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Trash2, Download, FileText, Folder, Plus, X } from 'lucide-react';
import './RagFileManager.css';

const RagFileManager = ({ isOpen, onClose }) => {
  const [domains, setDomains] = useState({});
  const [selectedDomain, setSelectedDomain] = useState('personal_credit');
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDomains();
      loadFiles(selectedDomain);
    }
  }, [isOpen, selectedDomain]);

  const loadDomains = async () => {
    try {
      const response = await axios.get('/api/rag/domains');
      setDomains(response.data.domains);
    } catch (error) {
      console.error('도메인 로드 실패:', error);
      setError('도메인 정보를 불러오는데 실패했습니다.');
    }
  };

  const loadFiles = async (domain) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/rag/files/${domain}`);
      setFiles(response.data.files);
      setError('');
    } catch (error) {
      console.error('파일 목록 로드 실패:', error);
      setError('파일 목록을 불러오는데 실패했습니다.');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`/api/rag/upload/${selectedDomain}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // 파일 목록 새로고침
      loadFiles(selectedDomain);
      
      // 파일 입력 초기화
      event.target.value = '';
      
    } catch (error) {
      console.error('파일 업로드 실패:', error);
      setError(error.response?.data?.error || '파일 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileDelete = async (filename) => {
    if (!window.confirm(`"${filename}" 파일을 삭제하시겠습니까?`)) {
      return;
    }

    try {
      await axios.delete(`/api/rag/delete/${selectedDomain}/${filename}`);
      loadFiles(selectedDomain);
      setError('');
    } catch (error) {
      console.error('파일 삭제 실패:', error);
      setError(error.response?.data?.error || '파일 삭제에 실패했습니다.');
    }
  };

  const handleFileDownload = async (filename) => {
    try {
      const response = await axios.get(`/api/rag/download/${selectedDomain}/${filename}`);
      
      // 파일 다운로드
      const blob = new Blob([response.data.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('파일 다운로드 실패:', error);
      setError(error.response?.data?.error || '파일 다운로드에 실패했습니다.');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  if (!isOpen) return null;

  return (
    <div className="rag-file-manager-overlay">
      <div className="rag-file-manager">
        <div className="rag-header">
          <h2>RAG 파일 관리</h2>
          <button className="close-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="rag-content">
          {/* 도메인 선택 */}
          <div className="domain-selector">
            <h3>도메인 선택</h3>
            <div className="domain-tabs">
              {Object.entries(domains).map(([key, name]) => (
                <button
                  key={key}
                  className={`domain-tab ${selectedDomain === key ? 'active' : ''}`}
                  onClick={() => setSelectedDomain(key)}
                >
                  <Folder size={16} />
                  {name}
                </button>
              ))}
            </div>
          </div>

          {/* 파일 업로드 */}
          <div className="file-upload-section">
            <h3>파일 업로드</h3>
            <div className="upload-area">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileUpload}
                accept=".txt,.pdf,.docx,.doc,.csv,.json,.md"
                disabled={uploading}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" className="upload-button">
                {uploading ? (
                  <div className="uploading">
                    <div className="spinner"></div>
                    업로드 중...
                  </div>
                ) : (
                  <>
                    <Upload size={20} />
                    파일 선택
                  </>
                )}
              </label>
              <p className="upload-hint">
                지원 형식: TXT, PDF, DOCX, DOC, CSV, JSON, MD
              </p>
            </div>
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* 파일 목록 */}
          <div className="file-list-section">
            <h3>업로드된 파일</h3>
            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                파일 목록을 불러오는 중...
              </div>
            ) : files.length === 0 ? (
              <div className="empty-state">
                <FileText size={48} />
                <p>업로드된 파일이 없습니다.</p>
                <p>위에서 파일을 업로드해주세요.</p>
              </div>
            ) : (
              <div className="file-list">
                {files.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <div className="file-name">{file.filename}</div>
                      <div className="file-details">
                        <span>{formatFileSize(file.size)}</span>
                        <span>•</span>
                        <span>{formatDate(file.upload_date)}</span>
                      </div>
                    </div>
                    <div className="file-actions">
                      <button
                        className="action-button download"
                        onClick={() => handleFileDownload(file.filename)}
                        title="다운로드"
                      >
                        <Download size={16} />
                      </button>
                      <button
                        className="action-button delete"
                        onClick={() => handleFileDelete(file.filename)}
                        title="삭제"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RagFileManager; 