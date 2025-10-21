/**
 * Client-side coordinator for direct provider communication
 * Handles routing and specialist execution in the browser
 */

import { streamDirectChat as streamAnthropic, classifyMessage as classifyAnthropic, RoutingDecision } from './anthropic';
import { streamDirectChat as streamGoogle, classifyMessage as classifyGoogle } from './google';
import { getSpecialistPrompt, SpecialistType } from '../../config/specialists';

export type Provider = 'anthropic' | 'google';

export interface CoordinatorOptions {
  provider: Provider;
  apiKey?: string;
  onRoutingInfo?: (routing: RoutingDecision) => void;
  onContent?: (content: string, specialist?: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

/**
 * Coordinate a request using client-side routing and specialist execution
 */
export const coordinateRequest = async (
  message: string,
  options: CoordinatorOptions
): Promise<void> => {
  const { provider, apiKey, onRoutingInfo, onContent, onError, onComplete } = options;

  try {
    // Step 1: Classify the message
    const classifyFn = provider === 'anthropic' ? classifyAnthropic : classifyGoogle;
    const routing = await classifyFn(message, apiKey);

    // Safety check: RAG is not supported in direct mode
    if (routing.primary_agent === 'rag_query') {
      console.warn('rag_query detected in direct mode, falling back to general_chat');
      routing.primary_agent = 'general_chat';
    }
    routing.parallel_agents = routing.parallel_agents.filter(
      (agent) => agent !== 'rag_query'
    );

    // Notify about routing decision
    if (onRoutingInfo) {
      onRoutingInfo(routing);
    }

    // Step 2: If general_chat, skip coordination and stream directly
    if (routing.primary_agent === 'general_chat') {
      const streamFn = provider === 'anthropic' ? streamAnthropic : streamGoogle;

      let hasError = false;
      await streamFn(message, {
        apiKey,
        onEvent: (event) => {
          if (event.type === 'content' && onContent) {
            onContent(event.data.content);
          } else if (event.type === 'error') {
            hasError = true;
            if (onError) {
              onError(event.data.message);
            }
          }
        },
      });

      // Only call onComplete if there was no error
      if (!hasError && onComplete) {
        onComplete();
      }
      return;
    }

    // Step 3: Execute primary specialist
    const primarySuccess = await executeSpecialist(
      message,
      routing.primary_agent as SpecialistType,
      provider,
      apiKey,
      onContent,
      onError,
      'Primary'
    );

    // Stop if primary specialist failed
    if (!primarySuccess) {
      return;
    }

    // Step 4: Execute parallel specialists sequentially
    for (const parallelAgent of routing.parallel_agents) {
      const success = await executeSpecialist(
        message,
        parallelAgent as SpecialistType,
        provider,
        apiKey,
        onContent,
        onError,
        capitalizeFirst(parallelAgent)
      );

      // Stop if any specialist fails
      if (!success) {
        return;
      }
    }

    // Step 5: Complete (only if no errors)
    if (onComplete) {
      onComplete();
    }

  } catch (error) {
    if (onError) {
      onError(error instanceof Error ? error.message : String(error));
    }
  }
};

/**
 * Execute a single specialist
 * Returns true if successful, false if error occurred
 */
async function executeSpecialist(
  message: string,
  specialistType: SpecialistType,
  provider: Provider,
  apiKey: string | undefined,
  onContent: ((content: string, specialist?: string) => void) | undefined,
  onError: ((error: string) => void) | undefined,
  specialistLabel: string
): Promise<boolean> {
  // Get specialist prompt
  const systemPrompt = getSpecialistPrompt(specialistType);

  // Build specialized message
  const specializedMessage = `${systemPrompt}\n\nUser Request: ${message}`;

  // Add separator for non-primary specialists
  if (specialistLabel !== 'Primary' && onContent) {
    onContent(`\n\n--- ${specialistLabel} Analysis ---\n\n`, specialistLabel);
  }

  // Stream response
  const streamFn = provider === 'anthropic' ? streamAnthropic : streamGoogle;

  let hasError = false;
  await streamFn(specializedMessage, {
    apiKey,
    onEvent: (event) => {
      if (event.type === 'content' && onContent) {
        onContent(event.data.content, specialistLabel);
      } else if (event.type === 'error') {
        hasError = true;
        if (onError) {
          onError(`${specialistLabel}: ${event.data.message}`);
        }
      }
    },
  });

  return !hasError;
}

/**
 * Capitalize first letter of string
 */
function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

/**
 * Get chat history from localStorage for context (optional)
 */
export const getChatHistory = (): string => {
  try {
    const history = localStorage.getItem('chatHistory');
    if (!history) return '';

    const messages = JSON.parse(history);
    // Format last 5 messages as context
    return messages
      .slice(-5)
      .map((m: any) => `User: ${m.question}\nAssistant: ${m.answer}`)
      .join('\n\n');
  } catch {
    return '';
  }
};