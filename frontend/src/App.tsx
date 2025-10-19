import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './components/Chat';
import { SettingsPanel } from './components/SettingsPanel';
import { Layout } from './components/layout/Layout';
import { SettingsProvider } from './contexts/SettingsContext';
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
      <SettingsProvider>
        <AppContent />
      </SettingsProvider>
    </QueryClientProvider>
  );
}

export default App;