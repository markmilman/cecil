import { FileFormat } from '@/types';

interface FormatSelectorProps {
  value: FileFormat | null;
  onChange: (format: FileFormat | null) => void;
  disabled?: boolean;
}

const FORMAT_OPTIONS: Array<{ value: FileFormat | null; label: string; description: string }> = [
  { value: null, label: 'Auto-detect', description: 'Detect format from file extension' },
  { value: FileFormat.JSONL, label: 'JSONL', description: 'JSON Lines format' },
  { value: FileFormat.CSV, label: 'CSV', description: 'Comma-separated values' },
  { value: FileFormat.PARQUET, label: 'Parquet', description: 'Apache Parquet columnar format' },
];

/**
 * FormatSelector component
 *
 * Provides a radio button group for selecting the file format for data ingestion.
 * Supports auto-detection or explicit format selection (JSONL, CSV, Parquet).
 */
export function FormatSelector({ value, onChange, disabled = false }: FormatSelectorProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6">
      <fieldset disabled={disabled}>
        <legend className="text-sm font-medium text-primary mb-3">File Format</legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {FORMAT_OPTIONS.map((option) => {
            const isSelected = value === option.value;
            const optionId = `format-${option.value ?? 'auto'}`;
            return (
              <label
                key={optionId}
                htmlFor={optionId}
                className={`
                  flex flex-col items-center p-3 rounded-lg border-2 cursor-pointer
                  transition-colors duration-150
                  ${isSelected
                    ? 'border-accent bg-indigo-50 text-accent'
                    : 'border-slate-200 hover:border-slate-300 text-primary'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <input
                  id={optionId}
                  type="radio"
                  name="file-format"
                  value={option.value ?? 'auto'}
                  checked={isSelected}
                  onChange={() => onChange(option.value)}
                  disabled={disabled}
                  className="sr-only"
                />
                <span className="font-medium text-sm">{option.label}</span>
                <span className="text-xs text-muted mt-1">{option.description}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    </div>
  );
}
