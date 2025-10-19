/**
 * API Configuration
 *
 * In development: Uses Vite proxy (empty base URL, relative paths)
 * In production: Set VITE_API_URL environment variable
 *
 * Example .env.production:
 * VITE_API_URL=https://api.yourdomain.com
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Constructs full API URL
 * @param path - API endpoint path (e.g., '/health', '/chat/coordinator')
 */
export const getApiUrl = (path: string): string => {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  // If no base URL, return relative path (for Vite proxy)
  if (!API_BASE_URL) {
    return normalizedPath;
  }

  // Remove trailing slash from base URL if present
  const baseUrl = API_BASE_URL.endsWith('/')
    ? API_BASE_URL.slice(0, -1)
    : API_BASE_URL;

  return `${baseUrl}${normalizedPath}`;
};