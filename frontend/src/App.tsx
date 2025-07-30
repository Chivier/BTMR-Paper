import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { HomePage } from '@/pages/HomePage';
import { PapersPage } from '@/pages/PapersPage';
import { ProcessPaperPage } from '@/pages/ProcessPaperPage';
import { PaperDetailPage } from '@/pages/PaperDetailPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { NotificationProvider } from '@/context/NotificationContext';

function App() {
  return (
    <NotificationProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/process" element={<ProcessPaperPage />} />
          <Route path="/papers" element={<PapersPage />} />
          <Route path="/papers/:paperId" element={<PaperDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </NotificationProvider>
  );
}

export default App;
