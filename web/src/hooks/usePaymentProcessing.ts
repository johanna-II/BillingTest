/**
 * Custom Hook: Payment Processing
 * React Query integration for payment operations with type safety
 */

import { useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { UseMutateFunction, UseMutateAsyncFunction } from '@tanstack/react-query'
import { processPayment, createCalculationError } from '@/lib/api/billing-api'
import type { PaymentResult, CalculationError } from '@/types/billing'
import type { PaymentRequest } from '@/lib/api/billing-api'
import { PAYMENT_QUERY_CONFIG, BILLING_QUERY_KEYS } from '@/constants/query'

// ============================================================================
// Types
// ============================================================================

export interface PaymentProcessingInput {
  readonly statementId: string
  readonly month: string // Required for API endpoint construction (e.g., "2024-11")
  readonly amount: number
  readonly uuid: string
  readonly billingGroupId: string
}

/**
 * Result type for usePaymentProcessing hook
 * Uses React Query's native types to preserve MutateOptions support
 */
interface UsePaymentProcessingResult {
  readonly mutate: UseMutateFunction<PaymentResult, Error, PaymentProcessingInput, unknown>
  readonly mutateAsync: UseMutateAsyncFunction<PaymentResult, Error, PaymentProcessingInput, unknown>
  readonly data: PaymentResult | undefined
  readonly error: CalculationError | null
  readonly isLoading: boolean
  readonly isSuccess: boolean
  readonly isError: boolean
  readonly reset: () => void
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function usePaymentProcessing(): UsePaymentProcessingResult {
  const queryClient = useQueryClient()

  const mutation = useMutation<PaymentResult, Error, PaymentProcessingInput>({
    mutationFn: async (input: PaymentProcessingInput) => {
      const request: PaymentRequest = {
        amount: input.amount,
        paymentGroupId: input.billingGroupId,
      }

      return processPayment(input.uuid, input.month, request)
    },

    onSuccess: (data: PaymentResult, variables: PaymentProcessingInput) => {
      // Cache the payment result
      queryClient.setQueryData([PAYMENT_QUERY_CONFIG.CACHE_KEY.PREFIX, data.paymentId], data)

      // Invalidate billing query for this statement
      // Note: Only invalidates the actual cached key ['billing', statementId]
      queryClient.invalidateQueries({
        queryKey: BILLING_QUERY_KEYS.byStatement(variables.statementId),
      })
    },

    retry: PAYMENT_QUERY_CONFIG.RETRY.MAX_RETRIES,
  })

  // Memoize error to maintain referential equality
  // Prevents unnecessary re-renders in consumer components
  const memoizedError = useMemo(
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
