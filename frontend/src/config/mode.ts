import { getApiUrl } from './config';

export type AppMode = 'full' | 'lite';

export const detectMode = async (): Promise<AppMode> => {
  // Check explicit env var first
  const envMode = import.meta.env.VITE_APP_MODE;
  if (envMode === 'lite') {
    return 'lite';
  }

  // Check if on GitHub Pages
  if (window.location.hostname.includes('github.io')) {
    return 'lite';
  }

  // Try health check with timeout to wake backend and detect mode
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(getApiUrl('/health'), {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      return 'full';
    }
    return 'lite';
  } catch (error) {
    // Timeout or network error - assume lite mode
    return 'lite';
  }
};