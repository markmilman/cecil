import { UploadIcon } from 'lucide-react';

interface FilePickerCardProps {
  value: string;
  onChange: (path: string) => void;
  disabled?: boolean;
}

/**
 * FilePickerCard component
 *
 * Provides a text input for specifying a file path, with a visual drop zone hint.
 * Used in the IngestPage for selecting local data files to sanitize.
 */
export function FilePickerCard({ value, onChange, disabled = false }: FilePickerCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6">
      <label htmlFor="file-path" className="block text-sm font-medium text-primary mb-2">
        File Path
      </label>
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <input
            id="file-path"
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="/path/to/data.jsonl"
            className="w-full px-4 py-3 border border-slate-200 rounded-lg text-primary
              placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-accent
              focus:border-transparent disabled:bg-slate-50 disabled:text-muted"
          />
        </div>
      </div>

      {/* Visual drop zone hint */}
      <div className="mt-4 flex items-center justify-center p-6 border-2 border-dashed
        border-slate-200 rounded-lg text-muted">
        <div className="text-center">
          <UploadIcon className="h-8 w-8 mx-auto mb-2 text-slate-300" />
          <p className="text-sm">Enter the full file path above</p>
          <p className="text-xs text-slate-400 mt-1">Supports JSONL, CSV, and Parquet files</p>
        </div>
      </div>
    </div>
  );
}
