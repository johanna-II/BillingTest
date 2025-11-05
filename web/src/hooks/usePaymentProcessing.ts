/**
 * Custom Hook: Payment Processing
 * React Query integration for payment operations with type safety
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { processPayment, createCalculationError } from '@/lib/api/billing-api'
import type { PaymentResult, CalculationError } from '@/types/billing'
import type { PaymentRequest } from '@/lib/api/billing-api'

// ============================================================================
// Configuration
// ============================================================================

const PAYMENT_CONFIG = {
  RETRY: {
    MAX_ATTEMPTS: 0, // Payments should not be retried automatically
  },
  CACHE_KEY: {
    PREFIX: 'payment',
  },
} as const
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

interface UsePaymentProcessingResult {
  readonly mutate: (input: PaymentProcessingInput) => void
  readonly mutateAsync: (input: PaymentProcessingInput) => Promise<PaymentResult>
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

  const mutation = useMutation({
    mutationFn: async (input: PaymentProcessingInput) => {
      const request: PaymentRequest = {
        amount: input.amount,
        paymentGroupId: input.billingGroupId,
      }

      return processPayment(input.uuid, input.month, request)
    },

    onSuccess: (data: PaymentResult, variables: PaymentProcessingInput) => {
      // Cache the payment result
      queryClient.setQueryData([PAYMENT_CONFIG.CACHE_KEY.PREFIX, data.paymentId], data)

      // Invalidate only specific billing queries affected by this payment
      queryClient.invalidateQueries({
        queryKey: ['billing', variables.statementId],
      })
      queryClient.invalidateQueries({
        queryKey: ['billing', 'statements', variables.statementId],
      })
      queryClient.invalidateQueries({
        queryKey: ['billing', 'groups', variables.billingGroupId],
      })
    },

    retry: PAYMENT_CONFIG.RETRY.MAX_ATTEMPTS,
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
