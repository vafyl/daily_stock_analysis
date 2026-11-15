import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ReportSite } from './ReportSite';
import './site.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ReportSite />
  </StrictMode>,
);
