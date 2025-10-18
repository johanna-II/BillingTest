/**
 * Payment Section Component
 * Process mock payment
 */

'use client'

import React, { useState } from 'react'
import { useCalculatedStatement, usePaymentResult, useBilling } from '@/contexts/BillingContext'
import { processPayment } from '@/lib/api/billing-api'

interface PaymentSectionProps {
  onBackToInput?: () => void
}

const PaymentSection: React.FC<PaymentSectionProps> = ({ onBackToInput }) => {
  const statement = useCalculatedStatement()
  const paymentResult = usePaymentResult()
  const { actions } = useBilling()
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!statement) {
    return (
      <div className="kinfolk-card p-12 text-center">
        <p className="text-sm text-kinfolk-gray-600">No statement available for payment.</p>
      </div>
    )
  }

  const handlePayment = async (): Promise<void> => {
    setError(null)
    setIsProcessing(true)

    try {
      const result = await processPayment(
        statement.uuid,
        statement.month,
        {
          amount: statement.totalAmount,
          paymentGroupId: statement.billingGroupId || `PG-${statement.uuid.slice(0, 8)}`,
        }
      )
      actions.setPaymentResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed')
    } finally {
      setIsProcessing(false)
    }
  }

  const formatCurrency = (amount: number): string => {
    return `₩${amount.toLocaleString('ko-KR')}`
  }

  if (paymentResult) {
    return (
      <div className="kinfolk-card p-8 md:p-12 fade-in">
        <h2 className="text-2xl font-kinfolk-serif mb-8">Payment Result</h2>

        <div
          className={`
            p-8 mb-8 text-center
            ${
              paymentResult.status === 'SUCCESS'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }
          `}
        >
          <div
            className={`
              w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center
              ${paymentResult.status === 'SUCCESS' ? 'bg-green-100' : 'bg-red-100'}
            `}
          >
            <span className="text-2xl">{paymentResult.status === 'SUCCESS' ? '✓' : '✗'}</span>
          </div>
          <h3 className="text-xl font-kinfolk-serif mb-2">
            {paymentResult.status === 'SUCCESS' ? 'Payment Successful' : 'Payment Failed'}
          </h3>
          <p className="text-sm text-kinfolk-gray-600">
            {paymentResult.status === 'SUCCESS'
              ? 'Your payment has been processed successfully.'
              : paymentResult.errorMessage || 'An error occurred during payment.'}
          </p>
        </div>

        <div className="space-y-4 mb-8">
          <div className="flex justify-between items-center py-3 border-b border-kinfolk-gray-200">
            <span className="text-sm text-kinfolk-gray-700">Payment ID</span>
            <span className="font-medium font-mono text-sm">{paymentResult.paymentId}</span>
          </div>
          <div className="flex justify-between items-center py-3 border-b border-kinfolk-gray-200">
            <span className="text-sm text-kinfolk-gray-700">Amount</span>
            <span className="font-medium text-sm font-kinfolk">{formatCurrency(paymentResult.amount)}</span>
          </div>
          <div className="flex justify-between items-center py-3 border-b border-kinfolk-gray-200">
            <span className="text-sm text-kinfolk-gray-700">Method</span>
            <span className="font-medium text-sm font-kinfolk">{paymentResult.method}</span>
          </div>
          <div className="flex justify-between items-center py-3 border-b border-kinfolk-gray-200">
            <span className="text-sm text-kinfolk-gray-700">Transaction Date</span>
            <span className="font-medium text-sm font-kinfolk">
              {new Date(paymentResult.transactionDate).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="flex justify-center">
          <button
            onClick={() => {
              actions.reset()
              if (onBackToInput) {
                onBackToInput()
              }
            }}
            className="kinfolk-button-secondary"
          >
            Start New Calculation
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="kinfolk-card p-8 md:p-12 fade-in">
      <h2 className="text-2xl font-kinfolk-serif mb-8">Process Payment</h2>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-800 text-sm">
          {error}
        </div>
      )}

      <div className="mb-8 p-6 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm text-kinfolk-gray-700">Statement ID</span>
          <span className="font-mono text-sm">{statement.statementId}</span>
        </div>
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm text-kinfolk-gray-700">Billing Group</span>
          <span className="text-sm font-kinfolk">{statement.billingGroupId}</span>
        </div>
        <div className="flex justify-between items-center pt-4 border-t border-kinfolk-gray-300">
          <span className="text-lg font-kinfolk-serif">Amount to Pay</span>
          <span className="text-2xl font-semibold font-kinfolk">{formatCurrency(statement.totalAmount)}</span>
        </div>
      </div>

      <div className="space-y-6 mb-8">
        <div>
          <label className="kinfolk-label">Payment Method</label>
          <select className="kinfolk-input" defaultValue="MOCK">
            <option value="MOCK">Mock Payment (Test)</option>
            <option value="CREDIT_CARD" disabled>
              Credit Card (Not Available)
            </option>
            <option value="BANK_TRANSFER" disabled>
              Bank Transfer (Not Available)
            </option>
          </select>
        </div>

        <div className="p-4 bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm">
          <p className="font-medium mb-1">Test Mode</p>
          <p>This is a mock payment for testing purposes. No actual charges will be made.</p>
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handlePayment}
          disabled={isProcessing}
          className="kinfolk-button disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <>
              <span className="spinner mr-2" />
              Processing...
            </>
          ) : (
            'Process Payment'
          )}
        </button>
      </div>
    </div>
  )
}

export default React.memo(PaymentSection)
