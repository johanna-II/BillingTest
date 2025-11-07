/**
 * Billing Input Form Component
 * Collects all billing parameters from user
 */

'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useBilling } from '@/contexts/BillingContext'
import { calculateBilling } from '@/lib/api/billing-api'
import { ErrorCode } from '@/types/billing'
import type { BillingInput, UsageInput, CreditInput, AdjustmentInput } from '@/types/billing'
import { BILLING_FORM_DEFAULTS } from '@/constants/forms'
import UsageInputSection from './sections/UsageInputSection'
import CreditInputSection from './sections/CreditInputSection'
import AdjustmentInputSection from './sections/AdjustmentInputSection'
import BasicInfoSection from './sections/BasicInfoSection'

// ============================================================================
// Component
// ============================================================================

interface BillingInputFormProps {
  onComplete: () => void
}

const BillingInputForm: React.FC<BillingInputFormProps> = ({ onComplete }) => {
  const { state, actions } = useBilling()

  // Basic info
  // Note: targetDate always defaults to current date (not from BILLING_FORM_DEFAULTS)
  // This ensures billing calculations are for the current period by default
  const [targetDate, setTargetDate] = useState<Date>(new Date())
  const [uuid, setUuid] = useState(BILLING_FORM_DEFAULTS.UUID)
  const [billingGroupId, setBillingGroupId] = useState(BILLING_FORM_DEFAULTS.BILLING_GROUP_ID)
  const [unpaidAmount, setUnpaidAmount] = useState(BILLING_FORM_DEFAULTS.UNPAID_AMOUNT)
  const [isOverdue, setIsOverdue] = useState(BILLING_FORM_DEFAULTS.IS_OVERDUE)

  // Usage, Credits, Adjustments
  const [usage, setUsage] = useState<UsageInput[]>([])
  const [credits, setCredits] = useState<CreditInput[]>([])
  const [adjustments, setAdjustments] = useState<AdjustmentInput[]>([])

  // Track the last synced billingInput to detect external changes (e.g., history loads)
  const lastSyncedInputRef = useRef<BillingInput | null>(null)

  // Sync form state with BillingContext when a history entry is loaded
  // Uses ref to prevent infinite loops - only updates when billingInput reference changes
  // This pattern is intentional for syncing external state (history load) into form
  useEffect(() => {
    const billingInput = state.billingInput

    // Only update if billingInput reference has changed (external update from history)
    if (billingInput && billingInput !== lastSyncedInputRef.current) {
      lastSyncedInputRef.current = billingInput

      // Update form state to match loaded history entry
      // Note: Data comes from trusted sources (BillingContext/HistoryStore)
      // and is already type-validated. Array.isArray checks are defensive fallbacks.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTargetDate(new Date(billingInput.targetDate))
      setUuid(billingInput.uuid ?? BILLING_FORM_DEFAULTS.UUID)
      setBillingGroupId(billingInput.billingGroupId ?? BILLING_FORM_DEFAULTS.BILLING_GROUP_ID)
      setUsage(Array.isArray(billingInput.usage) ? billingInput.usage as UsageInput[] : [])
      setCredits(Array.isArray(billingInput.credits) ? billingInput.credits as CreditInput[] : [])
      setAdjustments(Array.isArray(billingInput.adjustments) ? billingInput.adjustments as AdjustmentInput[] : [])
      setUnpaidAmount(billingInput.unpaidAmount ?? BILLING_FORM_DEFAULTS.UNPAID_AMOUNT)
      setIsOverdue(billingInput.isOverdue ?? BILLING_FORM_DEFAULTS.IS_OVERDUE)
    }
  }, [state.billingInput])
  const handleCalculate = async (): Promise<void> => {
    // Validation
    if (!uuid || !billingGroupId) {
      actions.setError({
        code: ErrorCode.VALIDATION_ERROR,
        message: 'UUID and Billing Group ID are required',
      })
      return
    }

    if (usage.length === 0) {
      actions.setError({
        code: ErrorCode.VALIDATION_ERROR,
        message: 'At least one usage entry is required',
      })
      return
    }

    actions.setError(null)

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
        code: ErrorCode.CALCULATION_ERROR,
        message: err instanceof Error ? err.message : 'Failed to calculate billing',
      })
    }
  }

  return (
    <div className="kinfolk-card p-8 md:p-12 fade-in">
      <h2 className="text-2xl font-kinfolk-serif mb-8">Billing Parameters</h2>

      {/* Error Display */}
      {state.error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 text-red-800 text-sm">
          {state.error.message}
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
          disabled={state.isCalculating}
          className="kinfolk-button disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {state.isCalculating ? 'Calculating...' : 'Calculate Billing'}
        </button>
      </div>
    </div>
  )
}

export default React.memo(BillingInputForm)
