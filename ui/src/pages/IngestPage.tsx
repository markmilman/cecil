import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadIcon, CheckCircleIcon, AlertCircleIcon, RefreshCwIcon, ArrowRightIcon, InfoIcon, XIcon } from 'lucide-react';
import { WelcomeModal } from '@/components/common/WelcomeModal';
import { FilePickerCard } from '@/components/ingestion/FilePickerCard';
import { FormatSelector } from '@/components/ingestion/FormatSelector';
import { IngestionProgress } from '@/components/ingestion/IngestionProgress';
import { useScanProgress } from '@/hooks/useScanProgress';
import { apiClient } from '@/lib/apiClient';
import { getErrorMessage } from '@/lib/errorMessages';
import type { FileFormat } from '@/types';
import type { SelectedFile } from '@/components/ingestion/FilePickerCard';
import type { FileSelectionMetadata } from '@/components/ingestion/FileBrowserModal';
import { ScanStatus } from '@/types';

/**
 * IngestPage component
 *
 * Main page for file ingestion. Users select a local data file and optional format,
 * then initiate a scan. Real-time progress is displayed via WebSocket connection.
 * Includes success/error flows and navigation guards (#62).
 */
export function IngestPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
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

  const handleFileSelect = (_path: string, metadata: FileSelectionMetadata) => {
    setSelectedFile({
      path: _path,
      name: metadata.name,
      size: metadata.size,
      format: metadata.format,
    });
    // Auto-detect format from metadata if available
    if (metadata.format) {
      setFileFormat(metadata.format as FileFormat);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.createScan({
        source: selectedFile.path,
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
    setSelectedFile(null);
    setFileFormat(null);
    setError(null);
  };

  // Handler: retry the current scan
  const handleRetry = async () => {
    setScanId(null);
    setError(null);
    // Brief delay to allow state cleanup before re-submitting
    await handleSubmit();
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
        <p className="text-slate-600 leading-relaxed mb-8">
          Select a local data file to sanitize. Supported formats: JSONL, CSV, and Parquet.
        </p>

        {/* Inline Helper Banner */}
        {showHelper && pageState === 'idle' && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-8 flex items-start gap-3">
            <InfoIcon className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-primary">New to Cecil?</p>
              <p className="text-sm text-slate-600 mt-0.5">
                Select a data file using the file browser below to begin sanitizing your data.
                Cecil processes everything locally on your machine.
              </p>
            </div>
            <button
              type="button"
              onClick={dismissHelper}
              className="flex-shrink-0 p-1 text-slate-400 hover:text-slate-600 transition-colors"
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
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                disabled={isSubmitting || isScanning}
              />
              <FormatSelector
                value={fileFormat}
                onChange={setFileFormat}
                disabled={isSubmitting || isScanning}
              />

              {/* Error display (API submission errors only) */}
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-danger text-sm">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting || isScanning || !selectedFile}
                className={`
                  px-6 py-3 rounded-lg font-medium text-white
                  transition-all duration-150 ease-out
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600
                  active:scale-[0.98]
                  ${isSubmitting || isScanning || !selectedFile
                    ? 'bg-slate-300 cursor-not-allowed'
                    : 'bg-accent hover:bg-indigo-700'
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
            <div className="bg-white border border-emerald-200 rounded-lg p-8 text-center">
              <CheckCircleIcon className="h-12 w-12 text-emerald-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-primary mb-2">Scan Complete</h2>
              <p className="text-muted mb-6">
                <span className="font-medium text-primary">{progress.records_processed.toLocaleString()}</span> records processed
              </p>
              <div className="flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={() => navigate('/audit')}
                  className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors duration-150"
                >
                  View Audit Results
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={handleNewScan}
                  className="px-6 py-3 border border-slate-200 text-primary hover:bg-slate-50 rounded-lg font-medium transition-colors duration-150"
                >
                  Start New Scan
                </button>
              </div>
            </div>
          )}

          {pageState === 'failed' && progress && (
            <div className="bg-white border border-red-200 rounded-lg p-8 text-center">
              <AlertCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-primary mb-2">Scan Failed</h2>
              <p className="text-muted mb-6">{getErrorMessage(progress.error_type)}</p>
              <div className="flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors duration-150"
                >
                  <RefreshCwIcon className="h-4 w-4" />
                  Retry
                </button>
                <button
                  type="button"
                  onClick={handleNewScan}
                  className="px-6 py-3 border border-slate-200 text-primary hover:bg-slate-50 rounded-lg font-medium transition-colors duration-150"
                >
                  Change File
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
