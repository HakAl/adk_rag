import { useEffect } from 'react';
import { Message } from '../api/chat';
import { sessionStorage } from './useSessionStorage';

interface UseMessagePersistenceOptions {
  sessionId: string;
  messages: Message[];
  updateSessionMetadata: (sessionId: string, messageCount: number, firstQuestion?: string) => void;
}

export const useMessagePersistence = ({
  sessionId,
  messages,
  updateSessionMetadata,
}: UseMessagePersistenceOptions): void => {
  useEffect(() => {
    if (sessionId && messages.length > 0) {
      // Save messages to localStorage
      sessionStorage.saveMessages(sessionId, messages);

      // Update session metadata
      const firstUserMessage = messages[0]?.question;
      updateSessionMetadata(sessionId, messages.length, firstUserMessage);
    }
  }, [sessionId, messages.length, updateSessionMetadata]);
};