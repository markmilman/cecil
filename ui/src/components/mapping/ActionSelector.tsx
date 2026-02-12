/**
 * ActionSelector component
 *
 * Segmented button group for selecting a redaction action.
 * Each action has a distinct color: REDACT (red), MASK (amber),
 * HASH (blue), KEEP (green). The active button has a filled
 * background; inactive buttons have border-only styling.
 */

import { RedactionAction } from '@/types';

interface ActionSelectorProps {
  value: RedactionAction;
  onChange: (action: RedactionAction) => void;
  disabled?: boolean;
}

interface ActionConfig {
  label: string;
  activeBg: string;
  activeText: string;
  hoverBg: string;
  borderColor: string;
  textColor: string;
}

const ACTION_CONFIG: Record<RedactionAction, ActionConfig> = {
  [RedactionAction.REDACT]: {
    label: 'Redact',
    activeBg: 'var(--danger-color)',
    activeText: '#FFFFFF',
    hoverBg: 'var(--danger-bg)',
    borderColor: 'var(--danger-color)',
    textColor: 'var(--danger-color)',
  },
  [RedactionAction.MASK]: {
    label: 'Mask',
    activeBg: '#D97706',
    activeText: '#FFFFFF',
    hoverBg: '#FFFBEB',
    borderColor: '#D97706',
    textColor: '#D97706',
  },
  [RedactionAction.HASH]: {
    label: 'Hash',
    activeBg: 'var(--primary-color)',
    activeText: '#FFFFFF',
    hoverBg: 'var(--primary-light)',
    borderColor: 'var(--primary-color)',
    textColor: 'var(--primary-color)',
  },
  [RedactionAction.KEEP]: {
    label: 'Keep',
    activeBg: 'var(--success-color)',
    activeText: '#FFFFFF',
    hoverBg: 'var(--success-bg)',
    borderColor: 'var(--success-color)',
    textColor: 'var(--success-color)',
  },
};

const ACTIONS = [
  RedactionAction.REDACT,
  RedactionAction.MASK,
  RedactionAction.HASH,
  RedactionAction.KEEP,
] as const;

export function ActionSelector({ value, onChange, disabled = false }: ActionSelectorProps) {
  return (
    <div className="inline-flex rounded-md" role="group" aria-label="Redaction action">
      {ACTIONS.map((action, index) => {
        const config = ACTION_CONFIG[action];
        const isActive = value === action;
        const isFirst = index === 0;
        const isLast = index === ACTIONS.length - 1;

        return (
          <button
            key={action}
            type="button"
            disabled={disabled}
            onClick={() => onChange(action)}
            aria-pressed={isActive}
            style={{
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: disabled ? 'not-allowed' : 'pointer',
              opacity: disabled ? 0.5 : 1,
              border: `1px solid ${config.borderColor}`,
              borderLeft: isFirst ? `1px solid ${config.borderColor}` : 'none',
              borderRadius: isFirst
                ? '4px 0 0 4px'
                : isLast
                  ? '0 4px 4px 0'
                  : '0',
              backgroundColor: isActive ? config.activeBg : 'transparent',
              color: isActive ? config.activeText : config.textColor,
              transition: 'background-color 0.15s, color 0.15s',
            }}
            onMouseEnter={(e) => {
              if (!isActive && !disabled) {
                e.currentTarget.style.backgroundColor = config.hoverBg;
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive && !disabled) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
          >
            {config.label}
          </button>
        );
      })}
    </div>
  );
}
