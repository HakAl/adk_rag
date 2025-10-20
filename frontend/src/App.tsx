import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './components/Chat';
import { SettingsPanel } from './components/SettingsPanel';
import { Layout } from './components/layout/Layout';
import { SettingsProvider } from './contexts/SettingsContext';
import { AuthProvider } from './contexts/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { VerifyEmailSentPage } from './pages/VerifyEmailSentPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useSettings } from './hooks/useSettings';
import { useHealthCheck } from './hooks/useHealthCheck';

const queryClient = new QueryClient();

function AppContent() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { health, error, loading } = useHealthCheck();
  const { settings, updateTheme, updateFontSize, resetSettings } = useSettings();

  return (
    <Layout
      loading={loading}
      error={error}
      onSettingsClick={() => setSettingsOpen(true)}
      onSettingsClose={() => setSettingsOpen(false)}
      settingsOpen={settingsOpen}
    >
      {health && (
        <>
          <Chat />
          <SettingsPanel
            settings={settings}
            onThemeChange={updateTheme}
            onFontSizeChange={updateFontSize}
            onReset={resetSettings}
            isOpen={settingsOpen}
            onClose={() => setSettingsOpen(false)}
            health={health}
          />
        </>
      )}
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SettingsProvider>
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/verify-email-sent" element={<VerifyEmailSentPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />

              {/* Protected routes */}
              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <AppContent />
                  </ProtectedRoute>
                }
              />

              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/chat" replace />} />
            </Routes>
          </BrowserRouter>
        </SettingsProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;