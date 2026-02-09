import { useState } from 'react';
import { UploadIcon } from 'lucide-react';
import { FilePickerCard } from '@/components/ingestion/FilePickerCard';
import { FormatSelector } from '@/components/ingestion/FormatSelector';
import { apiClient } from '@/lib/apiClient';
import type { FileFormat, ScanResponse } from '@/types';

/**
 * IngestPage component
 *
 * Main page for file ingestion. Users select a local data file and optional format,
 * then initiate a scan. This initial version handles basic scan creation.
 * Progress tracking (#61) and enhanced success/error flows (#62) will be added later.
 */
export function IngestPage() {
  const [filePath, setFilePath] = useState('');
  const [fileFormat, setFileFormat] = useState<FileFormat | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [scanResponse, setScanResponse] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!filePath.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.createScan({
        source: filePath,
        file_format: fileFormat,
      });
      setScanResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="flex items-center gap-3 mb-2">
          <UploadIcon className="h-8 w-8 text-accent" />
          <h1 className="text-3xl font-bold text-primary">File Ingestion</h1>
        </div>
        <p className="text-muted mb-8">
          Select a local data file to sanitize. Supported formats: JSONL, CSV, and Parquet.
        </p>

        {/* File Picker + Format Selector */}
        <div className="space-y-6">
          <FilePickerCard
            value={filePath}
            onChange={setFilePath}
            disabled={isSubmitting}
          />
          <FormatSelector
            value={fileFormat}
            onChange={setFileFormat}
            disabled={isSubmitting}
          />

          {/* Error display (basic — will be enhanced in #62) */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-danger text-sm">
              {error}
            </div>
          )}

          {/* Scan result placeholder (basic — will be enhanced in #61/#62) */}
          {scanResponse && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm">
              <p className="text-primary font-medium">Scan initiated</p>
              <p className="text-muted">Scan ID: {scanResponse.scan_id}</p>
              <p className="text-muted">Status: {scanResponse.status}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !filePath.trim()}
            className={`
              px-6 py-3 rounded-lg font-medium text-white
              transition-colors duration-150
              ${isSubmitting || !filePath.trim()
                ? 'bg-slate-300 cursor-not-allowed'
                : 'bg-accent hover:bg-indigo-700'
              }
            `}
          >
            {isSubmitting ? 'Starting Scan...' : 'Start Scan'}
          </button>
        </div>
      </div>
    </div>
  );
}
