import { useMutation, useQueryClient } from '@tanstack/react-query';
import { coordinateRequest } from '../api/direct/coordinator';
import { useApiKeys } from '../contexts/ApiKeyContext';
import { Message } from '../api/backend/chat';
import { sessionStorage } from './useSessionStorage';

/**
 * Lite mode chat hook - non-streaming mutation
 * Uses direct API calls via coordinator
 */
export const useChatLite = (sessionId: string | undefined, userId: string) => {
  const queryClient = useQueryClient();
  const { provider, keys } = useApiKeys();

  return useMutation({
    mutationFn: async (message: string) => {
      if (!sessionId) {
        throw new Error('No session available');
      }

      // Get API key for current provider
      const apiKey = provider === 'anthropic' ? keys.anthropic : keys.google;

      if (!apiKey) {
        throw new Error('API key not configured');
      }

      let fullResponse = '';

      // Collect full response via coordinator
      await coordinateRequest(message, {
        provider,
        apiKey,
        onContent: (content) => {
          fullResponse += content;
        },
        onError: (errorMsg) => {
          throw new Error(errorMsg);
        },
      });

      return { response: fullResponse };
    },
    onSuccess: (data, message) => {
      // Update the optimistic message with the actual response
      queryClient.setQueryData<Message[]>(['messages', sessionId], (old = []) => {
        // Find the most recent optimistic message for this question
        const optimisticIndex = [...old].reverse().findIndex(msg =>
          msg.question === message && msg.answer === ''
        );

        // Convert reversed index back to normal index
        const actualIndex = optimisticIndex !== -1 ? old.length - 1 - optimisticIndex : -1;

        let updated: Message[];
        if (actualIndex !== -1) {
          // Update the existing optimistic message in place
          updated = [...old];
          updated[actualIndex] = {
            ...updated[actualIndex],
            id: Date.now().toString(),
            answer: data.response,
          };
        } else {
          // If no optimistic message found, add a new one at the end (fallback)
          const newMessage: Message = {
            id: Date.now().toString(),
            question: message,
            answer: data.response,
            timestamp: Date.now(),
          };
          updated = [...old, newMessage];
        }

        // Save to localStorage
        if (sessionId) {
          sessionStorage.saveMessages(sessionId, updated);
        }

        return updated;
      });
    },
    onError: (_error, message) => {
      // Update the optimistic message with an error message
      queryClient.setQueryData<Message[]>(['messages', sessionId], (old = []) => {
        // Find the most recent optimistic message for this question
        const optimisticIndex = [...old].reverse().findIndex(msg =>
          msg.question === message && msg.answer === ''
        );

        // Convert reversed index back to normal index
        const actualIndex = optimisticIndex !== -1 ? old.length - 1 - optimisticIndex : -1;

        if (actualIndex !== -1) {
          // Update the existing optimistic message with error
          const updated = [...old];
          updated[actualIndex] = {
            ...updated[actualIndex],
            answer: '❌ Failed to get response. Please try again.',
          };

          // Save to localStorage
          if (sessionId) {
            sessionStorage.saveMessages(sessionId, updated);
          }

          return updated;
        }

        return old;
      });
    },
  });
};