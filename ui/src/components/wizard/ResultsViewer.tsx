import { useState, useEffect } from 'react';
import { XIcon, ChevronLeftIcon, ChevronRightIcon, EyeOffIcon } from 'lucide-react';
import { apiClient } from '@/lib/apiClient';

interface ResultsViewerProps {
  outputPath: string;
  onClose: () => void;
}

/**
 * ResultsViewer component
 *
 * Displays sanitized output records in a table format with pagination.
 * Highlights redacted values (e.g., [EMAIL_REDACTED]) with distinct styling.
 */
export function ResultsViewer({ outputPath, onClose }: ResultsViewerProps) {
  const [records, setRecords] = useState<Record<string, unknown>[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageSize = 50;

  useEffect(() => {
    const fetchRecords = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const offset = (currentPage - 1) * pageSize;
        const response = await apiClient.previewOutput(outputPath, offset, pageSize);
        setRecords(response.records);
        setTotalCount(response.total_count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load results');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecords();
  }, [outputPath, currentPage]);

  const totalPages = Math.ceil(totalCount / pageSize);
  const startRecord = totalCount === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endRecord = Math.min(currentPage * pageSize, totalCount);

  // Extract column names from the first record
  const columns = records.length > 0 ? Object.keys(records[0]) : [];

  // Check if a value looks like a redacted token
  const isRedacted = (value: unknown): boolean => {
    if (typeof value !== 'string') return false;
    return /^\[.*_REDACTED\]$/.test(value);
  };

  // Render a cell value with highlighting for redacted values
  const renderCellValue = (value: unknown): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span style={{ color: 'var(--text-muted)' }}>null</span>;
    }

    const stringValue = String(value);

    if (isRedacted(stringValue)) {
      return (
        <span
          style={{
            backgroundColor: '#fef2f2',
            color: '#b91c1c',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '12px',
            fontFamily: 'monospace',
            fontWeight: 500,
          }}
        >
          {stringValue}
        </span>
      );
    }

    return <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{stringValue}</span>;
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-card)',
          borderRadius: '12px',
          boxShadow: 'var(--shadow-lg)',
          width: '100%',
          maxWidth: '1200px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', color: 'var(--text-primary)' }}>
              Sanitized Results
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>
              {totalCount} {totalCount === 1 ? 'record' : 'records'} • {outputPath}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '8px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
            }}
            aria-label="Close"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px',
          }}
        >
          {isLoading && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '48px',
              }}
            >
              <div className="spinner" style={{ width: '32px', height: '32px' }} />
            </div>
          )}

          {error && (
            <div
              style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                padding: '16px',
                color: '#b91c1c',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <EyeOffIcon className="h-5 w-5" />
              <div>
                <p style={{ margin: 0, fontWeight: 500 }}>Failed to load results</p>
                <p style={{ margin: '4px 0 0', fontSize: '14px' }}>{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && records.length === 0 && (
            <div
              style={{
                textAlign: 'center',
                padding: '48px',
                color: 'var(--text-secondary)',
              }}
            >
              <p style={{ margin: 0 }}>No records found</p>
            </div>
          )}

          {!isLoading && !error && records.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: '14px',
                }}
              >
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th
                        key={col}
                        style={{
                          textAlign: 'left',
                          padding: '12px',
                          borderBottom: '2px solid var(--border-color)',
                          backgroundColor: 'var(--bg-body)',
                          color: 'var(--text-primary)',
                          fontWeight: 600,
                          position: 'sticky',
                          top: 0,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {records.map((record, rowIndex) => (
                    <tr key={rowIndex}>
                      {columns.map((col) => (
                        <td
                          key={col}
                          style={{
                            padding: '12px',
                            borderBottom: '1px solid var(--border-color)',
                            color: 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {renderCellValue(record[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer with pagination */}
        {!isLoading && !error && records.length > 0 && (
          <div
            style={{
              padding: '16px 24px',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              Showing {startRecord}–{endRecord} of {totalCount} records
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <ChevronLeftIcon className="h-4 w-4" />
                Previous
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                Next
                <ChevronRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
