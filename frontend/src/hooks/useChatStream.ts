import { useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { chatApi, Message, RoutingInfo } from '../api/chat';

interface UseChatStreamResult {
  sendMessage: (message: string) => Promise<void>;
  isStreaming: boolean;
  error: Error | null;
  routingInfo: RoutingInfo | null;
  streamingContent: string;
}

export const useChatStream = (sessionId: string, userId: string): UseChatStreamResult => {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [routingInfo, setRoutingInfo] = useState<RoutingInfo | null>(null);
  const [streamingContent, setStreamingContent] = useState('');

  // Use ref to avoid closure issues with streaming
  const fullResponseRef = useRef('');

  const sendMessage = useCallback(async (message: string) => {
    if (!sessionId) return;

    setIsStreaming(true);
    setError(null);
    setRoutingInfo(null);
    setStreamingContent('');
    fullResponseRef.current = '';

    try {
      await chatApi.streamMessage(
        message,
        (event) => {
          console.log('🎯 Event received:', event.type, event.data);
          switch (event.type) {
            case 'routing':
              console.log('📍 Setting routing info');
              setRoutingInfo(event.data);
              break;

            case 'content':
              fullResponseRef.current += event.data;
              console.log('📝 Content chunk:', event.data, 'Total length:', fullResponseRef.current.length);
              // Update state immediately without flushSync
              setStreamingContent(fullResponseRef.current);
              break;

            case 'done':
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
                  // Remove optimistic message if it exists
                  const filtered = old.filter(m => !m.id.startsWith('optimistic-'));
                  return [...filtered, finalMessage];
                }
              );

              setIsStreaming(false);
              setStreamingContent('');
              setRoutingInfo(null);
              fullResponseRef.current = '';
              break;

            case 'error':
              throw new Error(event.data.message || 'Streaming error');
          }
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
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
  }, [sessionId, userId, queryClient]);

  return {
    sendMessage,
    isStreaming,
    error,
    routingInfo,
    streamingContent,
  };
};