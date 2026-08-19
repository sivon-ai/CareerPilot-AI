import { CloudUpload, FileText, Upload } from 'lucide-react';
import { useId, useState } from 'react';

const UploadZone = ({
  onFileSelected,
  isUploading,
  uploadState,
  disabled = false,
}) => {
  const inputId = useId();
  const [dragActive, setDragActive] = useState(false);

  const handleFile = (file) => {
    if (!file) {
      return;
    }
    onFileSelected(file);
  };

  const handleDrag = (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (event.type === 'dragenter' || event.type === 'dragover') {
      setDragActive(true);
      return;
    }

    setDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);

    const file = event.dataTransfer.files?.[0];
    handleFile(file);
  };

  return (
    <div
      id="upload-zone-trigger"
      className={`upload-zone ${dragActive ? 'drag-active' : ''} ${uploadState === 'uploading' ? 'uploading' : ''}`}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      aria-disabled={disabled || isUploading}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if ((event.key === 'Enter' || event.key === ' ') && !disabled) {
          event.preventDefault();
          document.getElementById(inputId)?.click();
        }
      }}
    >
      <div className="upload-zone__icon">
        <CloudUpload size={28} />
      </div>

      <div className="upload-zone__body">
        <div className="upload-zone__title-row">
          <Upload size={16} />
          <span>Upload PDF</span>
        </div>

        <p className="upload-zone__message">
          {dragActive ? 'Drop PDF here' : 'Drag & drop your PDF here'}
        </p>

        <div className="upload-zone__cta-wrap">
          <button type="button" className="secondary-btn" onClick={() => document.getElementById(inputId)?.click()} disabled={disabled || isUploading}>
            Browse Files
          </button>
        </div>

        <div className="upload-zone__meta">
          <FileText size={14} />
          <span>PDF files only</span>
        </div>
      </div>

      <input
        id={inputId}
        type="file"
        accept=".pdf,application/pdf"
        onChange={(event) => {
          const file = event.target.files?.[0];
          handleFile(file);
          event.target.value = '';
        }}
        aria-label="Upload PDF document"
      />
    </div>
  );
};

export default UploadZone;
