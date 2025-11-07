/**
 * Usage Input Section - Add/Remove usage entries
 */

'use client'

import { useMemo, useCallback, memo, type Dispatch, type SetStateAction } from 'react'
import { CounterType } from '@/types/billing'
import type { UsageInput } from '@/types/billing'
import { generateUsageId, generateResourceId } from '@/lib/utils/id'
import { INSTANCE_TYPES, getInstanceDescription } from '@/constants/instance-types'
import { getCurrentLocale } from '@/lib/i18n/locale'

interface UsageInputSectionProps {
  usage: UsageInput[]
  setUsage: Dispatch<SetStateAction<UsageInput[]>>
}

function UsageInputSection({ usage, setUsage }: Readonly<UsageInputSectionProps>) {
  // Get locale once to avoid repeated calls during render
  const currentLocale = useMemo(() => getCurrentLocale(), [])

  const addUsage = useCallback((): void => {
    const defaultInstance = INSTANCE_TYPES[0]
    const newUsage: UsageInput = {
      id: generateUsageId(),
      counterName: defaultInstance.value,
      counterType: CounterType.DELTA,
      counterUnit: defaultInstance.unit,
      counterVolume: 0,
      resourceId: generateResourceId(),
      resourceName: '',
      appKey: '',
      projectId: '',
    }
    setUsage(prev => [...prev, newUsage])
  }, [setUsage])

  const removeUsage = useCallback((id: string): void => {
    setUsage(prev => prev.filter((u) => u.id !== id))
  }, [setUsage])

  const updateUsage = useCallback((id: string, field: keyof UsageInput, value: string | number): void => {
    setUsage(prev =>
      prev.map((u) =>
        u.id === id ? { ...u, [field]: value } : u
      )
    )
  }, [setUsage])

  const updateInstanceType = useCallback((id: string, counterName: string): void => {
    const instance = INSTANCE_TYPES.find(i => i.value === counterName)
    if (instance) {
      setUsage(prev =>
        prev.map((u) =>
          u.id === id ? { ...u, counterName: instance.value, counterUnit: instance.unit } : u
        )
      )
    }
  }, [setUsage])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="kinfolk-subheading">Usage Entries</h3>
        <button onClick={addUsage} className="kinfolk-button-secondary text-xs py-2 px-6">
          Add Usage
        </button>
      </div>

      {usage.length === 0 ? (
        <p className="text-sm text-kinfolk-gray-500 text-center py-8">
          No usage entries. Click "Add Usage" to get started.
        </p>
      ) : (
        <div className="space-y-6">
          {usage.map((item) => (
            <div key={item.id} className="p-6 border border-kinfolk-gray-200 bg-white">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="md:col-span-2">
                  <label htmlFor={`usage-instance-${item.id}`} className="kinfolk-label">
                    Instance Type
                  </label>
                  <select
                    id={`usage-instance-${item.id}`}
                    value={item.counterName}
                    onChange={(e) => updateInstanceType(item.id, e.target.value)}
                    className="kinfolk-input"
                  >
                    {INSTANCE_TYPES.map((instance) => (
                      <option key={instance.value} value={instance.value}>
                        {instance.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-kinfolk-gray-600 mt-1">
                    {getInstanceDescription(item.counterName, currentLocale)}
                  </p>
                </div>

                <div>
                  <label htmlFor={`usage-volume-${item.id}`} className="kinfolk-label">
                    Volume
                  </label>
                  <input
                    id={`usage-volume-${item.id}`}
                    type="number"
                    value={item.counterVolume}
                    onChange={(e) => {
                      const inputValue = e.target.value

                      // Explicit handling of empty input
                      if (inputValue === '') {
                        updateUsage(item.id, 'counterVolume', 0)
                        return
                      }

                      // Validate numeric input
                      const value = Number(inputValue)
                      if (!Number.isNaN(value) && value >= 0) {
                        updateUsage(item.id, 'counterVolume', value)
                      }
                    }}
                    className="kinfolk-input"
                    min="0"
                    step="1"
                  />
                  <p className="text-xs text-kinfolk-gray-600 mt-1">
                    Unit: {item.counterUnit}
                  </p>
                </div>

                <div>
                  <label htmlFor={`usage-name-${item.id}`} className="kinfolk-label">
                    Resource Name
                  </label>
                  <input
                    id={`usage-name-${item.id}`}
                    type="text"
                    value={item.resourceName || ''}
                    onChange={(e) => updateUsage(item.id, 'resourceName', e.target.value)}
                    className="kinfolk-input"
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor={`usage-resource-${item.id}`} className="kinfolk-label">
                    Resource ID
                  </label>
                  <input
                    id={`usage-resource-${item.id}`}
                    type="text"
                    value={item.resourceId}
                    onChange={(e) => updateUsage(item.id, 'resourceId', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                <div>
                  <label htmlFor={`usage-appkey-${item.id}`} className="kinfolk-label">
                    App Key
                  </label>
                  <input
                    id={`usage-appkey-${item.id}`}
                    type="text"
                    value={item.appKey}
                    onChange={(e) => updateUsage(item.id, 'appKey', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>
              </div>

              {/* Remove button - full width for better layout */}
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => removeUsage(item.id)}
                  className="text-sm text-red-600 hover:text-red-800 uppercase tracking-widest"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default memo(UsageInputSection)
