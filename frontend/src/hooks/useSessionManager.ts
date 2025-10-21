import { useSessionManagerFull } from './useSessionManager.full';
import { useSessionManagerLite } from './useSessionManager.lite';
import { useAppMode } from './useAppMode';

/**
 * Smart router hook for session manager
 * Automatically routes to full or lite version based on app mode
 */
export const useSessionManager = () => {
  const { mode } = useAppMode();

  if (mode === 'lite') {
    return useSessionManagerLite();
  }

  return useSessionManagerFull();
};