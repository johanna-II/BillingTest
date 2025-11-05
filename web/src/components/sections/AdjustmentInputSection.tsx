/**
 * Adjustment Input Section - Discounts and Surcharges
 */

'use client'

import React from 'react'
import { AdjustmentType, AdjustmentLevel, AdjustmentMethod } from '@/types/billing'
import type { AdjustmentInput } from '@/types/billing'

interface AdjustmentInputSectionProps {
  adjustments: AdjustmentInput[]
  setAdjustments: (adjustments: AdjustmentInput[]) => void
}

const AdjustmentInputSection: React.FC<AdjustmentInputSectionProps> = ({
  adjustments,
  setAdjustments,
}) => {
  const addAdjustment = (): void => {
    const newAdjustment: AdjustmentInput = {
      type: AdjustmentType.DISCOUNT,
      level: AdjustmentLevel.PROJECT,
      method: AdjustmentMethod.RATE,
      value: 5,
      description: 'Project Special Discount',
      targetProjectId: 'project-001',
    }
    setAdjustments([...adjustments, newAdjustment])
  }

  const removeAdjustment = (index: number): void => {
    setAdjustments(adjustments.filter((_, i) => i !== index))
  }

  const updateAdjustment = <K extends keyof AdjustmentInput>(
    index: number,
    field: K,
    value: AdjustmentInput[K]
  ): void => {
    setAdjustments(
      adjustments.map((a, i) => (i === index ? { ...a, [field]: value } : a))
    )
  }

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
          {adjustments.map((adjustment, index) => (
            <div key={index} className="p-6 border border-kinfolk-gray-200 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="kinfolk-label">Type</label>
                  <select
                    value={adjustment.type}
                    onChange={(e) =>
                      updateAdjustment(index, 'type', e.target.value as AdjustmentInput['type'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="DISCOUNT">Discount</option>
                    <option value="SURCHARGE">Surcharge</option>
                  </select>
                </div>

                <div>
                  <label className="kinfolk-label">Level</label>
                  <select
                    value={adjustment.level}
                    onChange={(e) =>
                      updateAdjustment(index, 'level', e.target.value as AdjustmentInput['level'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="BILLING_GROUP">Billing Group</option>
                    <option value="PROJECT">Project</option>
                  </select>
                </div>

                <div>
                  <label className="kinfolk-label">Method</label>
                  <select
                    value={adjustment.method}
                    onChange={(e) =>
                      updateAdjustment(index, 'method', e.target.value as AdjustmentInput['method'])
                    }
                    className="kinfolk-input"
                  >
                    <option value="RATE">Rate (%)</option>
                    <option value="FIXED">Fixed Amount</option>
                  </select>
                </div>

                <div>
                  <label className="kinfolk-label">
                    Value {adjustment.method === 'RATE' ? '(%)' : '(₩)'}
                  </label>
                  <input
                    type="number"
                    value={adjustment.value}
                    onChange={(e) => updateAdjustment(index, 'value', Number(e.target.value))}
                    className="kinfolk-input"
                  />
                </div>

                <div>
                  <label className="kinfolk-label">Description</label>
                  <input
                    type="text"
                    value={adjustment.description}
                    onChange={(e) => updateAdjustment(index, 'description', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                {adjustment.level === 'PROJECT' && (
                  <div>
                    <label className="kinfolk-label">Target Project ID</label>
                    <input
                      type="text"
                      value={adjustment.targetProjectId || ''}
                      onChange={(e) => updateAdjustment(index, 'targetProjectId', e.target.value)}
                      className="kinfolk-input"
                      placeholder="project-001"
                    />
                  </div>
                )}

                <div className="md:col-span-3 flex justify-end">
                  <button
                    onClick={() => removeAdjustment(index)}
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
