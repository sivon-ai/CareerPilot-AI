import { AlertCircle, ArrowRight, BriefcaseBusiness, CheckCircle2, FileText, Loader2, RefreshCw, Sparkles, TriangleAlert } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { useJobMatcher } from '../hooks/useJobMatcher.js';

const getMatchLabel = (score) => {
  if (score == null) return 'Match score unavailable';
  if (score >= 90) return 'Excellent match';
  if (score >= 75) return 'Strong match';
  if (score >= 60) return 'Moderate match';
  if (score >= 40) return 'Partial match';
  return 'Low match';
};

const BadgeList = ({ items, emptyText, tone = 'neutral' }) => {
  if (!items || items.length === 0) {
    return <p className="results-empty">{emptyText}</p>;
  }

  return (
    <div className="skill-list">
      {items.map((item, index) => (
        <span key={`${item}-${index}`} className={`skill-badge ${tone}`}>
          {tone === 'success' ? <CheckCircle2 size={14} /> : tone === 'warning' ? <TriangleAlert size={14} /> : <Sparkles size={14} />}
          {item}
        </span>
      ))}
    </div>
  );
};

const DocumentSelector = ({ label, value, documents, onChange, placeholder, typeLabel }) => {
  const options = documents.filter((doc) => doc.status === 'indexed');

  return (
    <div className="matcher-card selector-card">
      <label className="selector-label" htmlFor={label}>{label}</label>
      <select id={label} value={value} onChange={(event) => onChange(event.target.value)} aria-label={label}>
        <option value="">{placeholder}</option>
        {options.map((doc) => (
          <option key={doc.id} value={doc.id}>
            {doc.filename}
          </option>
        ))}
      </select>
      <div className="selector-meta">
        {value ? (
          <>
            <span>{documents.find((doc) => doc.id === value)?.filename || 'Selected'}</span>
            <span>{typeLabel}</span>
          </>
        ) : (
          <span>No document selected</span>
        )}
      </div>
    </div>
  );
};

const JobMatcherPage = () => {
  const {
    resumes,
    jobDescriptions,
    selectedResume,
    selectedJob,
    selectedResumeId,
    selectedJobId,
    setSelectedResumeId,
    setSelectedJobId,
    loading,
    analyzing,
    error,
    result,
    refreshDocuments,
    analyzeMatch,
  } = useJobMatcher();

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const canAnalyze = Boolean(selectedResumeId && selectedJobId && !analyzing);

  const handleAnalyze = async () => {
    try {
      await analyzeMatch();
    } catch (analysisError) {
      // handled by hook error state
    }
  };

  const matchRatioText = useMemo(() => {
    if (result && result.match_percentage != null) {
      return `${result.matched_required_skill_count || 0} of ${result.required_skill_count || 0} required skills matched`;
    }
    return 'Match score unavailable';
  }, [result]);

  return (
    <div className="jobs-page">
      <div className="page-header documents-header">
        <div>
          <p className="eyebrow accent">Job Matcher</p>
          <h1>Compare your profile against a target role.</h1>
          <p className="page-subtitle">CareerPilot compares the skills demonstrated in your resume with the requirements identified from the job description.</p>
        </div>
      </div>

      <div className="matcher-setup-grid">
        <DocumentSelector
          label="Your Resume"
          value={selectedResumeId}
          documents={resumes}
          onChange={setSelectedResumeId}
          placeholder="Select resume"
          typeLabel={selectedResume ? `${selectedResume.pages} pages • Indexed` : 'Indexed only'}
        />

        <div className="matcher-operator-wrap">
          <ArrowRight size={24} />
        </div>

        <DocumentSelector
          label="Job Description"
          value={selectedJobId}
          documents={jobDescriptions}
          onChange={setSelectedJobId}
          placeholder="Select job description"
          typeLabel={selectedJob ? `${selectedJob.pages} pages • Indexed` : 'Indexed only'}
        />
      </div>

      <div className="matcher-actions">
        <button type="button" className="primary-btn" onClick={handleAnalyze} disabled={!canAnalyze}>
          {analyzing ? <><Loader2 size={16} className="spin" />Anayzing...</> : 'Analyze Match'}
        </button>
        <button type="button" className="secondary-btn" onClick={refreshDocuments} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh documents'}
        </button>
      </div>

      {error ? (
        <div className="inline-message inline-message--error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      ) : null}

      {!loading && resumes.length === 0 && (
        <div className="empty-state-box">
          <FileText size={20} />
          <div>
            <h3>No resume uploaded</h3>
            <p>Upload your resume first to analyze your job fit.</p>
          </div>
          <a className="primary-btn inline-link" href="/documents">Upload Resume</a>
        </div>
      )}

      {!loading && jobDescriptions.length === 0 && (
        <div className="empty-state-box">
          <BriefcaseBusiness size={20} />
          <div>
            <h3>No job description available</h3>
            <p>Upload a job description to compare your profile.</p>
          </div>
          <a className="primary-btn inline-link" href="/documents">Upload Job Description</a>
        </div>
      )}

      {analyzing ? (
        <div className="analysis-loader">
          <Loader2 size={26} className="spin" />
          <div>
            <strong>Analyzing your profile...</strong>
            <p>Comparing resume evidence to the target role requirements.</p>
          </div>
        </div>
      ) : null}

      {result ? (
        <div className="match-result-panel">
          <div className="result-hero">
            <div className="score-ring" style={{ '--score': `${result.match_percentage ?? 0}%` }}>
              <div>
                <strong>{result.match_percentage ?? '—'}</strong>
                {result.match_percentage != null ? <span>%</span> : null}
              </div>
            </div>
            <div className="result-hero-copy">
              <p className="eyebrow accent">Your Match</p>
              <h2>{result.match_percentage != null ? getMatchLabel(result.match_percentage) : 'Match score unavailable'}</h2>
              <p>{matchRatioText}</p>
            </div>
          </div>

          <div className="result-grid">
            <section className="result-section">
              <h3>Matched Skills</h3>
              <BadgeList items={result.matched_skills || []} emptyText="No matched skills yet." tone="success" />
            </section>

            <section className="result-section">
              <h3>Missing Required Skills</h3>
              <BadgeList items={result.missing_skills || []} emptyText="No required skill gaps." tone="warning" />
            </section>

            <section className="result-section">
              <h3>Preferred Skill Gaps</h3>
              <BadgeList items={result.missing_preferred_skills || []} emptyText="No preferred skill gaps." tone="neutral" />
            </section>
          </div>

          <div className="result-grid">
            <section className="result-section">
              <h3>Your Strengths</h3>
              <ul className="text-list">
                {(result.strengths || []).map((strength, index) => (
                  <li key={`${strength}-${index}`}>{strength}</li>
                ))}
              </ul>
            </section>

            <section className="result-section">
              <h3>Skill Gaps</h3>
              {(result.skill_gaps || []).length ? (
                <div className="gap-list">
                  {result.skill_gaps.map((gap, index) => (
                    <article className="gap-card" key={`${gap.skill}-${index}`}>
                      <h4>{gap.skill}</h4>
                      <p>{gap.importance} • Priority: {gap.priority}</p>
                      <small>{gap.reason}</small>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="results-empty">No meaningful skill gaps reported.</p>
              )}
            </section>
          </div>

          <div className="result-grid">
            <section className="result-section">
              <h3>What You Should Do Next</h3>
              <ol className="recommendations-list">
                {(result.recommendations || []).map((recommendation, index) => (
                  <li key={`${recommendation.skill}-${index}`}>
                    <span className="recommendation-index">{String(index + 1).padStart(2, '0')}</span>
                    <div>
                      <strong>{recommendation.skill}</strong>
                      <p>{recommendation.reason}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>

            <section className="result-section">
              <h3>Job Requirements</h3>
              <div className="requirements-block">
                <h4>Required</h4>
                <ul>
                  {(result.matched_skills || []).concat(result.missing_skills || [])
                    .filter((item, index, arr) => arr.indexOf(item) === index)
                    .map((skill) => <li key={skill}>{skill}</li>)}
                </ul>
              </div>
            </section>
          </div>

          <section className="result-section">
            <h3>Evidence Used</h3>
            <div className="evidence-list">
              {(result.sources || []).map((source, index) => (
                <div className="evidence-item" key={`${source.source}-${source.page ?? index}`}>
                  <FileText size={16} />
                  <span>{source.source}</span>
                  {source.page ? <small>Page {source.page}</small> : null}
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
};

export default JobMatcherPage;
