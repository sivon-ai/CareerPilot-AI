import { AlertCircle, CheckCircle2, FileText, Loader2, PencilLine, Trash2, Upload, X } from 'lucide-react';
import { useMemo, useRef, useState } from 'react';

import UploadZone from '../components/UploadZone.jsx';
import { getFriendlyApiError, validatePdfFile } from '../services/api.js';
import { useDocuments } from '../hooks/useDocuments.js';

const statusStyles = {
  uploading: { label: 'Uploading', className: 'status-pill status-uploading', icon: Loader2 },
  processing: { label: 'Processing', className: 'status-pill status-processing', icon: Loader2 },
  indexed: { label: 'Indexed', className: 'status-pill status-indexed', icon: CheckCircle2 },
  failed: { label: 'Failed', className: 'status-pill status-failed', icon: AlertCircle },
};

const formatUploadDate = (value) => {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

function DocumentCard({ document, onDelete, deleting }) {
  const config = statusStyles[document.status] || statusStyles.indexed;
  const Icon = config.icon;

  return (
    <article className="document-card">
      <div className="document-card__header">
        <div className="document-card__title-wrap">
          <div className="document-card__file-icon">
            <FileText size={18} />
          </div>
          <div className="document-card__title-block">
            <h3>{document.filename}</h3>
            <div className="document-card__meta">
              {document.pages ? <span>{document.pages} pages</span> : null}
              {document.chunks ? <span>{document.chunks} chunks</span> : null}
              {document.uploaded_at ? <span>{formatUploadDate(document.uploaded_at)}</span> : null}
            </div>
          </div>
        </div>

        <button
          type="button"
          className="icon-button document-card__delete"
          aria-label="Delete document"
          onClick={() => onDelete(document.id)}
          disabled={deleting}
        >
          {deleting ? <Loader2 size={16} className="spin" /> : <Trash2 size={16} />}
        </button>
      </div>

      <div className="document-card__footer">
        <span className={config.className}>
          <Icon size={14} />
          {config.label}
        </span>
        {deleting ? <span className="document-card__small-subtle">Deleting...</span> : null}
      </div>
    </article>
  );
}

function DocumentList({ documents, onDelete, deletingDocumentId }) {
  if (!documents.length) {
    return (
      <div className="documents-empty-state">
        <div className="documents-empty-state__icon">
          <FileText size={26} />
        </div>
        <h3>No documents yet</h3>
        <p>Upload your resume or a job description to get started with CareerPilot AI.</p>
        <button type="button" className="primary-btn" onClick={() => document.getElementById('upload-zone-trigger')?.click()}>
          Upload Document
        </button>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((document) => (
        <DocumentCard
          key={document.id}
          document={document}
          onDelete={onDelete}
          deleting={deletingDocumentId === document.id}
        />
      ))}
    </div>
  );
}

function ConfirmModal({ isOpen, onClose, onConfirm, deleting }) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="delete-document-title">
      <div className="modal-card">
        <div className="modal-header">
          <h3 id="delete-document-title">Delete document?</h3>
          <button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <p>This document will no longer be available to CareerPilot AI.</p>

        <div className="modal-actions">
          <button type="button" className="secondary-btn" onClick={onClose} disabled={deleting}>
            Cancel
          </button>
          <button type="button" className="danger-btn" onClick={onConfirm} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

function DocumentsPage() {
  const {
    documents,
    loading,
    error,
    uploadFile,
    deleteDocument,
    refreshDocuments,
    uploadState,
    uploading,
    selectedFile,
    deletingDocumentId,
    clearSelectedFile,
  } = useDocuments();

  const [validationError, setValidationError] = useState('');
  const [pendingDeleteId, setPendingDeleteId] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileSelected = async (file) => {
    const validationMessage = validatePdfFile(file);
    setValidationError(validationMessage);

    if (validationMessage) {
      return;
    }

    setValidationError('');

    try {
      setUploadMessage('');
      await uploadFile(file);
      setUploadMessage('Document uploaded successfully.');
      clearSelectedFile();
      await refreshDocuments();
    } catch (uploadError) {
      setUploadMessage(getFriendlyApiError(uploadError));
    }
  };

  const handleDelete = async () => {
    if (!pendingDeleteId) {
      return;
    }

    const success = await deleteDocument(pendingDeleteId);
    if (success) {
      setUploadMessage('Document deleted successfully.');
    }

    setPendingDeleteId(null);
  };

  const pageError = useMemo(() => {
    if (error) {
      return error;
    }

    if (validationError) {
      return validationError;
    }

    return '';
  }, [error, validationError]);

  return (
    <div className="documents-page">
      <div className="page-header documents-header">
        <div>
          <p className="eyebrow accent">Documents</p>
          <h1>Documents</h1>
          <p className="page-subtitle">Manage the files CareerPilot AI uses for analysis and retrieval.</p>
        </div>

        <button type="button" className="primary-btn document-upload-button" onClick={() => document.getElementById('upload-zone-trigger')?.click()}>
          <Upload size={16} />
          Upload Document
        </button>
      </div>

      <div className="documents-main-panel">
        <div className="upload-panel">
          <UploadZone
            onFileSelected={handleFileSelected}
            isUploading={uploading}
            uploadState={uploadState}
            disabled={uploading}
          />

          {pageError ? (
            <div className="inline-message inline-message--error">
              <AlertCircle size={16} />
              <span>{pageError}</span>
            </div>
          ) : null}

          {uploadState === 'validating' ? (
            <div className="inline-message inline-message--muted">
              <Loader2 size={16} className="spin" />
              <span>Validating file...</span>
            </div>
          ) : null}

          {uploadState === 'uploading' ? (
            <div className="inline-message inline-message--muted">
              <Loader2 size={16} className="spin" />
              <span>Uploading document...</span>
            </div>
          ) : null}

          {uploadState === 'processing' ? (
            <div className="inline-message inline-message--muted">
              <Loader2 size={16} className="spin" />
              <span>Processing document...</span>
            </div>
          ) : null}

          {uploadState === 'success' ? (
            <div className="inline-message inline-message--success">
              <CheckCircle2 size={16} />
              <span>✓ Document indexed successfully</span>
            </div>
          ) : null}

          {uploadMessage && uploadState !== 'error' && uploadState !== 'validating' ? (
            <div className="inline-message inline-message--success">
              <CheckCircle2 size={16} />
              <span>{uploadMessage}</span>
            </div>
          ) : null}

          {selectedFile && !uploading ? (
            <div className="selected-file-panel">
              <span>Selected file</span>
              <strong>{selectedFile.name}</strong>
              <button type="button" onClick={() => clearSelectedFile()}>
                Clear
              </button>
            </div>
          ) : null}
        </div>

        <div className="document-section">
          <div className="documents-toolbar">
            <h2>Document library</h2>
            <button type="button" className="secondary-btn" onClick={refreshDocuments} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {loading ? (
            <div className="document-list document-list--loading">
              {[1, 2, 3].map((key) => (
                <div className="document-card document-card--skeleton" key={key}>
                  <div className="skeleton-line skeleton-line--wide" />
                  <div className="skeleton-line" />
                  <div className="skeleton-line skeleton-line--small" />
                </div>
              ))}
            </div>
          ) : (
            <DocumentList documents={documents} onDelete={(id) => setPendingDeleteId(id)} deletingDocumentId={deletingDocumentId} />
          )}

          {!loading && !documents.length && !error ? (
            <div className="inline-message inline-message--muted">
              <PencilLine size={16} />
              <span>Loading documents...</span>
            </div>
          ) : null}

          {error && !loading ? (
            <div className="documents-error-box">
              <h3>Unable to connect to CareerPilot AI.</h3>
              <p>Make sure the backend is running and try again.</p>
              <button type="button" className="primary-btn" onClick={refreshDocuments}>
                Retry
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <ConfirmModal
        isOpen={Boolean(pendingDeleteId)}
        onClose={() => setPendingDeleteId(null)}
        onConfirm={handleDelete}
        deleting={Boolean(deletingDocumentId)}
      />
    </div>
  );
}

export default DocumentsPage;
