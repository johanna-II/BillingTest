/**
 * Basic Info Section - Date, UUID, Billing Group, Unpaid Amount
 */

'use client'

import React from 'react'
import { format } from 'date-fns'

interface BasicInfoSectionProps {
  targetDate: Date
  setTargetDate: (date: Date) => void
  uuid: string
  setUuid: (uuid: string) => void
  billingGroupId: string
  setBillingGroupId: (id: string) => void
  unpaidAmount: number
  setUnpaidAmount: (amount: number) => void
  isOverdue: boolean
  setIsOverdue: (overdue: boolean) => void
}

const BasicInfoSection: React.FC<BasicInfoSectionProps> = ({
  targetDate,
  setTargetDate,
  uuid,
  setUuid,
  billingGroupId,
  setBillingGroupId,
  unpaidAmount,
  setUnpaidAmount,
  isOverdue,
  setIsOverdue,
}) => {
  return (
    <div>
      <h3 className="kinfolk-subheading">Basic Information</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Target Date */}
        <div>
          <label className="kinfolk-label" htmlFor="targetDate">
            Target Date
          </label>
          <input
            id="targetDate"
            type="date"
            value={format(targetDate, 'yyyy-MM-dd')}
            onChange={(e) => {
              // Use valueAsDate for correct local timezone handling
              // Prevents UTC parsing which causes off-by-one date shifts
              const date = e.target.valueAsDate

              // Validate: valueAsDate is null for empty/invalid input
              if (date && !Number.isNaN(date.getTime())) {
                setTargetDate(date)
              }
            }}
            className="kinfolk-input"
          />
        </div>

        {/* UUID */}
        <div>
          <label className="kinfolk-label" htmlFor="uuid">
            UUID
          </label>
          <input
            id="uuid"
            type="text"
            value={uuid}
            onChange={(e) => setUuid(e.target.value)}
            placeholder="test-uuid-001"
            className="kinfolk-input"
          />
        </div>

        {/* Billing Group ID */}
        <div>
          <label className="kinfolk-label" htmlFor="billingGroupId">
            Billing Group ID
          </label>
          <input
            id="billingGroupId"
            type="text"
            value={billingGroupId}
            onChange={(e) => setBillingGroupId(e.target.value)}
            placeholder="bg-kr-test"
            className="kinfolk-input"
          />
        </div>

        {/* Unpaid Amount */}
        <div>
          <label className="kinfolk-label" htmlFor="unpaidAmount">
            Unpaid Amount (₩)
          </label>
          <input
            id="unpaidAmount"
            type="number"
            value={unpaidAmount}
            onChange={(e) => {
              const inputValue = e.target.value

              // Explicit handling of empty input
              if (inputValue === '') {
                setUnpaidAmount(0)
                return
              }

              // Validate numeric input
              const value = Number(inputValue)
              if (!Number.isNaN(value) && value >= 0) {
                setUnpaidAmount(value)
              }
            }}
            min="0"
            step="1000"
            className="kinfolk-input"
          />
        </div>

        {/* Is Overdue Checkbox */}
        <div className="flex items-center space-x-3 pt-8">
          <input
            id="isOverdue"
            type="checkbox"
            checked={isOverdue}
            onChange={(e) => setIsOverdue(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="isOverdue" className="text-sm text-kinfolk-gray-700">
            Payment is overdue (applies late fee)
          </label>
        </div>
      </div>
    </div>
  )
}

export default React.memo(BasicInfoSection)
