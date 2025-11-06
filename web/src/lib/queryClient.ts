/**
 * React Query Client Configuration
 * Centralized query configuration with type-safe defaults
 */

import { QueryClient, QueryKey } from '@tanstack/react-query'
import { QUERY_CLIENT_CONFIG } from '@/constants/query'

// ============================================================================
// Query Client Instance
// ============================================================================

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_CLIENT_CONFIG.QUERIES.STALE_TIME_MS,
      gcTime: QUERY_CLIENT_CONFIG.CACHE.GC_TIME_MS,
      refetchOnWindowFocus: QUERY_CLIENT_CONFIG.QUERIES.REFETCH_ON_WINDOW_FOCUS,
      retry: QUERY_CLIENT_CONFIG.QUERIES.RETRY_ATTEMPTS,
      retryDelay: QUERY_CLIENT_CONFIG.QUERIES.RETRY_DELAY_MS,
    },
    mutations: {
      retry: QUERY_CLIENT_CONFIG.MUTATIONS.RETRY_ATTEMPTS,
    },
  },
})

// ============================================================================
// Query Client Utilities
// ============================================================================

/**
 * Reset all queries and clear cache
 */
export const resetQueryClient = (): void => {
  queryClient.clear()
}

/**
 * Invalidate all queries with a specific key
 */
export const invalidateQueries = (queryKey: QueryKey): Promise<void> => {
  return queryClient.invalidateQueries({ queryKey })
}

/**
 * Prefetch query data
 */
export const prefetchQuery = <T>(
  queryKey: QueryKey,
  queryFn: () => Promise<T>
): Promise<void> => {
  return queryClient.prefetchQuery({ queryKey, queryFn })
}
