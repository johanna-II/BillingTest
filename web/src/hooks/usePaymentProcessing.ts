/**
 * Custom hook for payment processing with React Query
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { processPayment } from '@/lib/api/billing-api'
import type { PaymentResult } from '@/types/billing'

export function usePaymentProcessing() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      statementId,
      amount,
      uuid,
      billingGroupId,
    }: {
      statementId: string
      amount: number
      uuid: string
      billingGroupId: string
    }) => processPayment(statementId, amount, uuid, billingGroupId),
    onSuccess: (data: PaymentResult) => {
      // Cache the payment result
      queryClient.setQueryData(['payment', data.paymentId], data)
    },
    retry: 1,
  })
}


