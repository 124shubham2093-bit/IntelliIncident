import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * FuzzyRiskPage (Deprecated)
 * The standalone manual fuzzy-risk workspace has been deprecated and removed.
 * Mamdani fuzzy risk assessment is strictly system-generated from runtime
 * incident telemetry and displayed read-only on IncidentDetailsPage and InvestigationPage.
 */
export const FuzzyRiskPage: React.FC = () => {
  return <Navigate to="/investigation" replace />;
};

export default FuzzyRiskPage;
