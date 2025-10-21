import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSessionStorage, sessionStorage } from './useSessionStorage';
import { Message } from '../api/backend/chat';

interface UseSessionManagerReturn {
  currentSessionId: string;
  isInitializing: boolean;
  initError: Error | null;
  sessions: any[];
  createNewSession: () => Promise<void>;
  switchSession: (sessionId: string) => void;
  removeSession: (sessionId: string) => void;
  retryInitialization: () => Promise<void>;
  updateSessionMetadata: (sessionId: string, messageCount: number, firstQuestion?: string) => void;
}

/**
 * Full mode session manager - uses backend sessions with localStorage cache
 */
export const useSessionManagerFull = (): UseSessionManagerReturn => {
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<Error | null>(null);

  const queryClient = useQueryClient();
  const {
    sessions,
    createSession,
    updateSessionMetadata,
    deleteSession: deleteStoredSession,
  } = useSessionStorage();

  const initializeSession = useCallback(async () => {
    setIsInitializing(true);
    setInitError(null);

    try {
      const storedSessionId = sessionStorage.getActiveSessionId(false);
      const storedSessions = sessionStorage.getSessions(false);

      if (storedSessionId && storedSessions.find(s => s.sessionId === storedSessionId)) {
        // Load existing session from localStorage
        setCurrentSessionId(storedSessionId);
        const storedMessages = sessionStorage.getMessages(storedSessionId, false);
        const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
        queryClient.setQueryData<Message[]>(['messages', storedSessionId], sortedMessages);
      } else {
        // Create new backend session
        const newSession = await createSession();
        setCurrentSessionId(newSession.sessionId);
        sessionStorage.setActiveSessionId(newSession.sessionId, false);
        queryClient.setQueryData<Message[]>(['messages', newSession.sessionId], []);
      }

      setIsInitializing(false);
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setInitError(error instanceof Error ? error : new Error('Failed to initialize session'));
      setIsInitializing(false);
    }
  }, [createSession, queryClient]);

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const createNewSession = useCallback(async () => {
    try {
      const newSession = await createSession();
      setCurrentSessionId(newSession.sessionId);
      sessionStorage.setActiveSessionId(newSession.sessionId, false);
      queryClient.setQueryData<Message[]>(['messages', newSession.sessionId], []);
    } catch (error) {
      console.error('Failed to create new session:', error);
      throw error;
    }
  }, [createSession, queryClient]);

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
    sessionStorage.setActiveSessionId(sessionId, false);

    const storedMessages = sessionStorage.getMessages(sessionId, false);
    const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
    queryClient.setQueryData<Message[]>(['messages', sessionId], sortedMessages);
  }, [queryClient]);

  const removeSession = useCallback((sessionId: string) => {
    const currentSessions = sessionStorage.getSessions(false);
    deleteStoredSession(sessionId);
    queryClient.removeQueries({ queryKey: ['messages', sessionId] });

    if (sessionId === currentSessionId) {
      const remainingSessions = currentSessions.filter(s => s.sessionId !== sessionId);

      if (remainingSessions.length > 0) {
        switchSession(remainingSessions[0].sessionId);
      } else {
        createNewSession();
      }
    }
  }, [currentSessionId, deleteStoredSession, queryClient, switchSession, createNewSession]);

  const retryInitialization = useCallback(async () => {
    await initializeSession();
  }, [initializeSession]);

  return {
    currentSessionId,
    isInitializing,
    initError,
    sessions,
    createNewSession,
    switchSession,
    removeSession,
    retryInitialization,
    updateSessionMetadata,
  };
};