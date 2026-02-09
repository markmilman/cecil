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
 * FormatSelector component (v2)
 *
 * Provides a radio button group for selecting the file format for data ingestion.
 * V2: larger touch targets, hover shadow, enhanced selected state with scale.
 */
export function FormatSelector({ value, onChange, disabled = false }: FormatSelectorProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm hover:shadow-md transition-shadow duration-200">
      <fieldset disabled={disabled}>
        <legend className="text-sm font-semibold text-primary mb-4">File Format</legend>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {FORMAT_OPTIONS.map((option) => {
            const isSelected = value === option.value;
            const optionId = `format-${option.value ?? 'auto'}`;
            return (
              <label
                key={optionId}
                htmlFor={optionId}
                className={`
                  flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer
                  transition-all duration-200
                  focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo-600
                  ${isSelected
                    ? 'border-accent bg-indigo-50 text-accent scale-105 shadow-md'
                    : 'border-slate-200 hover:border-indigo-200 hover:shadow-sm text-primary'
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
                <span className="font-semibold text-sm">{option.label}</span>
                <span className="text-xs text-slate-600 mt-1 text-center">{option.description}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    </div>
  );
}
