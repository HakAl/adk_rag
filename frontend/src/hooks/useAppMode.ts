import { useState, useEffect } from 'react';
import { detectMode, AppMode } from '../config/mode';
import { healthApi, HealthResponse } from '../api/health';

interface UseAppModeReturn {
  mode: AppMode;
  health: HealthResponse | null;
  loading: boolean;
  backendWaking: boolean;
}

export const useAppMode = (): UseAppModeReturn => {
  const [mode, setMode] = useState<AppMode>('lite');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [backendWaking, setBackendWaking] = useState<boolean>(false);

  useEffect(() => {
    const initializeMode = async () => {
      setLoading(true);

      // Detect mode (this will trigger health check to wake backend)
      const detectedMode = await detectMode();
      setMode(detectedMode);

      // If full mode, fetch full health info
      if (detectedMode === 'full') {
        try {
          const healthData = await healthApi.check();
          setHealth(healthData);
        } catch (error) {
          // Health check failed, stay in full mode but no health data
          console.error('Health check failed:', error);
        }
      } else {
        // In lite mode, show backend waking indicator briefly
        setBackendWaking(true);
        setTimeout(() => setBackendWaking(false), 3000);
      }

      setLoading(false);
    };

    initializeMode();
  }, []);

  return {
    mode,
    health,
    loading,
    backendWaking,
  };
};