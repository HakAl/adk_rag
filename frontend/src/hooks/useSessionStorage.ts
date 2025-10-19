import { useState, useEffect, useCallback } from 'react';
import { Message } from '../api/chat';
import { chatApi } from '../api/chat';

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

export const sessionStorage = {
  getSessions: (): SessionMetadata[] => {
    const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
    return data ? JSON.parse(data) : [];
  },

  saveSessions: (sessions: SessionMetadata[]) => {
    localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
  },

  getMessages: (sessionId: string): Message[] => {
    const data = localStorage.getItem(STORAGE_KEYS.getMessages(sessionId));
    return data ? JSON.parse(data) : [];
  },

  saveMessages: (sessionId: string, messages: Message[]) => {
    localStorage.setItem(STORAGE_KEYS.getMessages(sessionId), JSON.stringify(messages));
  },

  getActiveSessionId: (): string | null => {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
  },

  setActiveSessionId: (sessionId: string) => {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, sessionId);
  },

  deleteSession: (sessionId: string) => {
    localStorage.removeItem(STORAGE_KEYS.getMessages(sessionId));
  },

  addSession: (session: SessionMetadata) => {
    const sessions = sessionStorage.getSessions();
    sessions.unshift(session);
    sessionStorage.saveSessions(sessions);
  },

  updateSession: (sessionId: string, updates: Partial<SessionMetadata>) => {
    const sessions = sessionStorage.getSessions();
    const updated = sessions.map(s =>
      s.sessionId === sessionId ? { ...s, ...updates } : s
    );
    sessionStorage.saveSessions(updated);
  },
};

export const useSessionStorage = () => {
  const [sessions, setSessions] = useState<SessionMetadata[]>([]);

  useEffect(() => {
    setSessions(sessionStorage.getSessions());
  }, []);

  const refreshSessions = useCallback(() => {
    setSessions(sessionStorage.getSessions());
  }, []);

  const createSession = useCallback(async (): Promise<SessionMetadata> => {
    // FIXED: Call backend API to create session in database first
    const response = await chatApi.createSession('web_user');

    const newSession: SessionMetadata = {
      sessionId: response.session_id, // Use backend-generated session ID
      title: 'New Chat',
      createdAt: Date.now(),
      lastMessageAt: Date.now(),
      messageCount: 0,
    };
    sessionStorage.addSession(newSession);
    refreshSessions();
    return newSession;
  }, [refreshSessions]);

  const updateSessionMetadata = useCallback((
    sessionId: string,
    messageCount: number,
    firstQuestion?: string
  ) => {
    const currentSessions = sessionStorage.getSessions();
    const session = currentSessions.find(s => s.sessionId === sessionId);
    const updates: Partial<SessionMetadata> = {
      lastMessageAt: Date.now(),
      messageCount,
    };

    if (session && session.messageCount === 0 && firstQuestion) {
      updates.title = firstQuestion.slice(0, 50);
    }

    sessionStorage.updateSession(sessionId, updates);
    refreshSessions();
  }, [refreshSessions]);

  const deleteSession = useCallback((sessionId: string) => {
    sessionStorage.deleteSession(sessionId);
    const filtered = sessions.filter(s => s.sessionId !== sessionId);
    sessionStorage.saveSessions(filtered);
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