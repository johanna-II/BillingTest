/**
 * History Store with Zustand
 * Manages calculation history with localStorage persistence
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { BillingInput, BillingStatement, PaymentResult } from '@/types/billing'

export interface HistoryEntry {
  id: string
  timestamp: Date
  input: BillingInput
  statement: BillingStatement | null
  payment: PaymentResult | null
  notes?: string
}

interface HistoryStore {
  history: HistoryEntry[]
  addEntry: (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => void
  updateEntry: (id: string, updates: Partial<HistoryEntry>) => void
  deleteEntry: (id: string) => void
  clearHistory: () => void
  getEntry: (id: string) => HistoryEntry | undefined
}

export const useHistoryStore = create<HistoryStore>()(
  persist(
    (set, get) => ({
      history: [],

      addEntry: (entry) => {
        const newEntry: HistoryEntry = {
          ...entry,
          id: `entry-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
        }
        set((state) => ({
          history: [newEntry, ...state.history].slice(0, 50), // Keep last 50 entries
        }))
      },

      updateEntry: (id, updates) => {
        set((state) => ({
          history: state.history.map((entry: HistoryEntry) =>
            entry.id === id ? { ...entry, ...updates } : entry
          ),
        }))
      },

      deleteEntry: (id) => {
        set((state) => ({
          history: state.history.filter((entry: HistoryEntry) => entry.id !== id),
        }))
      },

      clearHistory: () => {
        set({ history: [] })
      },

      getEntry: (id) => {
        return get().history.find((entry: HistoryEntry) => entry.id === id)
      },
    }),
    {
      name: 'billing-history-storage',
      // Custom serialization to handle Date objects
      partialize: (state) => ({
        history: state.history.map((entry: HistoryEntry) => ({
          ...entry,
          timestamp: entry.timestamp instanceof Date ? entry.timestamp.toISOString() : entry.timestamp,
          input: {
            ...entry.input,
            targetDate: entry.input.targetDate instanceof Date ? entry.input.targetDate.toISOString() : entry.input.targetDate,
          },
          statement: entry.statement ? {
            ...entry.statement,
            dueDate: entry.statement.dueDate instanceof Date ? entry.statement.dueDate.toISOString() : entry.statement.dueDate,
            createdAt: entry.statement.createdAt instanceof Date ? entry.statement.createdAt.toISOString() : entry.statement.createdAt,
          } : null,
          payment: entry.payment ? {
            ...entry.payment,
            transactionDate: entry.payment.transactionDate instanceof Date ? entry.payment.transactionDate.toISOString() : entry.payment.transactionDate,
          } : null,
        })),
      }),
      // Custom deserialization to convert strings back to Date objects
      merge: (persistedState: any, currentState: HistoryStore) => {
        if (!persistedState || !persistedState.history) {
          return currentState
        }

        return {
          ...currentState,
          history: persistedState.history.map((entry: any) => ({
            ...entry,
            timestamp: typeof entry.timestamp === 'string' ? new Date(entry.timestamp) : entry.timestamp,
            input: {
              ...entry.input,
              targetDate: typeof entry.input.targetDate === 'string' ? new Date(entry.input.targetDate) : entry.input.targetDate,
            },
            statement: entry.statement ? {
              ...entry.statement,
              dueDate: typeof entry.statement.dueDate === 'string' ? new Date(entry.statement.dueDate) : entry.statement.dueDate,
              createdAt: typeof entry.statement.createdAt === 'string' ? new Date(entry.statement.createdAt) : entry.statement.createdAt,
            } : null,
            payment: entry.payment ? {
              ...entry.payment,
              transactionDate: typeof entry.payment.transactionDate === 'string' ? new Date(entry.payment.transactionDate) : entry.payment.transactionDate,
            } : null,
          })),
        }
      },
    }
  )
)
