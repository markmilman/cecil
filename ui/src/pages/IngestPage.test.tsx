import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { IngestPage } from './IngestPage';

describe('IngestPage', () => {
  it('renders the page heading', () => {
    render(<BrowserRouter><IngestPage /></BrowserRouter>);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('renders the file picker', () => {
    render(<BrowserRouter><IngestPage /></BrowserRouter>);
    expect(screen.getByLabelText('File Path')).toBeInTheDocument();
  });

  it('renders the format selector', () => {
    render(<BrowserRouter><IngestPage /></BrowserRouter>);
    expect(screen.getByText('File Format')).toBeInTheDocument();
  });

  it('renders the submit button', () => {
    render(<BrowserRouter><IngestPage /></BrowserRouter>);
    expect(screen.getByText('Start Scan')).toBeInTheDocument();
  });

  it('disables submit button when file path is empty', () => {
    render(<BrowserRouter><IngestPage /></BrowserRouter>);
    expect(screen.getByText('Start Scan')).toBeDisabled();
  });
});
