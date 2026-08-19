import { useCallback, useMemo, useState } from 'react';

import { getDocuments, getFriendlyApiError, matchJob } from '../services/api';

const normalizeDocument = (item) => {
  if (!item || typeof item !== 'object') {
    return null;
  }

  const documentType = (item.document_type || item.type || 'other').toString().trim().toLowerCase();
  const normalized = {
    id: item.document_id || item.id || item.filename || crypto.randomUUID(),
    filename: item.filename || 'Unnamed document',
    pages: item.pages ?? 0,
    status: item.status || 'indexed',
    documentType,
    uploaded_at: item.uploaded_at || item.uploadedAt || item.created_at || item.createdAt || null,
  };

  return normalized;
};

export const useJobMatcher = () => {
  const [documents, setDocuments] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const refreshDocuments = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await getDocuments();
      const normalized = (response || []).map(normalizeDocument).filter(Boolean);
      setDocuments(normalized);
    } catch (loadError) {
      setDocuments([]);
      setError(getFriendlyApiError(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  const resumes = useMemo(
    () => documents.filter((document) => document.status === 'indexed' && (document.documentType === 'resume' || document.documentType === 'other')),
    [documents],
  );

  const jobDescriptions = useMemo(
    () => documents.filter((document) => document.status === 'indexed' && (document.documentType === 'job_description' || document.documentType === 'other')),
    [documents],
  );

  const selectedResume = useMemo(
    () => resumes.find((document) => document.id === selectedResumeId) || null,
    [resumes, selectedResumeId],
  );

  const selectedJob = useMemo(
    () => jobDescriptions.find((document) => document.id === selectedJobId) || null,
    [jobDescriptions, selectedJobId],
  );

  const analyzeMatch = useCallback(async () => {
    if (!selectedResumeId) {
      throw new Error('Please select a resume.');
    }
    if (!selectedJobId) {
      throw new Error('Please select a job description.');
    }

    setAnalyzing(true);
    setError('');

    try {
      const payload = await matchJob(selectedResumeId, selectedJobId);
      setResult(payload);
      return payload;
    } catch (matchError) {
      setResult(null);
      setError(getFriendlyApiError(matchError));
      throw matchError;
    } finally {
      setAnalyzing(false);
    }
  }, [selectedJobId, selectedResumeId]);

  const reset = useCallback(() => {
    setSelectedResumeId('');
    setSelectedJobId('');
    setResult(null);
    setError('');
  }, []);

  return {
    documents,
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
    reset,
  };
};
