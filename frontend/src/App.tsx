import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './components/Chat';
import './App.css';

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
      <div className="App">
        <header className="App-header">
          <h1>VIBE Agent Frontend</h1>

          {loading && <p>Loading...</p>}

          {error && (
            <div className="error">
              <h2>Error</h2>
              <p>{error}</p>
            </div>
          )}

          {health && (
            <div className="health">
              <h2>API Health Check</h2>
              <p>Status: <span className="status-healthy">{health.status}</span></p>
              <p>Version: {health.version}</p>
            </div>
          )}

          {health && <Chat />}
        </header>
      </div>
    </QueryClientProvider>
  );
}

export default App;