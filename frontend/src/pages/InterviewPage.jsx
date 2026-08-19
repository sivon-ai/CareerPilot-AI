import { AlertCircle, ArrowRight, CheckCircle2, Loader2, RefreshCcw, Sparkles, Target } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getDocuments, getFriendlyApiError, getInterviewReport } from '../services/api';
import { useInterview } from '../hooks/useInterview';

const interviewTypes = ['Technical', 'AI/GenAI', 'Behavioral', 'Resume-based', 'Mixed'];
const difficulties = ['Easy', 'Medium', 'Hard'];
const questionCounts = [5, 10, 15];

const normalizeDocument = (item) => {
  if (!item || typeof item !== 'object') return null;
  const documentType = (item.document_type || item.type || 'other').toString().trim().toLowerCase();
  return {
    id: item.document_id || item.id || item.filename || crypto.randomUUID(),
    filename: item.filename || 'Unnamed document',
    status: item.status || 'indexed',
    documentType,
  };
};

const InterviewSetup = ({ resumes, jobs, selectedResumeId, setSelectedResumeId, selectedJobId, setSelectedJobId, interviewType, setInterviewType, difficulty, setDifficulty, questionCount, setQuestionCount, onStart, loading, error }) => (
  <section className="interview-shell">
    <div className="interview-card setup-card">
      <p className="eyebrow accent">AI Interviewer</p>
      <h1>Practice a personalized interview based on your resume and target role.</h1>
      <div className="form-grid">
        <label className="field">
          <span>Resume</span>
          <select value={selectedResumeId} onChange={(event) => setSelectedResumeId(event.target.value)}>
            <option value="">Select Resume</option>
            {resumes.map((document) => (
              <option key={document.id} value={document.id}>{document.filename}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Job Description</span>
          <select value={selectedJobId} onChange={(event) => setSelectedJobId(event.target.value)}>
            <option value="">Select Job Description</option>
            {jobs.map((document) => (
              <option key={document.id} value={document.id}>{document.filename}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Interview Type</span>
          <select value={interviewType} onChange={(event) => setInterviewType(event.target.value)}>
            {interviewTypes.map((option) => (
              <option key={option} value={option.toLowerCase().replace(/\s+/g, '_')}>{option}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Difficulty</span>
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
            {difficulties.map((option) => (
              <option key={option} value={option.toLowerCase()}>{option}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Number of Questions</span>
          <select value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))}>
            {questionCounts.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </label>
      </div>

      {error ? (
        <div className="inline-message inline-message--error" role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      ) : null}

      <button type="button" className="primary-btn interview-start" onClick={onStart} disabled={loading}>
        {loading ? <><Loader2 size={16} className="spin" />Starting...</> : 'Start Interview'}
      </button>
    </div>
  </section>
);

const InterviewSession = ({ question, questionNumber, totalQuestions, answer, setAnswer, evaluation, submitting, onSubmit, error, onRetry, completed, onViewReport, reportLoading }) => (
  <section className="interview-shell">
    <div className="interview-card session-card">
      <div className="session-header">
        <div>
          <p className="eyebrow accent">AI Interviewer</p>
          <h2>Question {questionNumber} of {totalQuestions}</h2>
        </div>
        <div className="progress-pill">{question?.category || 'Mixed'} • {question?.difficulty || 'medium'}</div>
      </div>

      <div className="progress-line" aria-label="Interview progress">
        <span style={{ width: `${((questionNumber - 1) / Math.max(totalQuestions, 1)) * 100}%` }} />
      </div>

      <div className="question-card">
        <div className="question-meta">
          <span>{question?.category || 'Mixed'}</span>
          <span>{question?.difficulty || 'medium'}</span>
          {question?.skill ? <span>Skill: {question.skill}</span> : null}
        </div>
        <h3>{question?.text || 'Loading question...'}</h3>
      </div>

      <label className="answer-label" htmlFor="interview-answer">Your answer</label>
      <textarea
        id="interview-answer"
        value={answer}
        onChange={(event) => setAnswer(event.target.value)}
        placeholder="Type your answer here..."
        rows={8}
        disabled={submitting}
      />

      {error ? (
        <div className="inline-message inline-message--error" role="alert">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      ) : null}

      <div className="session-actions">
        <button type="button" className="primary-btn" onClick={onSubmit} disabled={submitting || !answer.trim()}>
          {submitting ? <><Loader2 size={16} className="spin" />Evaluating...</> : 'Submit Answer'}
        </button>
      </div>

      {evaluation && !completed ? (
        <div className="evaluation-panel">
          <div className="score-box">
            <p>Your Score</p>
            <h3>{Number(evaluation.overall_score || 0).toFixed(1)} / 10</h3>
          </div>

          <div className="dimension-grid">
            <div><span>Correctness</span><strong>{Number(evaluation.correctness || 0).toFixed(1)}/10</strong></div>
            <div><span>Relevance</span><strong>{Number(evaluation.relevance || 0).toFixed(1)}/10</strong></div>
            <div><span>Depth</span><strong>{Number(evaluation.depth || 0).toFixed(1)}/10</strong></div>
            <div><span>Clarity</span><strong>{Number(evaluation.clarity || 0).toFixed(1)}/10</strong></div>
          </div>

          <div className="feedback-grid">
            <div>
              <h4>What you did well</h4>
              <ul>
                {(evaluation.strengths || []).map((item) => <li key={item}><CheckCircle2 size={14} />{item}</li>)}
              </ul>
            </div>
            <div>
              <h4>How to improve</h4>
              <ul>
                {(evaluation.improvements || []).map((item) => <li key={item}><Sparkles size={14} />{item}</li>)}
              </ul>
            </div>
          </div>

          <div className="session-actions">
            {onRetry ? <button type="button" className="secondary-btn" onClick={onRetry}><RefreshCcw size={16} />Try Again</button> : null}
            {completed ? <button type="button" className="primary-btn" onClick={onViewReport}>{reportLoading ? 'Loading...' : 'View Interview Report'}</button> : null}
          </div>
        </div>
      ) : null}

      {completed ? (
        <div className="completion-panel">
          <h3>Interview Complete</h3>
          <p>You’ve completed {totalQuestions} questions.</p>
          <button type="button" className="primary-btn" onClick={onViewReport}>{reportLoading ? 'Loading...' : 'View Interview Report'}</button>
        </div>
      ) : null}
    </div>
  </section>
);

const InterviewReportPage = ({ sessionId, onBack }) => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const payload = await getInterviewReport(sessionId);
        setReport(payload);
      } catch (fetchError) {
        setError(getFriendlyApiError(fetchError));
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [sessionId]);

  if (loading) {
    return <div className="interview-shell"><div className="interview-card"><p>Loading interview report...</p></div></div>;
  }

  if (error) {
    return <div className="interview-shell"><div className="interview-card"><p className="error-copy">{error}</p><button type="button" className="secondary-btn" onClick={onBack}>Back to interview</button></div></div>;
  }

  if (!report) return null;

  return (
    <div className="interview-shell">
      <div className="interview-card report-card">
        <p className="eyebrow accent">Interview Complete</p>
        <h1>{report.overall_score} / 100</h1>
        <p className="report-summary">{report.questions_answered} questions answered</p>

        <div className="category-grid">
          {Object.entries(report.category_scores || {}).map(([label, value]) => (
            <div key={label} className="category-box">
              <span>{label.replace('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase())}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>

        {report.strengths?.length ? (
          <div className="report-section">
            <h3>Strengths</h3>
            <ul>
              {report.strengths.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        ) : null}

        {report.weaknesses?.length ? (
          <div className="report-section">
            <h3>Areas to improve</h3>
            <ul>
              {report.weaknesses.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        ) : null}

        {report.recommendations?.length ? (
          <div className="report-section">
            <h3>Recommended preparation</h3>
            <ol>
              {report.recommendations.map((item, index) => <li key={item}>{index + 1}. {item}</li>)}
            </ol>
          </div>
        ) : null}

        <div className="report-section">
          <h3>Question History</h3>
          <div className="history-list">
            {(report.question_results || []).map((result, index) => (
              <div key={result.question_id || index} className="history-item">
                <div>
                  <span>Q{index + 1}</span>
                  <strong>{result.question_id || `Question ${index + 1}`}</strong>
                </div>
                <strong>{result.score}/10</strong>
              </div>
            ))}
          </div>
        </div>

        <button type="button" className="secondary-btn" onClick={onBack}>Practice Again</button>
      </div>
    </div>
  );
};

const InterviewPage = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [interviewType, setInterviewType] = useState('mixed');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(10);
  const [reportSessionId, setReportSessionId] = useState('');
  const [reportVisible, setReportVisible] = useState(false);
  const [setupError, setSetupError] = useState('');

  const interview = useInterview();

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const payload = await getDocuments();
        setDocuments((payload || []).map(normalizeDocument).filter(Boolean));
      } catch (loadError) {
        setSetupError(getFriendlyApiError(loadError));
      }
    };

    loadDocuments();
  }, []);

  const resumes = useMemo(() => documents.filter((document) => document.status === 'indexed' && (document.documentType === 'resume' || document.documentType === 'other')), [documents]);
  const jobs = useMemo(() => documents.filter((document) => document.status === 'indexed' && (document.documentType === 'job_description' || document.documentType === 'other')), [documents]);

  const startInterview = async () => {
    if (!selectedResumeId) {
      setSetupError('Please select a resume.');
      return;
    }
    if (!selectedJobId) {
      setSetupError('Please select a job description.');
      return;
    }

    setSetupError('');
    try {
      const payload = await interview.start({
        resumeDocumentId: selectedResumeId,
        jobDocumentId: selectedJobId,
        interviewType,
        difficulty,
        questionCount,
      });
      setReportVisible(false);
      setReportSessionId(payload.session_id);
    } catch (startError) {
      setSetupError(getFriendlyApiError(startError));
    }
  };

  const handleSubmit = async () => {
    try {
      await interview.submitAnswer();
      if (interview.completed) {
        setReportSessionId(interview.session?.session_id || reportSessionId);
        setReportVisible(true);
      }
    } catch (submitError) {
      // handled by hook
    }
  };

  const onViewReport = async () => {
    if (interview.session?.session_id) {
      setReportSessionId(interview.session.session_id);
    }
    setReportVisible(true);
  };

  const showSetup = !interview.session || reportVisible;

  if (reportVisible && reportSessionId) {
    return <InterviewReportPage sessionId={reportSessionId} onBack={() => { setReportVisible(false); interview.reset(); setSelectedResumeId(''); setSelectedJobId(''); }} />;
  }

  if (showSetup) {
    return (
      <InterviewSetup
        resumes={resumes}
        jobs={jobs}
        selectedResumeId={selectedResumeId}
        setSelectedResumeId={setSelectedResumeId}
        selectedJobId={selectedJobId}
        setSelectedJobId={setSelectedJobId}
        interviewType={interviewType}
        setInterviewType={setInterviewType}
        difficulty={difficulty}
        setDifficulty={setDifficulty}
        questionCount={questionCount}
        setQuestionCount={setQuestionCount}
        onStart={startInterview}
        loading={interview.loading}
        error={setupError || interview.error}
      />
    );
  }

  return (
    <InterviewSession
      question={interview.currentQuestion}
      questionNumber={interview.questionNumber}
      totalQuestions={interview.totalQuestions}
      answer={interview.answer}
      setAnswer={interview.setAnswer}
      evaluation={interview.evaluation}
      submitting={interview.submitting}
      onSubmit={handleSubmit}
      error={interview.error}
      onRetry={() => {
        interview.setAnswer(interview.answer);
      }}
      completed={interview.completed}
      onViewReport={onViewReport}
      reportLoading={false}
    />
  );
};

export default InterviewPage;
