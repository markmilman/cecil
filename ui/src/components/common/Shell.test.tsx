import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Shell } from './Shell';

/**
 * Test suite for Shell layout component
 */
describe('Shell', () => {
  it('renders the Cecil branding', () => {
    render(
      <BrowserRouter>
        <Shell>
          <div>Test content</div>
        </Shell>
      </BrowserRouter>
    );

    expect(screen.getByText('Cecil')).toBeInTheDocument();
    expect(screen.getByText('Data Sanitizer & Cost Optimizer')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Shell>
          <div>Test content</div>
        </Shell>
      </BrowserRouter>
    );

    expect(screen.getByText('Mapping')).toBeInTheDocument();
    expect(screen.getByText('Audit')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(
      <BrowserRouter>
        <Shell>
          <div>Test child content</div>
        </Shell>
      </BrowserRouter>
    );

    expect(screen.getByText('Test child content')).toBeInTheDocument();
  });

  it('displays the tagline', () => {
    render(
      <BrowserRouter>
        <Shell>
          <div>Test content</div>
        </Shell>
      </BrowserRouter>
    );

    expect(screen.getByText('Local-First, Cloud-Optional')).toBeInTheDocument();
  });
});
