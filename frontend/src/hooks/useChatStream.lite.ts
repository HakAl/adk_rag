import { useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { coordinateRequest, RoutingDecision } from '../api/direct/coordinator';
import { useApiKeys } from '../contexts/ApiKeyContext';
import { Message } from '../api/backend/chat';
import { sessionStorage } from './useSessionStorage';
import { formatApiError } from '../utils/errorFormatter';

interface UseChatStreamResult {
  sendMessage: (message: string) => Promise<void>;
  isStreaming: boolean;
  error: Error | null;
  routingInfo: RoutingDecision | null;
  streamingContent: string;
}

/**
 * Lite mode chat streaming hook - uses direct API calls via coordinator
 * Handles routing, streaming, and message state management
 */
export const useChatStreamLite = (sessionId: string | undefined): UseChatStreamResult => {
  const queryClient = useQueryClient();
  const { provider, keys } = useApiKeys();

  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [routingInfo, setRoutingInfo] = useState<RoutingDecision | null>(null);
  const [streamingContent, setStreamingContent] = useState('');

  const fullResponseRef = useRef('');

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId) {
      setError(new Error('Session not available'));
      return;
    }

    // Get API key for current provider
    const apiKey = provider === 'anthropic' ? keys.anthropic : keys.google;

    if (!apiKey) {
      setError(new Error('API key not configured'));
      return;
    }

    setIsStreaming(true);
    setError(null);
    setRoutingInfo(null);
    setStreamingContent('');
    fullResponseRef.current = '';

    try {
      await coordinateRequest(message, {
        provider,
        apiKey,
        onRoutingInfo: (routing) => {
          setRoutingInfo(routing);
        },
        onContent: (content) => {
          fullResponseRef.current += content;
          setStreamingContent(fullResponseRef.current);
        },
        onError: (errorMsg) => {
          // Format error message for user-friendly display
          const formattedError = formatApiError(errorMsg);
          setError(new Error(formattedError));
          setIsStreaming(false);
        },
        onComplete: () => {
          // Create final message and add to query cache
          const finalMessage: Message = {
            id: `msg-${Date.now()}`,
            question: message,
            answer: fullResponseRef.current,
            timestamp: Date.now(),
          };

          queryClient.setQueryData<Message[]>(
            ['messages', sessionId],
            (old = []) => {
              const filtered = old.filter(m => !m.id.startsWith('optimistic-'));
              const updated = [...filtered, finalMessage];

              // Save to in-memory storage (lite mode)
              sessionStorage.saveMessages(sessionId, updated, true);

              return updated;
            }
          );

          setIsStreaming(false);
          setStreamingContent('');
          setRoutingInfo(null);
          fullResponseRef.current = '';
        },
      });
    } catch (err) {
      // This catch handles errors from coordinateRequest itself (not from onError callback)
      const errorMessage = err instanceof Error ? err.message : 'Request failed';
      const formattedError = formatApiError(errorMessage);
      setError(new Error(formattedError));
      setIsStreaming(false);
      setStreamingContent('');
      setRoutingInfo(null);
      fullResponseRef.current = '';

      // Remove optimistic message on error
      queryClient.setQueryData<Message[]>(
        ['messages', sessionId],
        (old = []) => old.filter(m => !m.id.startsWith('optimistic-'))
      );
    }
  }, [sessionId, provider, keys, queryClient]);

  return {
    sendMessage,
    isStreaming,
    error,
    routingInfo,
    streamingContent,
  };
};