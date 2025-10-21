import { useQuery } from '@tanstack/react-query';
import { chatApi } from '../api/backend/chat';
import { useSessionLite } from './useSession.lite';
import { useAppMode } from './useAppMode';

/**
 * Full mode session hook
 * Calls backend API to create/retrieve session
 */
export const useSessionFull = (userId: string = 'web_user') => {
  return useQuery({
    queryKey: ['session', userId],
    queryFn: () => chatApi.createSession(userId),
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
};

/**
 * Smart router hook for session
 * Automatically routes to full or lite version based on app mode
 */
export const useSession = (userId: string = 'web_user') => {
  const { mode } = useAppMode();

  if (mode === 'lite') {
    return useSessionLite(userId);
  }

  return useSessionFull(userId);
};