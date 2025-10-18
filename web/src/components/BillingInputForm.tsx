/**
 * Billing Input Form Component
 * Collects all billing parameters from user
 */

'use client'

import React, { useState } from 'react'
import { useBilling } from '@/contexts/BillingContext'
import { calculateBilling } from '@/lib/api/billing-api'
import type { BillingInput, UsageInput, CreditInput, AdjustmentInput } from '@/types/billing'
import UsageInputSection from './sections/UsageInputSection'
import CreditInputSection from './sections/CreditInputSection'
import AdjustmentInputSection from './sections/AdjustmentInputSection'
import BasicInfoSection from './sections/BasicInfoSection'

interface BillingInputFormProps {
  onComplete: () => void
}

const BillingInputForm: React.FC<BillingInputFormProps> = ({ onComplete }) => {
  const { actions } = useBilling()

  // Basic info
  const [targetDate, setTargetDate] = useState<Date>(new Date())
  const [uuid, setUuid] = useState('test-uuid-001')
  const [billingGroupId, setBillingGroupId] = useState('bg-kr-test')
  const [unpaidAmount, setUnpaidAmount] = useState(0)
  const [isOverdue, setIsOverdue] = useState(false)

  // Usage, Credits, Adjustments
  const [usage, setUsage] = useState<UsageInput[]>([])
  const [credits, setCredits] = useState<CreditInput[]>([])
  const [adjustments, setAdjustments] = useState<AdjustmentInput[]>([])

  // UI state
  const [error, setError] = useState<string | null>(null)

  const handleCalculate = async (): Promise<void> => {
    // Validation
    if (!uuid || !billingGroupId) {
      setError('UUID and Billing Group ID are required')
      return
    }

    if (usage.length === 0) {
      setError('At least one usage entry is required')
      return
    }

    setError(null)

    const billingInput: BillingInput = {
      targetDate,
      uuid,
      billingGroupId,
      usage,
      credits,
      adjustments,
      unpaidAmount,
      isOverdue,
    }

    try {
      actions.setCalculating(true)
      actions.setBillingInput(billingInput)

      // Calculate billing via API
      const statement = await calculateBilling(billingInput)

      actions.setCalculatedStatement(statement)
      actions.setCalculating(false)

      onComplete()
    } catch (err) {
      actions.setCalculating(false)
      actions.setError({
        code: 'CALCULATION_ERROR',
        message: err instanceof Error ? err.message : 'Failed to calculate billing',
      })
      setError(err instanceof Error ? err.message : 'Failed to calculate billing')
    }
  }

  return (
    <div className="kinfolk-card p-8 md:p-12 fade-in">
      <h2 className="text-2xl font-kinfolk-serif mb-8">Billing Parameters</h2>

      {/* Error Display */}
      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-800 text-sm">
          {error}
        </div>
      )}

      {/* Form Sections */}
      <div className="space-y-12">
        <BasicInfoSection
          targetDate={targetDate}
          setTargetDate={setTargetDate}
          uuid={uuid}
          setUuid={setUuid}
          billingGroupId={billingGroupId}
          setBillingGroupId={setBillingGroupId}
          unpaidAmount={unpaidAmount}
          setUnpaidAmount={setUnpaidAmount}
          isOverdue={isOverdue}
          setIsOverdue={setIsOverdue}
        />

        <div className="kinfolk-divider" />

        <UsageInputSection
          usage={usage}
          setUsage={setUsage}
        />

        <div className="kinfolk-divider" />

        <CreditInputSection
          credits={credits}
          setCredits={setCredits}
        />

        <div className="kinfolk-divider" />

        <AdjustmentInputSection
          adjustments={adjustments}
          setAdjustments={setAdjustments}
        />
      </div>

      {/* Calculate Button */}
      <div className="mt-12 flex justify-center">
        <button
          onClick={handleCalculate}
          className="kinfolk-button"
        >
          Calculate Billing
        </button>
      </div>
    </div>
  )
}

export default React.memo(BillingInputForm)
