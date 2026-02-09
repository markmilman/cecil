import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from '@/components/common/Shell';
import { IngestPage } from '@/pages/IngestPage';
import { MappingPage } from '@/pages/MappingPage';
import { AuditPage } from '@/pages/AuditPage';

/**
 * Main App component
 *
 * Sets up routing and the overall application structure.
 * Default route redirects to the Ingest page.
 */
export function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/ingest" element={<IngestPage />} />
          <Route path="/mapping" element={<MappingPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/" element={<Navigate to="/ingest" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}
