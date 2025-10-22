import { getApiUrl } from '../config';

export interface Message {
  id: string;
  question: string;
  answer: string;
  timestamp: number;
}

export interface SessionResponse {
  session_id: string;
  user_id: string;
}

// Old interface - DEPRECATED, kept for backwards compatibility
export interface ChatRequestLegacy {
  message: string;
  user_id: string;
  session_id: string;
}

// New interface - session comes from cookie
export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface StreamEvent {
  type: 'routing' | 'content' | 'done' | 'error';
  data: any;
}

export interface RoutingInfo {
  agent: string;
  agent_name: string;
  confidence: number;
  reasoning?: string;
}

// CSRF token storage - persisted in sessionStorage
const CSRF_TOKEN_KEY = 'csrf_token';

export const setCsrfToken = (token: string | null) => {
  if (token) {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(CSRF_TOKEN_KEY);
  }
};

export const getCsrfToken = (): string | null => {
  return sessionStorage.getItem(CSRF_TOKEN_KEY);
};

export const chatApi = {
  createSession: async (userId: string = 'web_user'): Promise<SessionResponse> => {
    const response = await fetch(getApiUrl('/sessions/coordinator'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
      credentials: 'include', // CRITICAL: Send/receive cookies
    });

    if (!response.ok) {
      throw new Error('Failed to create session');
    }

    // Extract CSRF token from response header
    const token = response.headers.get('X-CSRF-Token');
    if (token) {
      setCsrfToken(token);
    }

    return response.json();
  },

  sendMessage: async (message: string): Promise<ChatResponse> => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Add CSRF token to all state-changing requests
    const token = getCsrfToken();
    if (token) {
      headers['X-CSRF-Token'] = token;
    }

    const response = await fetch(getApiUrl('/chat/coordinator'), {
      method: 'POST',
      headers,
      body: JSON.stringify({ message }), // No user_id/session_id needed
      credentials: 'include', // CRITICAL: Send cookies
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Session expired. Please refresh the page.');
      }
      if (response.status === 403) {
        throw new Error('Security token invalid. Please refresh the page.');
      }
      throw new Error('Failed to send message');
    }

    return response.json();
  },

  streamMessage: async (
    message: string,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Add CSRF token
    const token = getCsrfToken();
    if (token) {
      headers['X-CSRF-Token'] = token;
    }

    const response = await fetch(getApiUrl('/chat/coordinator/stream'), {
      method: 'POST',
      headers,
      body: JSON.stringify({ message }), // No user_id/session_id needed
      credentials: 'include', // CRITICAL: Send cookies
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Session expired. Please refresh the page.');
      }
      if (response.status === 403) {
        throw new Error('Security token invalid. Please refresh the page.');
      }
      throw new Error('Failed to stream message');
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
        console.log('🔥 Raw chunk received, size:', value?.length, 'done:', done);

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        console.log('📦 Buffer now:', buffer.length, 'chars');

        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const lines = event.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = line.slice(6);
                const parsedEvent: StreamEvent = JSON.parse(data);
                onEvent(parsedEvent);
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
  },

  logout: async (): Promise<void> => {
    const response = await fetch(getApiUrl('/logout'), {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to logout');
    }

    // Clear CSRF token
    setCsrfToken(null);
  },
};