import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WizardHeader } from './WizardHeader';

describe('WizardHeader', () => {
  it('renders the title', () => {
    render(<WizardHeader title="Test Title" subtitle="Test subtitle" />);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<WizardHeader title="Test Title" subtitle="Test subtitle" />);
    expect(screen.getByText('Test subtitle')).toBeInTheDocument();
  });

  it('renders an action slot when provided', () => {
    render(
      <WizardHeader
        title="Title"
        subtitle="Subtitle"
        action={<button>Action</button>}
      />,
    );
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('does not render action slot when not provided', () => {
    const { container } = render(
      <WizardHeader title="Title" subtitle="Subtitle" />,
    );
    const buttons = container.querySelectorAll('button');
    expect(buttons).toHaveLength(0);
  });
});
