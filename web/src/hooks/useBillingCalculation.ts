/**
 * Custom Hook: Billing Calculation
 * React Query integration with type-safe error handling and retry logic
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { calculateBilling, createCalculationError } from '@/lib/api/billing-api'
import type { BillingInput, BillingStatement, CalculationError } from '@/types/billing'

// ============================================================================
// Configuration
// ============================================================================

const QUERY_CONFIG = {
  RETRY: {
    MAX_RETRIES: 2, // Total attempts = 1 initial + 2 retries
    INITIAL_DELAY_MS: 1000,
    MAX_DELAY_MS: 30000,
    BACKOFF_MULTIPLIER: 2,
  },
  CACHE_KEY: {
    PREFIX: 'billing',
  },
} as const

// ============================================================================
// Types
// ============================================================================

interface UseBillingCalculationResult {
  readonly mutate: (input: BillingInput) => void
  readonly mutateAsync: (input: BillingInput) => Promise<BillingStatement>
  readonly data: BillingStatement | undefined
  readonly error: CalculationError | null
  readonly isLoading: boolean
  readonly isSuccess: boolean
  readonly isError: boolean
  readonly reset: () => void
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useBillingCalculation(): UseBillingCalculationResult {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (input: BillingInput) => calculateBilling(input),

    onSuccess: (data: BillingStatement) => {
      // Cache the successful result
      queryClient.setQueryData([QUERY_CONFIG.CACHE_KEY.PREFIX, data.statementId], data)
    },

    retry: QUERY_CONFIG.RETRY.MAX_RETRIES,

    retryDelay: (attemptIndex: number) => {
      const delay =
        QUERY_CONFIG.RETRY.INITIAL_DELAY_MS *
        Math.pow(QUERY_CONFIG.RETRY.BACKOFF_MULTIPLIER, attemptIndex)
      return Math.min(delay, QUERY_CONFIG.RETRY.MAX_DELAY_MS)
    },
  })

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    data: mutation.data,
    error: mutation.error ? createCalculationError(mutation.error) : null,
    isLoading: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    reset: mutation.reset,
  }
}
