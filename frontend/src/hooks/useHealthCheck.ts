import { useState, useEffect } from 'react';
import { healthApi, HealthResponse } from '../api/health';

interface UseHealthCheckReturn {
  health: HealthResponse | null;
  error: string | null;
  loading: boolean;
  refetch: () => Promise<void>;
}

export const useHealthCheck = (): UseHealthCheckReturn => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await healthApi.check();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return {
    health,
    error,
    loading,
    refetch: fetchHealth,
  };
};