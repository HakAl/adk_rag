import { useState, useEffect, useCallback, useRef } from 'react';
import { Message } from '../api/backend/chat.ts';
import { chatApi } from '../api/backend/chat.ts';
import { useAppMode } from './useAppMode';

export interface SessionMetadata {
  sessionId: string;
  title: string;
  createdAt: number;
  lastMessageAt: number;
  messageCount: number;
}

const STORAGE_KEYS = {
  SESSIONS: 'chat_sessions',
  ACTIVE_SESSION: 'activeSessionId',
  getMessages: (sessionId: string) => `messages_${sessionId}`,
};

// SECURITY NOTE: We store session metadata differently based on mode:
// - Full mode: localStorage (no sensitive data, backend does all work)
// - Lite mode: in-memory only (user provides API keys, more sensitive)
// In both modes, actual session authentication is done via secure HttpOnly
// cookies that JavaScript cannot access. This provides CSRF protection and
// rate limiting for the backend API endpoints.

// Global in-memory storage for lite mode (persists across component remounts)
const inMemoryStorage = {
  sessions: [] as SessionMetadata[],
  messages: new Map<string, Message[]>(),
  activeSessionId: null as string | null,
};

export const sessionStorage = {
  getSessions: (isLiteMode: boolean): SessionMetadata[] => {
    if (isLiteMode) {
      return inMemoryStorage.sessions;
    }
    const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
    return data ? JSON.parse(data) : [];
  },

  saveSessions: (sessions: SessionMetadata[], isLiteMode: boolean) => {
    if (isLiteMode) {
      inMemoryStorage.sessions = sessions;
    } else {
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
    }
  },

  getMessages: (sessionId: string, isLiteMode: boolean): Message[] => {
    if (isLiteMode) {
      return inMemoryStorage.messages.get(sessionId) || [];
    }
    const data = localStorage.getItem(STORAGE_KEYS.getMessages(sessionId));
    return data ? JSON.parse(data) : [];
  },

  saveMessages: (sessionId: string, messages: Message[], isLiteMode: boolean) => {
    if (isLiteMode) {
      inMemoryStorage.messages.set(sessionId, messages);
    } else {
      localStorage.setItem(STORAGE_KEYS.getMessages(sessionId), JSON.stringify(messages));
    }
  },

  getActiveSessionId: (isLiteMode: boolean): string | null => {
    if (isLiteMode) {
      return inMemoryStorage.activeSessionId;
    }
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
  },

  setActiveSessionId: (sessionId: string, isLiteMode: boolean) => {
    if (isLiteMode) {
      inMemoryStorage.activeSessionId = sessionId;
    } else {
      localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, sessionId);
    }
  },

  deleteSession: (sessionId: string, isLiteMode: boolean) => {
    if (isLiteMode) {
      inMemoryStorage.messages.delete(sessionId);
    } else {
      localStorage.removeItem(STORAGE_KEYS.getMessages(sessionId));
    }
  },

  addSession: (session: SessionMetadata, isLiteMode: boolean) => {
    const sessions = sessionStorage.getSessions(isLiteMode);
    sessions.unshift(session);
    sessionStorage.saveSessions(sessions, isLiteMode);
  },

  updateSession: (sessionId: string, updates: Partial<SessionMetadata>, isLiteMode: boolean) => {
    const sessions = sessionStorage.getSessions(isLiteMode);
    const updated = sessions.map(s =>
      s.sessionId === sessionId ? { ...s, ...updates } : s
    );
    sessionStorage.saveSessions(updated, isLiteMode);
  },
};

export const useSessionStorage = () => {
  const { mode } = useAppMode();
  const isLiteMode = mode === 'lite';

  const [sessions, setSessions] = useState<SessionMetadata[]>([]);

  // Use ref to maintain state reference across renders
  const isLiteModeRef = useRef(isLiteMode);
  isLiteModeRef.current = isLiteMode;

  useEffect(() => {
    setSessions(sessionStorage.getSessions(isLiteMode));
  }, [isLiteMode]);

  const refreshSessions = useCallback(() => {
    setSessions(sessionStorage.getSessions(isLiteModeRef.current));
  }, []);

  const createSession = useCallback(async (): Promise<SessionMetadata> => {
    // Backend creates both auth session (cookie) and chat session (database)
    // This is required in both modes for secure API access
    const response = await chatApi.createSession('web_user');

    const newSession: SessionMetadata = {
      sessionId: response.session_id,
      title: 'New Chat',
      createdAt: Date.now(),
      lastMessageAt: Date.now(),
      messageCount: 0,
    };
    sessionStorage.addSession(newSession, isLiteModeRef.current);
    refreshSessions();
    return newSession;
  }, [refreshSessions]);

  const updateSessionMetadata = useCallback((
    sessionId: string,
    messageCount: number,
    firstQuestion?: string
  ) => {
    const currentSessions = sessionStorage.getSessions(isLiteModeRef.current);
    const session = currentSessions.find(s => s.sessionId === sessionId);
    const updates: Partial<SessionMetadata> = {
      lastMessageAt: Date.now(),
      messageCount,
    };

    if (session && session.messageCount === 0 && firstQuestion) {
      updates.title = firstQuestion.slice(0, 50);
    }

    sessionStorage.updateSession(sessionId, updates, isLiteModeRef.current);
    refreshSessions();
  }, [refreshSessions]);

  const deleteSession = useCallback((sessionId: string) => {
    sessionStorage.deleteSession(sessionId, isLiteModeRef.current);
    const filtered = sessions.filter(s => s.sessionId !== sessionId);
    sessionStorage.saveSessions(filtered, isLiteModeRef.current);
    refreshSessions();
  }, [sessions, refreshSessions]);

  return {
    sessions,
    createSession,
    updateSessionMetadata,
    deleteSession,
    refreshSessions,
  };
};