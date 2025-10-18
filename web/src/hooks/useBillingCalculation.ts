/**
 * Custom hook for billing calculation with React Query
 * Provides caching, automatic retries, and optimistic updates
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { calculateBilling } from '@/lib/api/billing-api'
import type { BillingInput, BillingStatement } from '@/types/billing'

export function useBillingCalculation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: BillingInput) => calculateBilling(input),
    onSuccess: (data: BillingStatement) => {
      // Cache the result
      queryClient.setQueryData(['billing', data.statementId], data)
    },
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}
