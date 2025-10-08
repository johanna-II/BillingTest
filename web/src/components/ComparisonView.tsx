/**
 * Comparison View Component
 * Compare multiple billing scenarios side by side
 */

'use client'

import React, { useState } from 'react'
import { useHistoryStore, type HistoryEntry } from '@/stores/historyStore'
import { format } from 'date-fns'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const ComparisonView: React.FC = () => {
  const { history } = useHistoryStore()
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  // Filter entries with statements
  const comparableEntries = history.filter((entry) => entry.statement !== null)

  const toggleSelection = (id: string): void => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id].slice(-4)
    )
  }

  const selectedEntries = comparableEntries.filter((entry) =>
    selectedIds.includes(entry.id)
  )

  // Prepare chart data
  const chartData = selectedEntries.map((entry, index) => ({
    name: `Scenario ${index + 1}`,
    Subtotal: entry.statement!.subtotal,
    Adjustments: Math.abs(entry.statement!.adjustmentTotal),
    Credits: entry.statement!.creditApplied,
    Total: entry.statement!.totalAmount,
  }))

  const formatCurrency = (amount: number): string => {
    return `₩${amount.toLocaleString('ko-KR')}`
  }

  return (
    <div className="kinfolk-card p-8 md:p-12 fade-in">
      <h2 className="text-2xl font-kinfolk-serif mb-8">Scenario Comparison</h2>

      {comparableEntries.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-kinfolk-gray-600">
            No scenarios available for comparison. Calculate some billing first.
          </p>
        </div>
      ) : (
        <>
          {/* Selection */}
          <div className="mb-8">
            <h3 className="kinfolk-subheading mb-4">
              Select Scenarios (up to 4)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {comparableEntries.slice(0, 10).map((entry) => (
                <label
                  key={entry.id}
                  className={`
                    p-4 border cursor-pointer transition-all
                    ${
                      selectedIds.includes(entry.id)
                        ? 'border-kinfolk-gray-900 bg-kinfolk-beige-50'
                        : 'border-kinfolk-gray-200 hover:border-kinfolk-gray-400'
                    }
                  `}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(entry.id)}
                    onChange={() => toggleSelection(entry.id)}
                    disabled={
                      !selectedIds.includes(entry.id) && selectedIds.length >= 4
                    }
                    className="mr-3"
                  />
                  <span className="text-sm font-medium">
                    {entry.input.billingGroupId}
                  </span>
                  <span className="text-xs text-kinfolk-gray-500 ml-2">
                    ({format(
                      typeof entry.timestamp === 'string' 
                        ? new Date(entry.timestamp) 
                        : entry.timestamp, 
                      'PP'
                    )})
                  </span>
                  {entry.statement && (
                    <div className="mt-2 text-xs text-kinfolk-gray-600">
                      Total: {formatCurrency(entry.statement.totalAmount)}
                    </div>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Comparison Results */}
          {selectedEntries.length > 0 && (
            <>
              <div className="kinfolk-divider" />

              {/* Chart */}
              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">Visual Comparison</h3>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis
                        dataKey="name"
                        tick={{ fontSize: 12, fill: '#737373' }}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: '#737373' }}
                        tickFormatter={(value) => `₩${(value / 1000).toFixed(0)}K`}
                      />
                      <Tooltip
                        formatter={(value: number) => `₩${value.toLocaleString()}`}
                      />
                      <Legend />
                      <Bar dataKey="Subtotal" fill="#171717" />
                      <Bar dataKey="Adjustments" fill="#737373" />
                      <Bar dataKey="Credits" fill="#22c55e" />
                      <Bar dataKey="Total" fill="#ef4444" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Table Comparison */}
              <div>
                <h3 className="kinfolk-subheading mb-4">Detailed Comparison</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-kinfolk-gray-300">
                        <th className="text-left py-3 px-2 text-xs uppercase tracking-widest text-kinfolk-gray-600">
                          Item
                        </th>
                        {selectedEntries.map((_, index) => (
                          <th
                            key={index}
                            className="text-right py-3 px-2 text-xs uppercase tracking-widest text-kinfolk-gray-600"
                          >
                            Scenario {index + 1}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Billing Group</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right font-mono text-xs">
                            {entry.input.billingGroupId}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Subtotal</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right">
                            {formatCurrency(entry.statement!.subtotal)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Adjustments</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right">
                            {formatCurrency(entry.statement!.adjustmentTotal)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Credits Applied</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right text-green-600">
                            -{formatCurrency(entry.statement!.creditApplied)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Unpaid Amount</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right text-red-600">
                            {formatCurrency(entry.statement!.unpaidAmount)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b-2 border-kinfolk-gray-900">
                        <td className="py-3 px-2 font-medium">Total Amount</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right font-bold">
                            {formatCurrency(entry.statement!.totalAmount)}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Usage Entries</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right">
                            {entry.input.usage.length}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Credits</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right">
                            {entry.input.credits.length}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-kinfolk-gray-100">
                        <td className="py-3 px-2">Adjustments</td>
                        {selectedEntries.map((entry) => (
                          <td key={entry.id} className="py-3 px-2 text-right">
                            {entry.input.adjustments.length}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default React.memo(ComparisonView)

