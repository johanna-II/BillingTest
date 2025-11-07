/**
 * Credit Input Section
 */

'use client'

import React from 'react'
import { CreditType } from '@/types/billing'
import type { CreditInput } from '@/types/billing'
import { generateCreditId } from '@/lib/utils/id'

interface CreditInputSectionProps {
  credits: CreditInput[]
  setCredits: (credits: CreditInput[]) => void
}

function CreditInputSection({ credits, setCredits }: Readonly<CreditInputSectionProps>) {
  const addCredit = (): void => {
    const newCredit: CreditInput = {
      id: generateCreditId(),
      type: CreditType.FREE,
      amount: 0,
      name: '',
    }
    setCredits([...credits, newCredit])
  }

  const removeCredit = (id: string): void => {
    setCredits(credits.filter((c) => c.id !== id))
  }

  const updateCredit = <K extends keyof CreditInput>(
    id: string,
    field: K,
    value: CreditInput[K]
  ): void => {
    setCredits(
      credits.map((c) => (c.id === id ? { ...c, [field]: value } : c))
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="kinfolk-subheading">Credits</h3>
        <button onClick={addCredit} className="kinfolk-button-secondary text-xs py-2 px-6">
          Add Credit
        </button>
      </div>

      {credits.length === 0 ? (
        <p className="text-sm text-kinfolk-gray-500 text-center py-8">
          No credits. Add credits to reduce billing amount.
        </p>
      ) : (
        <div className="space-y-4">
          {credits.map((credit) => (
            <div key={credit.id} className="p-6 border border-kinfolk-gray-200 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor={`credit-type-${credit.id}`} className="kinfolk-label">
                    Type
                  </label>
                  <select
                    id={`credit-type-${credit.id}`}
                    value={credit.type}
                    onChange={(e) =>
                      updateCredit(credit.id, 'type', e.target.value as CreditInput['type'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="FREE">Free</option>
                    <option value="PAID">Paid</option>
                    <option value="PROMOTIONAL">Promotional</option>
                  </select>
                </div>

                <div>
                  <label htmlFor={`credit-amount-${credit.id}`} className="kinfolk-label">
                    Amount (₩)
                  </label>
                  <input
                    id={`credit-amount-${credit.id}`}
                    type="number"
                    value={credit.amount}
                    onChange={(e) => {
                      const inputValue = e.target.value

                      // Explicit handling of empty input
                      if (inputValue === '') {
                        updateCredit(credit.id, 'amount', 0)
                        return
                      }

                      // Validate numeric input
                      const value = Number(inputValue)
                      if (!Number.isNaN(value) && value >= 0) {
                        updateCredit(credit.id, 'amount', value)
                      }
                    }}
                    className="kinfolk-input"
                    min={0}
                    step={1}
                  />
                </div>

                <div>
                  <label htmlFor={`credit-name-${credit.id}`} className="kinfolk-label">
                    Name
                  </label>
                  <input
                    id={`credit-name-${credit.id}`}
                    type="text"
                    value={credit.name}
                    onChange={(e) => updateCredit(credit.id, 'name', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                <div className="md:col-span-3 flex justify-end">
                  <button
                    onClick={() => removeCredit(credit.id)}
                    className="text-sm text-red-600 hover:text-red-800 uppercase tracking-widest"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default React.memo(CreditInputSection)
