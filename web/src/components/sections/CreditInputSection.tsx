/**
 * Credit Input Section
 */

'use client'

import React from 'react'
import type { CreditInput } from '@/types/billing'

interface CreditInputSectionProps {
  credits: CreditInput[]
  setCredits: (credits: CreditInput[]) => void
}

const CreditInputSection: React.FC<CreditInputSectionProps> = ({ credits, setCredits }) => {
  const addCredit = (): void => {
    const newCredit: CreditInput = {
      type: 'FREE',
      amount: 10000,
      name: 'Test Credit',
    }
    setCredits([...credits, newCredit])
  }

  const removeCredit = (index: number): void => {
    setCredits(credits.filter((_, i) => i !== index))
  }

  const updateCredit = <K extends keyof CreditInput>(
    index: number,
    field: K,
    value: CreditInput[K]
  ): void => {
    setCredits(
      credits.map((c, i) => (i === index ? { ...c, [field]: value } : c))
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
          {credits.map((credit, index) => (
            <div key={index} className="p-6 border border-kinfolk-gray-200 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="kinfolk-label">Type</label>
                  <select
                    value={credit.type}
                    onChange={(e) =>
                      updateCredit(index, 'type', e.target.value as CreditInput['type'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="FREE">Free</option>
                    <option value="PAID">Paid</option>
                    <option value="PROMOTIONAL">Promotional</option>
                  </select>
                </div>

                <div>
                  <label className="kinfolk-label">Amount (₩)</label>
                  <input
                    type="number"
                    value={credit.amount}
                    onChange={(e) => updateCredit(index, 'amount', Number(e.target.value))}
                    className="kinfolk-input"
                  />
                </div>

                <div>
                  <label className="kinfolk-label">Name</label>
                  <input
                    type="text"
                    value={credit.name}
                    onChange={(e) => updateCredit(index, 'name', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                <div className="md:col-span-3 flex justify-end">
                  <button
                    onClick={() => removeCredit(index)}
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
