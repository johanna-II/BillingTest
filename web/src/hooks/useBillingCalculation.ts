/**
 * Custom Hook: Billing Calculation
 * React Query integration with type-safe error handling and retry logic
 */

import React from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { calculateBilling, createCalculationError } from '@/lib/api/billing-api'
import type { BillingInput, BillingStatement, CalculationError } from '@/types/billing'
import { BILLING_QUERY_CONFIG } from '@/constants/query'

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
      queryClient.setQueryData([BILLING_QUERY_CONFIG.CACHE_KEY.PREFIX, data.statementId], data)
    },

    retry: BILLING_QUERY_CONFIG.RETRY.MAX_RETRIES,

    retryDelay: (attemptIndex: number) => {
      const delay =
        BILLING_QUERY_CONFIG.RETRY.INITIAL_DELAY_MS *
        Math.pow(BILLING_QUERY_CONFIG.RETRY.BACKOFF_MULTIPLIER, attemptIndex)
      return Math.min(delay, BILLING_QUERY_CONFIG.RETRY.MAX_DELAY_MS)
    },
  })

  // Memoize error to maintain referential equality
  // Prevents unnecessary re-renders in consumer components
  const memoizedError = React.useMemo(
    () => (mutation.error ? createCalculationError(mutation.error) : null),
    [mutation.error]
  )

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    data: mutation.data,
    error: memoizedError,
    isLoading: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    reset: mutation.reset,
  }
}
