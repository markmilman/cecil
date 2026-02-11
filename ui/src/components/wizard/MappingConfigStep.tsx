import { useState, useCallback } from 'react';
import { FileTextIcon, PlusCircleIcon, FolderIcon, AlertCircleIcon, CheckCircleIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { apiClient } from '@/lib/apiClient';
import type { UploadedFileInfo, MappingConfigResponse } from '@/types';

interface MappingConfigStepProps {
  files: UploadedFileInfo[];
  onReady: (mappingId: string, outputDir: string) => void;
  onBack: () => void;
  onCreateMapping: (source: string) => void;
  initialMappingId?: string | null;
}

/**
 * MappingConfigStep component (Wizard Step 3)
 *
 * Lets the user load an existing mapping YAML file or open the
 * mapping editor to create new rules. Also collects the output
 * directory before starting sanitization.
 */
export function MappingConfigStep({
  files,
  onReady,
  onBack,
  onCreateMapping,
  initialMappingId,
}: MappingConfigStepProps) {
  const [mappingId, setMappingId] = useState<string | null>(initialMappingId ?? null);
  const [yamlPath, setYamlPath] = useState('');
  const [outputDir, setOutputDir] = useState('~/.cecil/output/');
  const [outputDirError, setOutputDirError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(
    initialMappingId ? 'Mapping loaded from editor.' : null,
  );

  const handleLoadYaml = useCallback(async () => {
    if (!yamlPath.trim()) return;
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response: MappingConfigResponse = await apiClient.loadMappingYaml(yamlPath.trim());
      setMappingId(response.mapping_id);
      setSuccessMessage(`Mapping loaded: ${response.mapping_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load mapping YAML');
    } finally {
      setIsLoading(false);
    }
  }, [yamlPath]);

  const validateOutputDir = useCallback((path: string): string | null => {
    const trimmed = path.trim();
    if (!trimmed) {
      return 'Output directory cannot be empty';
    }
    // Check for invalid characters (Windows-style invalid chars that are also problematic on Unix)
    const invalidChars = /[<>:"|?*\0]/;
    if (invalidChars.test(trimmed)) {
      return 'Output directory contains invalid characters';
    }
    return null;
  }, []);

  const handleOutputDirChange = useCallback((value: string) => {
    setOutputDir(value);
    setOutputDirError(validateOutputDir(value));
  }, [validateOutputDir]);

  const handleStartSanitization = useCallback(() => {
    if (mappingId && outputDir.trim() && !outputDirError) {
      onReady(mappingId, outputDir.trim());
    }
  }, [mappingId, outputDir, outputDirError, onReady]);

  return (
    <div>
      <WizardHeader
        title="Configure Mapping"
        subtitle="Load an existing mapping or create new rules for your data fields."
      />

      {/* Error banner */}
      {error && (
        <div
          className="flex items-center gap-2"
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: '8px',
            marginBottom: '16px',
            color: 'var(--danger-color)',
            fontSize: '14px',
          }}
        >
          <AlertCircleIcon className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Success banner */}
      {successMessage && (
        <div
          className="flex items-center gap-2"
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: '8px',
            marginBottom: '16px',
            color: 'var(--success-color)',
            fontSize: '14px',
          }}
        >
          <CheckCircleIcon className="h-4 w-4" />
          {successMessage}
        </div>
      )}

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Two-column card grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
            marginBottom: '32px',
          }}
        >
          {/* Card A: Load Existing Mapping */}
          <div
            style={{
              padding: '24px',
              backgroundColor: 'var(--bg-body)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
            }}
          >
            <div className="flex items-center gap-2" style={{ marginBottom: '16px' }}>
              <FileTextIcon className="h-5 w-5" style={{ color: 'var(--primary-color)' }} />
              <h3
                style={{
                  margin: 0,
                  fontSize: '16px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                Load Existing Mapping
              </h3>
            </div>
            <div className="flex" style={{ gap: '8px', marginBottom: '8px' }}>
              <input
                type="text"
                value={yamlPath}
                onChange={(e) => setYamlPath(e.target.value)}
                placeholder="/path/to/mapping.yaml"
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  fontSize: '14px',
                  color: 'var(--text-primary)',
                  backgroundColor: 'var(--bg-card, white)',
                }}
              />
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleLoadYaml}
                disabled={isLoading || !yamlPath.trim()}
                style={{ padding: '8px 16px', fontSize: '14px' }}
              >
                {isLoading ? 'Loading...' : 'Load'}
              </button>
            </div>
          </div>

          {/* Card B: Create New Mapping */}
          <div
            style={{
              padding: '24px',
              backgroundColor: 'var(--bg-body)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
            }}
          >
            <div className="flex items-center gap-2" style={{ marginBottom: '16px' }}>
              <PlusCircleIcon className="h-5 w-5" style={{ color: 'var(--primary-color)' }} />
              <h3
                style={{
                  margin: 0,
                  fontSize: '16px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                Create New Mapping
              </h3>
            </div>
            <p
              style={{
                margin: '0 0 16px',
                fontSize: '14px',
                color: 'var(--text-secondary)',
              }}
            >
              Open the mapping editor to create rules for your data fields.
            </p>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                if (files.length > 0 && files[0]?.path) {
                  onCreateMapping(files[0].path);
                }
              }}
              disabled={files.length === 0}
            >
              Open Mapping Editor
            </button>
          </div>
        </div>

        {/* Output Directory */}
        <div style={{ marginBottom: '32px' }}>
          <div className="flex items-center gap-2" style={{ marginBottom: '8px' }}>
            <FolderIcon className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
            <label
              htmlFor="output-dir"
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary)',
              }}
            >
              Output Directory
            </label>
          </div>
          <input
            id="output-dir"
            type="text"
            value={outputDir}
            onChange={(e) => handleOutputDirChange(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: `1px solid ${outputDirError ? 'var(--danger-border)' : 'var(--border-color)'}`,
              borderRadius: '6px',
              fontSize: '14px',
              color: 'var(--text-primary)',
              backgroundColor: 'var(--bg-card, white)',
              boxSizing: 'border-box',
            }}
          />
          {outputDirError ? (
            <p
              style={{
                margin: '4px 0 0',
                fontSize: '12px',
                color: 'var(--danger-color)',
              }}
            >
              {outputDirError}
            </p>
          ) : (
            <p
              style={{
                margin: '4px 0 0',
                fontSize: '12px',
                color: 'var(--text-secondary)',
              }}
            >
              Sanitized files will be saved here
            </p>
          )}
        </div>

        {/* Footer Actions */}
        <div
          className="flex items-center justify-end"
          style={{
            gap: '12px',
            borderTop: '1px solid var(--border-color)',
            paddingTop: '24px',
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBack}
          >
            Back
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleStartSanitization}
            disabled={!mappingId || !outputDir.trim() || !!outputDirError}
          >
            Start Sanitization
          </button>
        </div>
      </div>
    </div>
  );
}
