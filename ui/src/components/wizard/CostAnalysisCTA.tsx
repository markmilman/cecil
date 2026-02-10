interface CostAnalysisCTAProps {
  onGetReport?: () => void;
}

/**
 * Cost Analysis CTA card for the wizard completion view.
 *
 * Gradient background card with "RECOMMENDED" label, value propositions,
 * "Get Free Report" primary button, and trust text. This is the SaaS
 * lead capture surface per the "Safe-Pipe" conversion flow.
 */
export function CostAnalysisCTA({ onGetReport }: CostAnalysisCTAProps) {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, var(--cta-gradient-start) 0%, var(--cta-gradient-end) 100%)',
        border: '1px solid var(--primary-light)',
        borderRadius: '12px',
        padding: '32px',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '11px',
          fontWeight: 700,
          color: 'var(--primary-color)',
          letterSpacing: '1px',
          marginBottom: '8px',
        }}
      >
        RECOMMENDED
      </div>
      <div
        style={{
          color: 'var(--primary-color)',
          fontSize: '20px',
          fontWeight: 700,
          marginBottom: '12px',
        }}
      >
        Unlock 20% Cost Savings
      </div>
      <div
        style={{
          color: 'var(--text-primary)',
          opacity: 0.8,
          marginBottom: '24px',
        }}
      >
        Get a free report identifying model switching opportunities.
      </div>

      <div
        style={{
          textAlign: 'left',
          marginBottom: '20px',
          fontSize: '14px',
          color: 'var(--primary-hover)',
        }}
      >
        <div>&#10003; Detailed Spend Breakdown</div>
        <div>&#10003; Token Efficiency Analysis</div>
      </div>

      <button
        type="button"
        className="btn btn-primary"
        style={{ width: '100%', justifyContent: 'center' }}
        onClick={onGetReport}
      >
        Get Free Report
      </button>
      <div
        style={{
          fontSize: '11px',
          marginTop: '12px',
          color: 'var(--primary-color)',
          opacity: 0.8,
        }}
      >
        Metadata only. No sensitive data.
      </div>
    </div>
  );
}
