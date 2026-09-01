import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Activity, 
  Clock, 
  Lock, 
  FileText, 
  Trash2, 
  Upload, 
  Play, 
  HelpCircle, 
  AlertCircle, 
  CheckCircle, 
  Search 
} from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const SAMPLE_RECORD = `PATIENT RECORD - RESTRICTED ACCESS
Date: 2026-08-11
Patient: John Doe, Age: 45 years old
Aadhaar: 1234-5678-9012, PAN: ABCDE1234F
Contact: 9876543210
Email: johndoe.patient@gmail.com
Hospital: City General Hospital
Doctor: Dr. Alice Smith
Patient ID: PID-98765

Chief Complaint:
Patient John Doe visited the clinic complaining of a persistent cough, mild fever, and shortness of breath for 4 days.

History of Present Illness:
Patient is a 45 yo male. History of mild seasonal asthma. Reports that symptoms started after exposure to dust.

Clinical Assessment & Diagnosis:
Upon examination by Dr. Alice Smith at City General Hospital, chest wheezing was noted. O2 saturation was 96%.
Diagnosis: Acute Bronchitis secondary to asthma exacerbation.

Treatment Plan:
1. Albuterol inhaler (2 puffs every 4-6 hours as needed).
2. Amoxicillin 500mg capsules (1 capsule three times daily for 7 days).
3. Advised to stay hydrated and rest.

Follow-up:
Advised John Doe to return to City General Hospital for follow-up in 7 days or report immediately if breathing difficulties worsen.`;

function App() {
  // Input State
  const [medicalText, setMedicalText] = useState('');
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);

  // Status and API Loading State
  const [apiOnline, setApiOnline] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAnswering, setIsAnswering] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Processed Output State
  const [originalText, setOriginalText] = useState('');
  const [deidentifiedText, setDeidentifiedText] = useState('');
  const [entities, setEntities] = useState([]);
  const [summary, setSummary] = useState('');
  const [processingTimeMs, setProcessingTimeMs] = useState(0);
  const [privacyStatus, setPrivacyStatus] = useState('Pending');
  const [activeTab, setActiveTab] = useState('Original');

  // QA Feature State
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [qaError, setQaError] = useState('');

  // Suggested Questions list
  const suggestedQuestions = [
    'What was the diagnosis?',
    'What symptoms were reported?',
    'What medications were prescribed?',
    'What investigations were abnormal?',
    'What medical history was mentioned?',
    'What follow-up was advised?',
    'Summarize this case in 3 lines.'
  ];

  // Monitor word and character count on text change
  useEffect(() => {
    setCharCount(medicalText.length);
    const words = medicalText.trim().split(/\s+/).filter(Boolean);
    setWordCount(words.length);
  }, [medicalText]);

  // Check API Server status on load and periodically
  const checkApiStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        setApiOnline(data.status === 'online');
      } else {
        setApiOnline(false);
      }
    } catch {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    checkApiStatus();
    const interval = setInterval(checkApiStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle Loading Sample
  const handleLoadSample = () => {
    setMedicalText(SAMPLE_RECORD);
    setErrorMessage('');
  };

  // Handle Clearing State
  const handleClear = () => {
    setMedicalText('');
    setOriginalText('');
    setDeidentifiedText('');
    setEntities([]);
    setSummary('');
    setProcessingTimeMs(0);
    setPrivacyStatus('Pending');
    setActiveTab('Original');
    setQuestion('');
    setAnswer('');
    setErrorMessage('');
    setQaError('');
  };

  // File Upload handler
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
      setErrorMessage('Unsupported file type. Please upload a .txt file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setMedicalText(event.target.result);
      setErrorMessage('');
    };
    reader.readAsText(file);
  };

  // Call Process Record API
  const handleProcessRecord = async () => {
    if (!medicalText.trim()) {
      setErrorMessage('Please type/paste clinical text or upload a document first.');
      return;
    }

    setIsProcessing(true);
    setErrorMessage('');
    setAnswer('');
    setQuestion('');

    try {
      const res = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: medicalText })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to process clinical text.');
      }

      const data = await res.json();
      setOriginalText(data.original_text);
      setDeidentifiedText(data.deidentified_text);
      setEntities(data.entities);
      setSummary(data.summary);
      setProcessingTimeMs(data.processing_time_ms);
      setPrivacyStatus(data.privacy_status);
      setActiveTab('De-Identified'); // Shift focus to the de-identified tab
    } catch (err) {
      setErrorMessage(err.message || 'API Server Offline. Start backend on port 8000.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Call Ask Question API
  const handleAskQuestion = async (customQ = '') => {
    const qText = customQ || question;
    if (!qText.trim()) {
      setQaError('Please enter or select a question.');
      return;
    }
    if (!deidentifiedText.trim()) {
      setQaError('De-identified text reference is missing. Process a record first.');
      return;
    }

    setIsAnswering(true);
    setQaError('');
    setAnswer('');

    try {
      const res = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: deidentifiedText, // Send ONLY the de-identified text
          question: qText
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Q&A inference failed.');
      }

      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      setQaError(err.message || 'Inference engine failed to respond.');
    } finally {
      setIsAnswering(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
    handleAskQuestion(suggestion);
  };

  // Highlight de-identified tags inline
  const renderDeidentifiedTextMarkup = (text) => {
    if (!text) return <div className="empty-state">No clinical text de-identified yet.</div>;
    const regex = /(\[[A-Z_]+\])/g;
    const parts = text.split(regex);
    return (
      <div style={{ wordBreak: 'break-word' }}>
        {parts.map((part, index) => {
          if (part.match(regex)) {
            return (
              <span key={index} className="entity-badge-inline">
                {part}
              </span>
            );
          }
          return part;
        })}
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">🛡️</div>
          <div className="brand-details">
            <h1>CareText</h1>
            <p>PRIVATE CLINICAL TEXT INTELLIGENCE</p>
          </div>
        </div>
        <div className={`status-pill ${apiOnline ? 'online' : 'offline'}`}>
          <div className="status-dot"></div>
          {apiOnline ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="dashboard-grid">
        {/* Left Hand Card: Clinical Workspace Input */}
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">
              <FileText size={18} />
              Clinical Note Workspace
            </h2>
            <div className="workspace-controls">
              <button className="btn btn-secondary" onClick={handleLoadSample} disabled={isProcessing}>
                Load Sample
              </button>
              <div className="upload-btn-wrapper">
                <button className="btn btn-secondary" disabled={isProcessing}>
                  <Upload size={14} />
                  Upload TXT
                </button>
                <input type="file" accept=".txt" onChange={handleFileUpload} disabled={isProcessing} />
              </div>
              <button className="btn btn-danger" onClick={handleClear} disabled={isProcessing}>
                <Trash2 size={14} />
                Clear
              </button>
            </div>
          </div>

          {errorMessage && (
            <div className="error-banner">
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="textarea-container">
            <textarea
              className="textarea-workspace"
              placeholder="Paste clinical notes or load a sample record here..."
              value={medicalText}
              onChange={(e) => setMedicalText(e.target.value)}
              disabled={isProcessing}
            ></textarea>
          </div>

          <div className="workspace-stats">
            <span>{charCount} Characters</span>
            <span>{wordCount} Words</span>
          </div>

          <button 
            className="btn btn-primary" 
            onClick={handleProcessRecord} 
            disabled={isProcessing || !medicalText.trim()}
            style={{ width: '100%', padding: '0.8rem' }}
          >
            <Play size={16} />
            {isProcessing ? 'Processing Clinical Engine...' : 'Process Clinical Record'}
          </button>
        </section>

        {/* Right Hand Card: Results Dashboard & Tabs */}
        <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Summary Metric Mini Cards */}
          <div className="results-summary-cards">
            <div className="summary-mini-card">
              <span className="mini-card-label">PHI Detected</span>
              <span className="mini-card-val phi-detected">{entities.length} Entities</span>
            </div>
            <div className="summary-mini-card">
              <span className="mini-card-label">Clean Word Count</span>
              <span className="mini-card-val">
                {deidentifiedText ? deidentifiedText.trim().split(/\s+/).filter(Boolean).length : 0} Words
              </span>
            </div>
            <div className="summary-mini-card">
              <span className="mini-card-label">Processing Time</span>
              <span className="mini-card-val">{processingTimeMs} ms</span>
            </div>
            <div className="summary-mini-card">
              <span className="mini-card-label">Privacy Status</span>
              <span className={`mini-card-val ${deidentifiedText ? 'secure' : ''}`}>
                {deidentifiedText ? 'SECURE' : 'PENDING'}
              </span>
            </div>
          </div>

          {/* Tab Selection Header */}
          <nav className="tabs-header">
            {['Original', 'De-Identified', 'Detected PHI', 'Medical Summary', 'Ask CareText'].map((tab) => (
              <button
                key={tab}
                className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </nav>

          {/* Dynamic Tab Render Panels */}
          {isProcessing ? (
            <div className="loading-wrapper">
              <div className="loading-spinner"></div>
              <span className="loading-text">Anonymizing PHI and summarizing text...</span>
            </div>
          ) : (
            <>
              {/* Tab 1: Original Text */}
              {activeTab === 'Original' && (
                <div className="tab-content-panel">
                  {originalText || (
                    <div className="empty-state">
                      <HelpCircle className="empty-state-icon" />
                      <span>Original clinical text will be loaded here.</span>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: De-identified Text */}
              {activeTab === 'De-Identified' && (
                <div className="tab-content-panel">
                  {renderDeidentifiedTextMarkup(deidentifiedText)}
                </div>
              )}

              {/* Tab 3: Detected PHI Entity Grid */}
              {activeTab === 'Detected PHI' && (
                <div className="tab-content-panel">
                  {entities.length === 0 ? (
                    <div className="empty-state">
                      <CheckCircle className="empty-state-icon" style={{ color: 'var(--color-emerald)' }} />
                      <span>No Protected Health Information (PHI) detected.</span>
                    </div>
                  ) : (
                    <div className="entity-list-grid">
                      {entities.map((ent, idx) => (
                        <div className="entity-row" key={idx}>
                          <div className="entity-meta-left">
                            <span className={`entity-label-pill ${ent.entity_type.toLowerCase()}`}>
                              {ent.entity_type}
                            </span>
                            <span className="entity-original-val">{ent.text}</span>
                          </div>
                          <span className="entity-conf-badge">
                            {(ent.confidence * 100).toFixed(0)}% Match (index {ent.start}-{ent.end})
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: Medical Summary */}
              {activeTab === 'Medical Summary' && (
                <div className="tab-content-panel">
                  {summary ? (
                    <div>
                      <div className="privacy-badge">
                        <span className="privacy-badge-icon">🔒</span>
                        <span>
                          <strong>De-identified before AI processing</strong>
                          <br />
                          AI analysis is performed using the de-identified version of the medical text.
                        </span>
                      </div>
                      <div style={{ padding: '0.5rem 0' }}>{summary}</div>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <HelpCircle className="empty-state-icon" />
                      <span>Medical summary will render after processing clinical records.</span>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 5: Ask CareText Q&A System */}
              {activeTab === 'Ask CareText' && (
                <div className="tab-content-panel">
                  <div className="privacy-badge" style={{ marginBottom: '1.25rem' }}>
                    <span className="privacy-badge-icon">🔒</span>
                    <span>
                      <strong>De-identified before AI processing</strong>
                      <br />
                      AI analysis is performed using the de-identified version of the medical text.
                    </span>
                  </div>

                  {qaError && (
                    <div className="error-banner" style={{ margin: '0 0 1rem 0' }}>
                      <AlertCircle size={16} />
                      <span>{qaError}</span>
                    </div>
                  )}

                  <div className="suggestions-header">SUGGESTED CLINICAL QUESTIONS</div>
                  <div className="suggestions-grid">
                    {suggestedQuestions.map((s, idx) => (
                      <button
                        key={idx}
                        className="suggestion-chip"
                        onClick={() => handleSuggestionClick(s)}
                        disabled={!deidentifiedText || isAnswering}
                      >
                        {s}
                      </button>
                    ))}
                  </div>

                  <div className="qa-input-wrapper">
                    <input
                      type="text"
                      className="qa-text-input"
                      placeholder={
                        deidentifiedText 
                          ? "Type your clinical query here..." 
                          : "Please process a clinical note first..."
                      }
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      disabled={!deidentifiedText || isAnswering}
                    />
                    <button
                      className="btn btn-primary"
                      onClick={() => handleAskQuestion()}
                      disabled={!deidentifiedText || isAnswering || !question.trim()}
                    >
                      <Search size={16} />
                      {isAnswering ? 'Searching...' : 'Ask'}
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={() => { setQuestion(''); setAnswer(''); setQaError(''); }}
                      disabled={isAnswering}
                    >
                      Clear
                    </button>
                  </div>

                  {isAnswering && (
                    <div className="loading-wrapper" style={{ padding: '2rem 0' }}>
                      <div className="loading-spinner" style={{ width: '36px', height: '36px' }}></div>
                      <span className="loading-text" style={{ fontSize: '0.85rem' }}>Analyzing medical record...</span>
                    </div>
                  )}

                  {answer && !isAnswering && (
                    <div className="qa-answer-card">
                      <div className="qa-answer-header">CareText Intelligence Answer</div>
                      <div className="qa-answer-body">{answer}</div>
                    </div>
                  )}

                  {!deidentifiedText && (
                    <div className="empty-state" style={{ padding: '2rem 0' }}>
                      <span>Q&A is locked. You must process a clinical record first.</span>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
