import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './components/Chat';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';

interface HealthResponse {
  status: string;
  version: string;
}

const queryClient = new QueryClient();

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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
      <div className="dark h-screen bg-background flex flex-col">
        {/* Skip to main content link for keyboard navigation */}
        <a
          href="#main-content"
          className="skip-link"
        >
          Skip to main content
        </a>

        {/* Header */}
        <header className="flex-shrink-0 border-b border-border">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-primary">VIBE Agent</h1>

              {health && (
                <div className="flex items-center gap-4 text-sm" role="status" aria-live="polite">
                  <span className="text-muted-foreground">Status:</span>
                  <span className="text-green-500 font-semibold" aria-label="System status">
                    {health.status}
                  </span>
                  <span className="text-muted-foreground">Version:</span>
                  <span className="text-muted-foreground" aria-label="Application version">
                    {process.env.REACT_APP_VERSION || '0.1.0'}
                  </span>
                </div>
              )}
            </div>

            {loading && (
              <p className="text-muted-foreground mt-2" role="status" aria-live="polite">
                Loading...
              </p>
            )}

            {error && (
              <Card className="border-red-500 bg-red-950/20 mt-4" role="alert">
                <CardHeader>
                  <CardTitle className="text-red-500">Error</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-red-400">{error}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </header>

        {/* Chat Area - Full width, remaining height */}
        {health && (
          <div className="flex-1 px-4 py-4 min-h-0 overflow-hidden">
            <Chat />
          </div>
        )}
      </div>
    </QueryClientProvider>
  );
}

export default App;