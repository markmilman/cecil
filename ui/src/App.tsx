import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from '@/components/common/Shell';
import { MappingPage } from '@/pages/MappingPage';
import { AuditPage } from '@/pages/AuditPage';

/**
 * Main App component
 *
 * Sets up routing and the overall application structure.
 * Default route redirects to the Mapping page.
 */
export function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/mapping" element={<MappingPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/" element={<Navigate to="/mapping" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}
