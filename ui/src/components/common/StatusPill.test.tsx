import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusPill } from './StatusPill';

describe('StatusPill', () => {
  it('renders the label text', () => {
    render(<StatusPill label="Completed" variant="success" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('applies success variant styles', () => {
    render(<StatusPill label="Completed" variant="success" />);
    const pill = screen.getByText('Completed');
    expect(pill.style.backgroundColor).toBe('var(--success-bg)');
    expect(pill.style.color).toBe('var(--success-color)');
  });

  it('applies danger variant styles', () => {
    render(<StatusPill label="PII Detected" variant="danger" />);
    const pill = screen.getByText('PII Detected');
    expect(pill.style.backgroundColor).toBe('var(--danger-bg)');
    expect(pill.style.color).toBe('var(--danger-color)');
  });

  it('renders as an inline-block element with pill shape', () => {
    render(<StatusPill label="Test" variant="success" />);
    const pill = screen.getByText('Test');
    expect(pill.style.borderRadius).toBe('99px');
    expect(pill.style.display).toBe('inline-block');
  });
});
