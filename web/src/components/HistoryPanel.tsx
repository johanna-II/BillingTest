/**
 * History Panel Component
 * Shows calculation history with search and filtering
 */

'use client'

import React, { useState, useMemo } from 'react'
import { useHistoryStore } from '@/stores/historyStore'
import { format } from 'date-fns'
import { motion, AnimatePresence } from 'motion/react'

interface HistoryPanelProps {
  onLoadEntry: (entryId: string) => void
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ onLoadEntry }) => {
  const { history, deleteEntry, clearHistory } = useHistoryStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  // Filter history
  const filteredHistory = useMemo(() => {
    if (!searchTerm) return history

    const term = searchTerm.toLowerCase()
    return history.filter(
      (entry) =>
        entry.input.uuid.toLowerCase().includes(term) ||
        entry.input.billingGroupId.toLowerCase().includes(term) ||
        entry.notes?.toLowerCase().includes(term)
    )
  }, [history, searchTerm])

  const formatCurrency = (amount: number): string => {
    return `₩${amount.toLocaleString('ko-KR')}`
  }

  const formatDate = (timestamp: Date | string): string => {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
    return format(date, 'PPp')
  }

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed right-6 bottom-6 z-50 rounded-full w-14 h-14 flex items-center justify-center shadow-lg bg-kinfolk-gray-900 text-white hover:bg-kinfolk-gray-700 transition-all duration-300 border-2 border-kinfolk-gray-900 hover:border-kinfolk-gray-700"
        title="History"
        aria-label="Toggle History Panel"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </button>

      {/* Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/30 z-40"
            />

            {/* Panel Content */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 bottom-0 w-full md:w-[480px] bg-white shadow-2xl z-50 overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="p-6 border-b border-kinfolk-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-kinfolk-serif">History</h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-kinfolk-gray-500 hover:text-kinfolk-gray-900"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Search */}
                <input
                  type="text"
                  placeholder="Search by UUID, Billing Group..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="kinfolk-input text-sm"
                />

                {/* Clear All */}
                {history.length > 0 && (
                  <button
                    onClick={() => {
                      if (confirm('Clear all history?')) {
                        clearHistory()
                      }
                    }}
                    className="mt-3 text-xs text-red-600 hover:text-red-800 uppercase tracking-widest"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {/* History List */}
              <div className="flex-1 overflow-y-auto p-6">
                {filteredHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-sm text-kinfolk-gray-500">
                      {history.length === 0
                        ? 'No history yet. Calculate some billing to get started.'
                        : 'No matching results.'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredHistory.map((entry) => (
                      <div
                        key={entry.id}
                        className="border border-kinfolk-gray-200 p-4 hover:border-kinfolk-gray-400 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <p className="text-sm font-medium text-kinfolk-gray-900">
                              {entry.input.billingGroupId}
                            </p>
                            <p className="text-xs text-kinfolk-gray-500">
                              {formatDate(entry.timestamp)}
                            </p>
                          </div>
                          <button
                            onClick={() => deleteEntry(entry.id)}
                            className="text-kinfolk-gray-400 hover:text-red-600"
                            title="Delete"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>

                        <div className="space-y-1 mb-3 text-xs">
                          <div className="flex justify-between">
                            <span className="text-kinfolk-gray-600">UUID:</span>
                            <span className="font-mono">{entry.input.uuid}</span>
                          </div>
                          {entry.statement && (
                            <div className="flex justify-between font-medium">
                              <span className="text-kinfolk-gray-600">Total:</span>
                              <span>{formatCurrency(entry.statement.totalAmount)}</span>
                            </div>
                          )}
                          {entry.payment && (
                            <div className="flex justify-between">
                              <span className="text-kinfolk-gray-600">Payment:</span>
                              <span className={entry.payment.status === 'SUCCESS' ? 'text-green-600' : 'text-red-600'}>
                                {entry.payment.status}
                              </span>
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => {
                            onLoadEntry(entry.id)
                            setIsOpen(false)
                          }}
                          className="text-xs uppercase tracking-widest text-kinfolk-gray-900 hover:underline"
                        >
                          Load This Entry →
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export default React.memo(HistoryPanel)
