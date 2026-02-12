import { useEffect } from 'react';
import { X, FolderOpen } from 'lucide-react';
import { StatusPill } from '@/components/common/StatusPill';
import { apiClient } from '@/lib/apiClient';

import type { JobRecord } from '@/types';

interface JobDetailDrawerProps {
  job: JobRecord | null;
  onClose: () => void;
  onViewMapping?: (mappingId: string) => void;
}

/**
 * Extract the parent directory from a file path.
 */
function parentDir(path: string): string {
  const parts = path.replace(/\\/g, '/').split('/');
  parts.pop();
  return parts.join('/') || '/';
}

/**
 * Map a job status string to a StatusPill variant.
 */
function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'neutral' {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'danger';
    case 'running':
      return 'warning';
    default:
      return 'neutral';
  }
}

/**
 * Format an ISO 8601 date string for display.
 */
function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

/**
 * Slide-from-right drawer panel for displaying job details.
 *
 * Shows job metadata, record counts, source/output paths with
 * "Open Folder" buttons, mapping info, and errors (if any).
 */
export function JobDetailDrawer({ job, onClose, onViewMapping }: JobDetailDrawerProps) {
  useEffect(() => {
    if (!job) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [job, onClose]);

  if (!job) return null;

  const pill = statusVariant(job.status);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
      {/* Backdrop */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
        }}
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div
        className="animate-slide-in-right"
        style={{
          position: 'relative',
          width: '420px',
          maxWidth: '100%',
          height: '100%',
          backgroundColor: 'var(--bg-card)',
          borderLeft: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-md)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid var(--border-color)',
          }}
        >
          <h2
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Job Details
          </h2>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '6px',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Status section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Status</SectionLabel>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span
                style={{
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                }}
              >
                {job.job_id}
              </span>
              <StatusPill
                label={job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                variant={pill}
              />
            </div>
          </div>

          {/* Dates section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Dates</SectionLabel>
            <DetailRow label="Created" value={formatDateTime(job.created_at)} />
            <DetailRow
              label="Completed"
              value={job.completed_at ? formatDateTime(job.completed_at) : '—'}
            />
          </div>

          {/* Records section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Records</SectionLabel>
            <DetailRow label="Processed" value={job.records_processed.toLocaleString()} />
            <DetailRow label="Sanitized" value={job.records_sanitized.toLocaleString()} />
            <DetailRow label="Failed" value={job.records_failed.toLocaleString()} />
          </div>

          {/* Source File section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Source File</SectionLabel>
            <p
              style={{
                fontSize: '13px',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                wordBreak: 'break-all',
                margin: 0,
              }}
            >
              {job.source}
            </p>
            <OpenFolderButton onClick={() => apiClient.openDirectory(parentDir(job.source))} />
          </div>

          {/* Sanitized Output section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Sanitized Output</SectionLabel>
            <p
              style={{
                fontSize: '13px',
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                wordBreak: 'break-all',
                margin: 0,
              }}
            >
              {job.output_path}
            </p>
            <OpenFolderButton onClick={() => apiClient.openDirectory(parentDir(job.output_path))} />
          </div>

          {/* Mapping section */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <SectionLabel>Mapping</SectionLabel>
            {job.mapping_name ? (
              <>
                {onViewMapping && job.mapping_id ? (
                  <button
                    type="button"
                    onClick={() => onViewMapping(job.mapping_id!)}
                    style={{
                      fontSize: '14px',
                      color: 'var(--primary-color)',
                      margin: 0,
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                      textAlign: 'left',
                      textDecoration: 'underline',
                      fontWeight: 500,
                    }}
                  >
                    {job.mapping_name}
                  </button>
                ) : (
                  <p style={{ fontSize: '14px', color: 'var(--text-primary)', margin: 0 }}>
                    {job.mapping_name}
                  </p>
                )}
                {job.mapping_id && (
                  <p
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      fontFamily: 'monospace',
                      margin: 0,
                    }}
                  >
                    {job.mapping_id}
                  </p>
                )}
              </>
            ) : job.mapping_id ? (
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  fontFamily: 'monospace',
                  margin: 0,
                }}
              >
                {job.mapping_id}
              </p>
            ) : (
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0 }}>
                No custom mapping (default rules)
              </p>
            )}
          </div>

          {/* Errors section */}
          {job.errors.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <SectionLabel>Errors</SectionLabel>
              <div
                style={{
                  backgroundColor: 'var(--danger-bg)',
                  border: '1px solid var(--danger-border)',
                  borderRadius: '8px',
                  padding: '12px',
                }}
              >
                {job.errors.map((err, i) => (
                  <p
                    key={i}
                    style={{
                      fontSize: '13px',
                      color: 'var(--danger-color)',
                      margin: i > 0 ? '8px 0 0 0' : 0,
                      wordBreak: 'break-word',
                    }}
                  >
                    {err}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Section label heading used within the drawer.
 */
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontSize: '11px',
        fontWeight: 600,
        color: 'var(--text-secondary)',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
      }}
    >
      {children}
    </span>
  );
}

/**
 * Label + value row for detail display.
 */
function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{label}</span>
      <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{value}</span>
    </div>
  );
}

/**
 * Button to open a folder in the system file manager.
 */
function OpenFolderButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      className="btn btn-secondary"
      style={{
        padding: '6px 12px',
        fontSize: '13px',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        alignSelf: 'flex-start',
      }}
      onClick={onClick}
    >
      <FolderOpen size={14} />
      Open Folder
    </button>
  );
}
