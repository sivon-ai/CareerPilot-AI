import { useCallback, useEffect, useMemo, useState } from 'react';

import { API_CONFIG, deleteDocument, getDocuments, getFriendlyApiError, uploadDocument } from '../services/api';

const normalizeDocument = (item) => {
  if (!item || typeof item !== 'object') {
    return null;
  }

  const id = item.document_id || item.id || item.filename || crypto.randomUUID();

  return {
    id,
    filename: item.filename || 'Unnamed document',
    pages: item.pages ?? 0,
    chunks: item.chunks ?? 0,
    status: item.status || 'indexed',
    uploaded_at: item.uploaded_at || item.uploadedAt || item.created_at || item.createdAt || null,
  };
};

export const useDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadState, setUploadState] = useState('idle');
  const [selectedFile, setSelectedFile] = useState(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);

  const refreshDocuments = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await getDocuments();
      const normalizedDocuments = (response || []).map(normalizeDocument).filter(Boolean);
      setDocuments(normalizedDocuments);
    } catch (loadError) {
      const friendlyMessage = getFriendlyApiError(loadError);
      setError(friendlyMessage);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const uploadFile = useCallback(
    async (file) => {
      if (!file) {
        setUploadState('error');
        setError('Please select a file.');
        return;
      }

      setSelectedFile(file);
      setUploadState('validating');
      setError('');

      try {
        setUploading(true);
        setUploadProgress(0);
        setUploadState('uploading');

        const uploadedFile = await uploadDocument(file);
        const normalized = normalizeDocument({
          ...uploadedFile,
          document_id: uploadedFile.id,
          status: uploadedFile.status || 'indexed',
        });

        setDocuments((currentDocuments) => {
          const alreadyExists = currentDocuments.some((document) => document.id === normalized.id);
          return alreadyExists ? currentDocuments : [normalized, ...currentDocuments];
        });

        setUploadProgress(100);
        setUploadState(uploadedFile.status === 'indexed' ? 'success' : 'processing');

        if (uploadedFile.status === 'indexed') {
          await refreshDocuments();
        }
      } catch (uploadError) {
        setUploadState('error');
        setError(getFriendlyApiError(uploadError));
      } finally {
        setUploading(false);
      }
    },
    [refreshDocuments],
  );

  const removeDocument = useCallback(
    async (documentId) => {
      setDeletingDocumentId(documentId);
      setError('');

      try {
        await deleteDocument(documentId);
        setDocuments((currentDocuments) => currentDocuments.filter((document) => document.id !== documentId));
        return true;
      } catch (deleteError) {
        setError('Unable to delete this document. Please try again.');
        return false;
      } finally {
        setDeletingDocumentId(null);
      }
    },
    [],
  );

  const clearSelectedFile = useCallback(() => {
    setSelectedFile(null);
    setUploadState('idle');
    setUploadProgress(0);
  }, []);

  return useMemo(
    () => ({
      documents,
      loading,
      error,
      uploading,
      uploadProgress,
      uploadState,
      selectedFile,
      deletingDocumentId,
      refreshDocuments,
      uploadFile,
      deleteDocument: removeDocument,
      clearSelectedFile,
      apiBaseUrl: API_CONFIG.baseUrl,
    }),
    [clearSelectedFile, deletingDocumentId, documents, error, loading, removeDocument, refreshDocuments, selectedFile, uploadFile, uploadProgress, uploadState, uploading],
  );
};
