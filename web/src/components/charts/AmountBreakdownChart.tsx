/**
 * Amount Breakdown Chart Component
 * Visualizes billing amounts with recharts
 */

'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type PieLabelRenderProps,
} from 'recharts'
import type { BillingStatement } from '@/types/billing'

interface AmountBreakdownChartProps {
  statement: BillingStatement
  type?: 'bar' | 'pie'
}

const COLORS = {
  subtotal: '#171717',
  adjustments: '#737373',
  credits: '#22c55e',
  unpaid: '#ef4444',
  lateFee: '#f97316',
}

const AmountBreakdownChart: React.FC<AmountBreakdownChartProps> = ({
  statement,
  type = 'bar',
}) => {
  // Prepare data
  const data = [
    {
      name: 'Subtotal',
      amount: statement.subtotal,
      color: COLORS.subtotal,
    },
    statement.adjustmentTotal !== 0 && {
      name: 'Adjustments',
      amount: Math.abs(statement.adjustmentTotal),
      color: COLORS.adjustments,
    },
    statement.creditApplied > 0 && {
      name: 'Credits',
      amount: statement.creditApplied,
      color: COLORS.credits,
    },
    statement.unpaidAmount > 0 && {
      name: 'Unpaid',
      amount: statement.unpaidAmount,
      color: COLORS.unpaid,
    },
    statement.lateFee > 0 && {
      name: 'Late Fee',
      amount: statement.lateFee,
      color: COLORS.lateFee,
    },
  ].filter(Boolean) as Array<{ name: string; amount: number; color: string }>

  const formatCurrency = (value: number): string => {
    return `₩${(value / 1000).toFixed(0)}K`
  }

  const formatPieLabel = (entry: PieLabelRenderProps): string => {
    const name = entry.name as string
    const amount = entry.value as number
    return `${name}: ${formatCurrency(amount)}`
  }

  if (type === 'pie') {
    return (
      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="amount"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={formatPieLabel}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number | undefined) =>
              value !== undefined ? `₩${value.toLocaleString()}` : ''
            } />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 12, fill: '#737373' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#737373' }}
            tickLine={false}
            tickFormatter={formatCurrency}
          />
          <Tooltip
            formatter={(value: number | undefined) =>
              value !== undefined ? `₩${value.toLocaleString()}` : ''
            }
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e5e5',
              borderRadius: 0,
            }}
          />
          <Legend />
          <Bar dataKey="amount" fill="#171717">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default React.memo(AmountBreakdownChart)
