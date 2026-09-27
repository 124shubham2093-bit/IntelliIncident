import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/Layout/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { IncidentsPage } from '@/pages/IncidentsPage';
import { IncidentDetailsPage } from '@/pages/IncidentDetailsPage';
import { InvestigationPage } from '@/pages/InvestigationPage';
import { MLAnalyticsPage } from '@/pages/MLAnalyticsPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { TopologyPage } from '@/pages/TopologyPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/incidents/:id" element={<IncidentDetailsPage />} />
          <Route path="/investigation" element={<InvestigationPage />} />
          <Route path="/topology" element={<TopologyPage />} />
          <Route path="/ml-analytics" element={<MLAnalyticsPage />} />
          <Route path="/fuzzy-risk" element={<Navigate to="/investigation" replace />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
