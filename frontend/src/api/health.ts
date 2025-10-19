import { getApiUrl } from './config';

export interface HealthResponse {
  status: string;
  version: string;
}

export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await fetch(getApiUrl('/health'));

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },
};