/**
 * Adjustment Input Section - Discounts and Surcharges
 */

'use client'

import React from 'react'
import { AdjustmentType, AdjustmentLevel, AdjustmentMethod } from '@/types/billing'
import type { AdjustmentInput } from '@/types/billing'
import { generateAdjustmentId } from '@/lib/utils/id'

interface AdjustmentInputSectionProps {
  adjustments: AdjustmentInput[]
  setAdjustments: (adjustments: AdjustmentInput[]) => void
}

const AdjustmentInputSection: React.FC<AdjustmentInputSectionProps> = ({
  adjustments,
  setAdjustments,
}) => {
  // Memoize callbacks to prevent unnecessary re-renders
  const addAdjustment = React.useCallback((): void => {
    const newAdjustment: AdjustmentInput = {
      id: generateAdjustmentId(),
      type: AdjustmentType.DISCOUNT,
      level: AdjustmentLevel.BILLING_GROUP,
      method: AdjustmentMethod.RATE,
      value: 0,
      description: '',
      targetProjectId: '',
    }
    setAdjustments([...adjustments, newAdjustment])
  }, [adjustments, setAdjustments])

  const removeAdjustment = React.useCallback((id: string): void => {
    setAdjustments(adjustments.filter((a) => a.id !== id))
  }, [adjustments, setAdjustments])

  const updateAdjustment = React.useCallback(<K extends keyof AdjustmentInput>(
    id: string,
    field: K,
    value: AdjustmentInput[K]
  ): void => {
    setAdjustments(
      adjustments.map((a) => (a.id === id ? { ...a, [field]: value } : a))
    )
  }, [adjustments, setAdjustments])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="kinfolk-subheading">Adjustments</h3>
        <button onClick={addAdjustment} className="kinfolk-button-secondary text-xs py-2 px-6">
          Add Adjustment
        </button>
      </div>

      {adjustments.length === 0 ? (
        <p className="text-sm text-kinfolk-gray-500 text-center py-8">
          No adjustments. Add discounts or surcharges.
        </p>
      ) : (
        <div className="space-y-4">
          {adjustments.map((adjustment) => (
            <div key={adjustment.id} className="p-6 border border-kinfolk-gray-200 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor={`adj-type-${adjustment.id}`} className="kinfolk-label">
                    Type
                  </label>
                  <select
                    id={`adj-type-${adjustment.id}`}
                    value={adjustment.type}
                    onChange={(e) =>
                      updateAdjustment(adjustment.id, 'type', e.target.value as AdjustmentInput['type'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="DISCOUNT">Discount</option>
                    <option value="SURCHARGE">Surcharge</option>
                  </select>
                </div>

                <div>
                  <label htmlFor={`adj-level-${adjustment.id}`} className="kinfolk-label">
                    Level
                  </label>
                  <select
                    id={`adj-level-${adjustment.id}`}
                    value={adjustment.level}
                    onChange={(e) =>
                      updateAdjustment(adjustment.id, 'level', e.target.value as AdjustmentInput['level'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="BILLING_GROUP">Billing Group</option>
                    <option value="PROJECT">Project</option>
                  </select>
                </div>

                <div>
                  <label htmlFor={`adj-method-${adjustment.id}`} className="kinfolk-label">
                    Method
                  </label>
                  <select
                    id={`adj-method-${adjustment.id}`}
                    value={adjustment.method}
                    onChange={(e) =>
                      updateAdjustment(adjustment.id, 'method', e.target.value as AdjustmentInput['method'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="RATE">Rate (%)</option>
                    <option value="FIXED">Fixed Amount</option>
                  </select>
                </div>

                <div>
                  <label htmlFor={`adj-value-${adjustment.id}`} className="kinfolk-label">
                    Value {adjustment.method === 'RATE' ? '(%)' : '(₩)'}
                  </label>
                  <input
                    id={`adj-value-${adjustment.id}`}
                    type="number"
                    value={adjustment.value}
                    onChange={(e) => {
                      const inputValue = e.target.value

                      // Explicit handling of empty input
                      if (inputValue === '') {
                        updateAdjustment(adjustment.id, 'value', 0)
                        return
                      }

                      // Validate numeric input with range check
                      const value = Number(inputValue)
                      if (!Number.isNaN(value) && value >= 0) {
                        updateAdjustment(adjustment.id, 'value', value)
                      }
                    }}
                    className="kinfolk-input"
                    min={0}
                    max={adjustment.method === AdjustmentMethod.RATE ? 100 : undefined}
                    step={adjustment.method === AdjustmentMethod.RATE ? 0.1 : 1}
                  />
                </div>

                <div>
                  <label htmlFor={`adj-desc-${adjustment.id}`} className="kinfolk-label">
                    Description
                  </label>
                  <input
                    id={`adj-desc-${adjustment.id}`}
                    type="text"
                    value={adjustment.description}
                    onChange={(e) => updateAdjustment(adjustment.id, 'description', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                {adjustment.level === 'PROJECT' && (
                  <div>
                    <label htmlFor={`adj-project-${adjustment.id}`} className="kinfolk-label">
                      Target Project ID
                    </label>
                    <input
                      id={`adj-project-${adjustment.id}`}
                      type="text"
                      value={adjustment.targetProjectId || ''}
                      onChange={(e) => updateAdjustment(adjustment.id, 'targetProjectId', e.target.value)}
                      className="kinfolk-input"
                      placeholder="project-001"
                    />
                  </div>
                )}

                <div className="md:col-span-3 flex justify-end">
                  <button
                    onClick={() => removeAdjustment(adjustment.id)}
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

export default React.memo(AdjustmentInputSection)
