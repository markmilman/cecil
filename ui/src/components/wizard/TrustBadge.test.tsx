import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TrustBadge } from './TrustBadge';

describe('TrustBadge', () => {
  it('renders the trust text', () => {
    render(<TrustBadge />);
    expect(screen.getByText('Data stays local')).toBeInTheDocument();
  });

  it('renders with the lock icon', () => {
    const { container } = render(<TrustBadge />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
