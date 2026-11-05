import type { ApiService } from './api';
import { MockApiService } from './mock-api';
import { RealApiService } from './real-api';

export type { ApiService } from './api';

/** Singleton API service instance */
let apiInstance: ApiService | null = null;

/**
 * Get the API service instance.
 * Reads VITE_USE_REAL_API env variable to decide which implementation to use.
 * Defaults to MockApiService.
 */
export function getApiService(): ApiService {
  if (!apiInstance) {
    const useReal = import.meta.env.VITE_USE_REAL_API === 'true';
    apiInstance = useReal ? new RealApiService() : new MockApiService();
  }
  return apiInstance;
}

/**
 * Get the mock API service directly.
 * Used when we need mock-specific methods like storeVoteRecord().
 */
export function getMockApiService(): MockApiService | null {
  const service = getApiService();
  return service instanceof MockApiService ? service : null;
}
