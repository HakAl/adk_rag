import { useChatStreamFull } from './useChatStream.full';
import { useChatStreamLite } from './useChatStream.lite';
import { useAppMode } from './useAppMode';

/**
 * Smart router hook for chat streaming
 * Automatically routes to full or lite version based on app mode
 */
export const useChatStream = (sessionId: string | undefined, userId: string) => {
  const { mode } = useAppMode();

  if (mode === 'lite') {
    return useChatStreamLite(sessionId);
  }

  return useChatStreamFull(sessionId, userId);
};