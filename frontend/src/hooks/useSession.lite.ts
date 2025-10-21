import { useQuery } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';

interface Session {
  sessionId: string;
  userId: string;
}

/**
 * Lite mode session hook - generates client-side session IDs
 * No backend calls, sessions exist only in browser
 */
export const useSessionLite = (userId: string = 'web_user') => {
  return useQuery({
    queryKey: ['session', userId],
    queryFn: (): Session => {
      // Generate a client-side session ID
      const sessionId = `lite-${uuidv4()}`;

      return {
        sessionId,
        userId,
      };
    },
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
};