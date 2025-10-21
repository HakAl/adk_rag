import { useEffect } from 'react';
import { Message } from '../api/backend/chat.ts';
import { sessionStorage } from './useSessionStorage';
import { useAppMode } from './useAppMode';

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
  const { mode } = useAppMode();
  const isLiteMode = mode === 'lite';

  useEffect(() => {
    if (sessionId && messages.length > 0) {
      // Save messages (in-memory for lite mode, localStorage for full mode)
      sessionStorage.saveMessages(sessionId, messages, isLiteMode);

      // Update session metadata
      const firstUserMessage = messages[0]?.question;
      updateSessionMetadata(sessionId, messages.length, firstUserMessage);
    }
  }, [sessionId, messages, isLiteMode, updateSessionMetadata]);
};