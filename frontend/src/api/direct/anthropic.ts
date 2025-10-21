/**
 * Direct Anthropic API integration (bypasses coordinator)
 */

import { getCsrfToken } from '../backend/chat';

export interface StreamEvent {
  type: 'content' | 'done' | 'error';
  data: any;
}

export interface RoutingDecision {
  primary_agent: string;
  parallel_agents: string[];
  confidence: number;
  reasoning: string;
}

export interface DirectChatOptions {
  apiKey?: string;
  onEvent: (event: StreamEvent) => void;
}

/**
 * Stream chat directly to Anthropic API
 */
export const streamDirectChat = async (
  message: string,
  options: DirectChatOptions
): Promise<void> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add CSRF token (required for session-based auth)
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  // Add API key if provided (optional - falls back to .env in dev)
  if (options.apiKey) {
    headers['X-API-Key'] = options.apiKey;
  }

  const response = await fetch('/chat/direct/anthropic/stream', {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
    credentials: 'include', // Required for session cookies
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('Session expired. Please refresh the page.');
    }
    if (response.status === 403) {
      throw new Error('Security token invalid. Please refresh the page.');
    }
    if (response.status === 429) {
      throw new Error('Rate limit exceeded. Please slow down.');
    }
    throw new Error(`Failed to stream message: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        const lines = event.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = line.slice(6);
              const parsedEvent: StreamEvent = JSON.parse(data);
              options.onEvent(parsedEvent);
            } catch (e) {
              console.error('Failed to parse SSE event:', line, e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

/**
 * Classify a message using Anthropic's routing
 * (Optional - for showing routing info in UI)
 */
export const classifyMessage = async (
  message: string,
  apiKey?: string
): Promise<RoutingDecision> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const response = await fetch('/chat/direct/anthropic/classify', {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to classify message');
  }

  return response.json();
};

export const directAnthropicApi = {
  streamDirectChat,
  classifyMessage,
};