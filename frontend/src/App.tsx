import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Settings as SettingsIcon } from 'lucide-react';
import { Chat } from './components/Chat';
import { SettingsPanel } from './components/SettingsPanel';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { useSettings } from './hooks/useSettings';

interface HealthResponse {
  status: string;
  version: string;
}

const queryClient = new QueryClient();

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const {
    settings,
    updateTheme,
    updateFontSize,
    resetSettings,
  } = useSettings();

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: HealthResponse = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <div className="h-screen bg-background flex flex-col">
        {/* Skip to main content link for keyboard navigation */}
        <a
          href="#main-content"
          className="skip-link"
        >
          Skip to main content
        </a>

        {/* Header - Mobile responsive */}
        <header className="flex-shrink-0 border-b border-border">
          <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
              <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">
                VIBE Agent
              </h1>

              <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
                {/* Settings Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSettingsOpen(true)}
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  aria-label="Open settings"
                  aria-expanded={settingsOpen}
                >
                  <SettingsIcon className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />
                </Button>
              </div>
            </div>

            {loading && (
              <p className="text-muted-foreground mt-2 text-sm" role="status" aria-live="polite">
                Loading...
              </p>
            )}

            {error && (
              <Card className="border-red-500 bg-red-950/20 mt-3 sm:mt-4" role="alert">
                <CardHeader className="p-3 sm:p-6">
                  <CardTitle className="text-red-500 text-base sm:text-lg">Error</CardTitle>
                </CardHeader>
                <CardContent className="p-3 sm:p-6 pt-0">
                  <p className="text-red-400 text-sm">{error}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </header>

        {/* Chat Area - Full width, remaining height - Mobile optimized */}
        {health && (
          <div className="flex-1 px-2 sm:px-4 py-2 sm:py-4 min-h-0 overflow-hidden relative">
            <Chat />

            {/* Settings Panel */}
            <SettingsPanel
              settings={settings}
              onThemeChange={updateTheme}
              onFontSizeChange={updateFontSize}
              onReset={resetSettings}
              isOpen={settingsOpen}
              onClose={() => setSettingsOpen(false)}
              health={health}
            />
          </div>
        )}
      </div>
    </QueryClientProvider>
  );
}

export default App;