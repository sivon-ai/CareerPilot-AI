const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const getPayloadError = (payload, fallback) => {
  if (payload && typeof payload === 'object') {
    if (payload.error && typeof payload.error.message === 'string') {
      return payload.error.message;
    }
    if (typeof payload.detail === 'string') {
      return payload.detail;
    }
    if (typeof payload.message === 'string') {
      return payload.message;
    }
  }

  return fallback;
};

export const API_CONFIG = {
  baseUrl: API_BASE_URL,
  maxFileSizeBytes: MAX_FILE_SIZE_BYTES,
};

export const validatePdfFile = (file) => {
  if (!file) {
    return 'Please select a file.';
  }

  const filename = file.name || '';
  const hasPdfExtension = filename.toLowerCase().endsWith('.pdf');
  const hasPdfType = file.type === 'application/pdf' || file.type === 'application/octet-stream';

  if (!hasPdfExtension && !hasPdfType) {
    return 'Only PDF files are supported.';
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return 'This file is larger than the 10 MB limit.';
  }

  return '';
};

export const normalizeDocumentsResponse = (payload) => {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (payload && Array.isArray(payload.documents)) {
    return payload.documents;
  }

  return [];
};

export const getDocuments = async () => {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to load documents.'));
  }

  return normalizeDocumentsResponse(payload);
};

export const getDocument = async (documentId) => {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to load this document.'));
  }

  return payload;
};

export const uploadDocument = async (file) => {
  const validationMessage = validatePdfFile(file);
  if (validationMessage) {
    throw new Error(validationMessage);
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to upload the document.'));
  }

  return {
    id: payload.document_id,
    filename: payload.filename,
    pages: payload.pages ?? 0,
    chunks: payload.chunks ?? 0,
    status: payload.status ?? 'indexed',
  };
};

export const deleteDocument = async (documentId) => {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: 'DELETE',
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to delete this document. Please try again.'));
  }

  return payload;
};

export const matchJob = async (resumeDocumentId, jobDocumentId) => {
  const response = await fetch(`${API_BASE_URL}/jobs/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ resume_document_id: resumeDocumentId, job_document_id: jobDocumentId }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to calculate the job match.'));
  }

  return payload;
};

export const startInterview = async ({ resume_document_id, job_document_id, interview_type = 'mixed', difficulty = 'medium', question_count = 10 }) => {
  const response = await fetch(`${API_BASE_URL}/interview/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      resume_document_id,
      job_document_id,
      interview_type,
      difficulty,
      question_count,
    }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to start the interview.'));
  }

  return payload;
};

export const submitInterviewAnswer = async (sessionId, { question_id, answer }) => {
  const response = await fetch(`${API_BASE_URL}/interview/${sessionId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ question_id, answer }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'We couldn\'t evaluate this answer. Please try again.'));
  }

  return payload;
};

export const getInterviewReport = async (sessionId) => {
  const response = await fetch(`${API_BASE_URL}/interview/${sessionId}/report`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getPayloadError(payload, 'Unable to load the interview report.'));
  }

  return payload;
};

export const getFriendlyApiError = (error) => {
  const message = error?.message || '';

  if (!message) {
    return 'Unable to connect to CareerPilot AI.';
  }

  if (message.includes('Failed to fetch') || message.includes('fetch')) {
    return 'Unable to connect to CareerPilot AI.';
  }

  return message;
};
