import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSessionStorage, sessionStorage } from './useSessionStorage';
import { Message } from '../api/backend/chat';
import { v4 as uuidv4 } from 'uuid';

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
 * Lite mode session manager - handles client-side sessions only
 * All session data stored in-memory, no backend calls
 */
export const useSessionManagerLite = (): UseSessionManagerReturn => {
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<Error | null>(null);

  const queryClient = useQueryClient();
  const {
    sessions,
    updateSessionMetadata,
    deleteSession: deleteStoredSession,
  } = useSessionStorage();

  const initializeSession = useCallback(async () => {
    setIsInitializing(true);
    setInitError(null);

    try {
      const storedSessionId = sessionStorage.getActiveSessionId(true);
      const storedSessions = sessionStorage.getSessions(true);

      if (storedSessionId && storedSessions.find(s => s.sessionId === storedSessionId)) {
        // Load existing session from in-memory storage
        setCurrentSessionId(storedSessionId);
        const storedMessages = sessionStorage.getMessages(storedSessionId, true);
        const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
        queryClient.setQueryData<Message[]>(['messages', storedSessionId], sortedMessages);
      } else {
        // Create new client-side session (no backend call)
        const newSessionId = `lite-${uuidv4()}`;
        const newSession = {
          sessionId: newSessionId,
          title: 'New Chat',
          createdAt: Date.now(),
          lastMessageAt: Date.now(),
          messageCount: 0,
        };
        sessionStorage.addSession(newSession, true);
        setCurrentSessionId(newSessionId);
        sessionStorage.setActiveSessionId(newSessionId, true);
        queryClient.setQueryData<Message[]>(['messages', newSessionId], []);
      }

      setIsInitializing(false);
    } catch (error) {
      console.error('Failed to initialize session:', error);
      setInitError(error instanceof Error ? error : new Error('Failed to initialize session'));
      setIsInitializing(false);
    }
  }, [queryClient]);

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const createNewSession = useCallback(async () => {
    try {
      const newSessionId = `lite-${uuidv4()}`;
      const newSession = {
        sessionId: newSessionId,
        title: 'New Chat',
        createdAt: Date.now(),
        lastMessageAt: Date.now(),
        messageCount: 0,
      };
      sessionStorage.addSession(newSession, true);
      setCurrentSessionId(newSessionId);
      sessionStorage.setActiveSessionId(newSessionId, true);
      queryClient.setQueryData<Message[]>(['messages', newSessionId], []);
    } catch (error) {
      console.error('Failed to create new session:', error);
      throw error;
    }
  }, [queryClient]);

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
    sessionStorage.setActiveSessionId(sessionId, true);

    const storedMessages = sessionStorage.getMessages(sessionId, true);
    const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
    queryClient.setQueryData<Message[]>(['messages', sessionId], sortedMessages);
  }, [queryClient]);

  const removeSession = useCallback((sessionId: string) => {
    const currentSessions = sessionStorage.getSessions(true);
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