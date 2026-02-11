import { useState, useEffect } from 'react';
import { UploadIcon, CheckCircleIcon, AlertCircleIcon, RefreshCwIcon, ArrowRightIcon, InfoIcon, XIcon } from 'lucide-react';
import { WelcomeModal } from '@/components/common/WelcomeModal';
import { FilePickerCard } from '@/components/ingestion/FilePickerCard';
import { FormatSelector } from '@/components/ingestion/FormatSelector';
import { IngestionProgress } from '@/components/ingestion/IngestionProgress';
import { useScanProgress } from '@/hooks/useScanProgress';
import { apiClient } from '@/lib/apiClient';
import { getErrorMessage } from '@/lib/errorMessages';
import type { FileFormat, UploadedFileInfo } from '@/types';
import { ScanStatus } from '@/types';

interface IngestPageProps {
  onViewResults?: (source: string, scanId: string) => void;
}

/**
 * IngestPage component
 *
 * Main page for file ingestion. Users upload local data files via the browser's
 * native file picker, then initiate a scan. Real-time progress is displayed
 * via WebSocket connection.
 */
export function IngestPage({ onViewResults }: IngestPageProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [fileFormat, setFileFormat] = useState<FileFormat | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const { progress, isConnected } = useScanProgress(scanId);
  const [showHelper, setShowHelper] = useState(() => {
    try {
      return localStorage.getItem('cecil:ingest_helper_dismissed') !== 'true';
    } catch {
      return true;
    }
  });

  const dismissHelper = () => {
    setShowHelper(false);
    try {
      localStorage.setItem('cecil:ingest_helper_dismissed', 'true');
    } catch {
      // Silently ignore storage errors
    }
  };

  const handleBrowseClick = async (fileList: FileList) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const files = Array.from(fileList);
      const response = await apiClient.uploadFiles(files);
      if (response.files.length > 0) {
        setUploadedFiles((prev) => [...prev, ...response.files]);
        // Auto-detect format from the first file if not already set
        if (!fileFormat && response.files[0].format) {
          setFileFormat(response.files[0].format as FileFormat);
        }
      }
      if (response.errors.length > 0) {
        setUploadError(response.errors.join('; '));
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (uploadedFiles.length === 0) return;
    setIsSubmitting(true);
    setError(null);
    try {
      // Scan the first uploaded file (multi-file scan support can be added later)
      const file = uploadedFiles[0];
      const response = await apiClient.createScan({
        source: file.path,
        file_format: fileFormat,
      });
      setScanId(response.scan_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Determine the current page state
  type PageState = 'idle' | 'scanning' | 'completed' | 'failed';
  const pageState: PageState = (() => {
    if (!scanId || !progress) return scanId ? 'scanning' : 'idle';
    if (progress.status === ScanStatus.COMPLETED) return 'completed';
    if (progress.status === ScanStatus.FAILED) return 'failed';
    return 'scanning';
  })();

  // Determine if a scan is currently active (not in a terminal state)
  const isScanning = pageState === 'scanning';

  // Navigation guard: warn before closing browser tab/window during scan
  useEffect(() => {
    if (pageState === 'scanning') {
      const handleBeforeUnload = (e: BeforeUnloadEvent) => {
        e.preventDefault();
        e.returnValue = '';
      };
      window.addEventListener('beforeunload', handleBeforeUnload);
      return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }
  }, [pageState]);

  // Handler: reset state for a new scan
  const handleNewScan = () => {
    setScanId(null);
    setUploadedFiles([]);
    setFileFormat(null);
    setError(null);
    setUploadError(null);
  };

  // Handler: retry the current scan
  const handleRetry = async () => {
    setScanId(null);
    setError(null);
    await handleSubmit();
  };

  // Handler: navigate to audit/mapping view with scan results
  const handleViewResults = () => {
    if (scanId && uploadedFiles.length > 0 && onViewResults) {
      onViewResults(uploadedFiles[0].path, scanId);
    }
  };

  return (
    <>
    <WelcomeModal />
    <div className="p-10">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="flex items-center gap-3 mb-2">
          <UploadIcon className="h-8 w-8 text-accent" />
          <h1 className="text-3xl font-extrabold text-primary">File Ingestion</h1>
        </div>
        <p className="text-muted leading-relaxed mb-8">
          Upload data files to sanitize. Supported formats: JSONL, CSV, and Parquet.
        </p>

        {/* Inline Helper Banner */}
        {showHelper && pageState === 'idle' && (
          <div className="bg-accent-light border border-[var(--border-accent)] rounded-lg p-4 mb-8 flex items-start gap-3">
            <InfoIcon className="h-5 w-5 text-accent flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-primary">New to Cecil?</p>
              <p className="text-sm text-muted mt-0.5">
                Click "Browse Files" to select data files from your computer.
                Cecil uploads them locally and processes everything on your machine.
              </p>
            </div>
            <button
              type="button"
              onClick={dismissHelper}
              className="flex-shrink-0 p-1 text-faint hover:text-muted transition-colors"
              aria-label="Dismiss helper"
            >
              <XIcon className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Main Content — conditional on page state */}
        <div className="space-y-8">
          {pageState === 'idle' && (
            <>
              <FilePickerCard
                onFilesUploaded={setUploadedFiles}
                uploadedFiles={uploadedFiles}
                isUploading={isUploading}
                uploadError={uploadError}
                onBrowseClick={handleBrowseClick}
                onRemoveFile={handleRemoveFile}
                disabled={isSubmitting || isScanning}
              />
              <FormatSelector
                value={fileFormat}
                onChange={setFileFormat}
                disabled={isSubmitting || isScanning}
              />

              {/* Error display (API submission errors only) */}
              {error && (
                <div className="p-4 bg-danger-bg border border-[var(--danger-border)] rounded-lg text-danger text-sm">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting || isScanning || uploadedFiles.length === 0}
                className={`
                  px-6 py-3 rounded-lg font-medium
                  transition-all duration-150 ease-out
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
                  active:scale-[0.98]
                  ${isSubmitting || isScanning || uploadedFiles.length === 0
                    ? 'bg-skeleton text-muted cursor-not-allowed'
                    : 'bg-accent hover:bg-accent-hover text-white'
                  }
                `}
              >
                {isSubmitting ? 'Starting Scan...' : 'Start Scan'}
              </button>
            </>
          )}

          {pageState === 'scanning' && (
            <IngestionProgress progress={progress} isConnected={isConnected} />
          )}

          {pageState === 'completed' && progress && (
            <div className="bg-card border border-[var(--success-border)] rounded-lg p-8 text-center">
              <CheckCircleIcon className="h-12 w-12 text-emerald-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-primary mb-2">Scan Complete</h2>
              <p className="text-muted mb-6">
                <span className="font-medium text-primary">{progress.records_processed.toLocaleString()}</span> records processed
              </p>
              <div className="flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={handleViewResults}
                  className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium transition-colors duration-150"
                >
                  View Audit Results
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={handleNewScan}
                  className="px-6 py-3 border text-primary hover:bg-subtle rounded-lg font-medium transition-colors duration-150"
                >
                  Start New Scan
                </button>
              </div>
            </div>
          )}

          {pageState === 'failed' && progress && (
            <div className="bg-card border border-[var(--danger-border)] rounded-lg p-8 text-center">
              <AlertCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-primary mb-2">Scan Failed</h2>
              <p className="text-muted mb-6">{getErrorMessage(progress.error_type)}</p>
              <div className="flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium transition-colors duration-150"
                >
                  <RefreshCwIcon className="h-4 w-4" />
                  Retry
                </button>
                <button
                  type="button"
                  onClick={handleNewScan}
                  className="px-6 py-3 border text-primary hover:bg-subtle rounded-lg font-medium transition-colors duration-150"
                >
                  Upload New Files
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
