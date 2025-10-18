/**
 * Usage Input Section - Add/Remove usage entries
 */

'use client'

import React from 'react'
import type { UsageInput } from '@/types/billing'

interface UsageInputSectionProps {
  usage: UsageInput[]
  setUsage: (usage: UsageInput[]) => void
}

// Available instance types with pricing
const INSTANCE_TYPES = [
  {
    value: 'compute.c2.c8m8',
    label: 'compute.c2.c8m8 (8 vCPU, 8GB RAM)',
    unit: 'HOURS',
    description: '일반 컴퓨팅 인스턴스 - ₩397/시간'
  },
  {
    value: 'compute.g2.t4.c8m64',
    label: 'compute.g2.t4.c8m64 (GPU T4, 8 vCPU, 64GB RAM)',
    unit: 'HOURS',
    description: 'GPU 인스턴스 - ₩166.67/시간'
  },
  {
    value: 'storage.volume.ssd',
    label: 'storage.volume.ssd (SSD Storage)',
    unit: 'GB',
    description: 'SSD 블록 스토리지 - ₩100/GB/월'
  },
  {
    value: 'network.floating_ip',
    label: 'network.floating_ip (Floating IP)',
    unit: 'HOURS',
    description: 'Floating IP - ₩25/시간'
  },
]

const UsageInputSection: React.FC<UsageInputSectionProps> = ({ usage, setUsage }) => {
  const addUsage = (): void => {
    const defaultInstance = INSTANCE_TYPES[0]
    const newUsage: UsageInput = {
      id: `usage-${Date.now()}`,
      counterName: defaultInstance.value,
      counterType: 'DELTA',
      counterUnit: defaultInstance.unit,
      counterVolume: 100,
      resourceId: `resource-${Date.now()}`,
      resourceName: 'Test Resource',
      appKey: 'app-kr-master-001',
      projectId: 'project-001',
    }
    setUsage([...usage, newUsage])
  }

  const removeUsage = (id: string): void => {
    setUsage(usage.filter((u) => u.id !== id))
  }

  const updateUsage = (id: string, field: keyof UsageInput, value: string | number): void => {
    setUsage(
      usage.map((u) =>
        u.id === id ? { ...u, [field]: value } : u
      )
    )
  }

  const updateInstanceType = (id: string, counterName: string): void => {
    const instance = INSTANCE_TYPES.find(i => i.value === counterName)
    if (instance) {
      setUsage(
        usage.map((u) =>
          u.id === id ? { ...u, counterName: instance.value, counterUnit: instance.unit } : u
        )
      )
    }
  }

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
                  <label className="kinfolk-label">Instance Type</label>
                  <select
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
                    {INSTANCE_TYPES.find(i => i.value === item.counterName)?.description}
                  </p>
                </div>

                <div>
                  <label className="kinfolk-label">Volume</label>
                  <input
                    type="number"
                    value={item.counterVolume}
                    onChange={(e) => updateUsage(item.id, 'counterVolume', Number(e.target.value))}
                    className="kinfolk-input"
                    min="0"
                    step="1"
                  />
                  <p className="text-xs text-kinfolk-gray-600 mt-1">
                    Unit: {item.counterUnit}
                  </p>
                </div>

                <div>
                  <label className="kinfolk-label">Resource Name</label>
                  <input
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
                  <label className="kinfolk-label">Resource ID</label>
                  <input
                    type="text"
                    value={item.resourceId}
                    onChange={(e) => updateUsage(item.id, 'resourceId', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                <div>
                  <label className="kinfolk-label">App Key</label>
                  <input
                    type="text"
                    value={item.appKey}
                    onChange={(e) => updateUsage(item.id, 'appKey', e.target.value)}
                    className="kinfolk-input"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={() => removeUsage(item.id)}
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

export default React.memo(UsageInputSection)
