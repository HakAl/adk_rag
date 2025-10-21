import { useChatFull } from './useChat.full';
import { useChatLite } from './useChat.lite';
import { useAppMode } from './useAppMode';

/**
 * Smart router hook for chat
 * Automatically routes to full or lite version based on app mode
 */
export const useChat = (sessionId: string | undefined, userId: string) => {
  const { mode } = useAppMode();

  if (mode === 'lite') {
    return useChatLite(sessionId, userId);
  }

  return useChatFull(sessionId, userId);
};