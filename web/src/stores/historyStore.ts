/**
 * History Store - Zustand State Management
 * Type-safe localStorage persistence with proper serialization
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { BillingInput, BillingStatement, PaymentResult } from '@/types/billing'

// ============================================================================
// Configuration
// ============================================================================

const STORE_CONFIG = {
  STORAGE: {
    NAME: 'billing-history-storage',
    MAX_ENTRIES: 50,
  },
  ID: {
    PREFIX: 'entry-',
    RANDOM_LENGTH: 9,
    RANDOM_BASE: 36,
  },
} as const

// ============================================================================
// Types
// ============================================================================

export interface HistoryEntry {
  readonly id: string
  readonly timestamp: Date
  readonly input: BillingInput
  readonly statement: BillingStatement | null
  readonly payment: PaymentResult | null
  readonly notes?: string
}

interface SerializedHistoryEntry {
  readonly id: string
  readonly timestamp: string
  readonly input: SerializedBillingInput
  readonly statement: SerializedBillingStatement | null
  readonly payment: SerializedPaymentResult | null
  readonly notes?: string
}

interface SerializedBillingInput extends Omit<BillingInput, 'targetDate'> {
  readonly targetDate: string
}

interface SerializedBillingStatement extends Omit<BillingStatement, 'dueDate' | 'createdAt'> {
  readonly dueDate?: string
  readonly createdAt?: string
}

interface SerializedPaymentResult extends Omit<PaymentResult, 'transactionDate'> {
  readonly transactionDate: string
}

interface PersistedState {
  readonly history: ReadonlyArray<SerializedHistoryEntry>
}

// ============================================================================
// Store Interface
// ============================================================================

interface HistoryStore {
  readonly history: ReadonlyArray<HistoryEntry>
  readonly addEntry: (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => void
  readonly updateEntry: (id: string, updates: Partial<Omit<HistoryEntry, 'id' | 'timestamp'>>) => void
  readonly deleteEntry: (id: string) => void
  readonly clearHistory: () => void
  readonly getEntry: (id: string) => HistoryEntry | undefined
}

// ============================================================================
// Serialization Helpers
// ============================================================================

const serializeDate = (date: Date | undefined): string | undefined => {
  return date instanceof Date ? date.toISOString() : undefined
}

const deserializeDate = (dateStr: string | undefined): Date | undefined => {
  if (!dateStr) return undefined
  const date = new Date(dateStr)
  return Number.isNaN(date.getTime()) ? undefined : date
}

const serializeHistoryEntry = (entry: HistoryEntry): SerializedHistoryEntry => {
  return {
    id: entry.id,
    timestamp: entry.timestamp.toISOString(),
    input: {
      ...entry.input,
      targetDate: entry.input.targetDate.toISOString(),
    },
    statement: entry.statement
      ? {
          ...entry.statement,
          dueDate: serializeDate(entry.statement.dueDate),
          createdAt: serializeDate(entry.statement.createdAt),
        }
      : null,
    payment: entry.payment
      ? {
          ...entry.payment,
          transactionDate: entry.payment.transactionDate.toISOString(),
        }
      : null,
    notes: entry.notes,
  }
}

const deserializeHistoryEntry = (serialized: SerializedHistoryEntry): HistoryEntry => {
  // Deserialize and validate all required date fields
  const timestamp = deserializeDate(serialized.timestamp)
  const targetDate = deserializeDate(serialized.input.targetDate)

  // Ensure required date fields are valid
  if (!timestamp || !targetDate) {
    throw new Error(
      `Invalid required date fields in history entry: ${serialized.id}. ` +
      `timestamp=${serialized.timestamp}, targetDate=${serialized.input.targetDate}`
    )
  }

  // Deserialize payment transaction date with validation
  let transactionDate: Date | undefined
  if (serialized.payment) {
    transactionDate = deserializeDate(serialized.payment.transactionDate)
    if (!transactionDate) {
      // Use epoch as fallback for corrupted payment date to preserve data
      console.warn(
        `Invalid transactionDate in history entry ${serialized.id}: ${serialized.payment.transactionDate}. Using epoch.`
      )
      transactionDate = new Date(0)
    }
  }

  return {
    id: serialized.id,
    timestamp,
    input: {
      ...serialized.input,
      targetDate,
    },
    statement: serialized.statement
      ? {
          ...serialized.statement,
          dueDate: deserializeDate(serialized.statement.dueDate),
          createdAt: deserializeDate(serialized.statement.createdAt),
        }
      : null,
    payment: serialized.payment
      ? {
          ...serialized.payment,
          transactionDate: transactionDate!,
        }
      : null,
    notes: serialized.notes,
  }
}

// ============================================================================
// ID Generation
// ============================================================================

const generateEntryId = (): string => {
  const timestamp = Date.now()

  // Use crypto.getRandomValues for secure random generation
  const randomArray = new Uint32Array(1)
  crypto.getRandomValues(randomArray)
  const random = randomArray[0].toString(STORE_CONFIG.ID.RANDOM_BASE)
    .substring(0, STORE_CONFIG.ID.RANDOM_LENGTH)
    .padEnd(STORE_CONFIG.ID.RANDOM_LENGTH, '0')

  return `${STORE_CONFIG.ID.PREFIX}${timestamp}-${random}`
}

// ============================================================================
// Store Implementation
// ============================================================================

export const useHistoryStore = create<HistoryStore>()(
  persist(
    (set, get) => ({
      history: [],

      addEntry: (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => {
        const newEntry: HistoryEntry = {
          ...entry,
          id: generateEntryId(),
          timestamp: new Date(),
        }

        set((state) => ({
          history: [newEntry, ...state.history].slice(0, STORE_CONFIG.STORAGE.MAX_ENTRIES),
        }))
      },

      updateEntry: (id: string, updates: Partial<Omit<HistoryEntry, 'id' | 'timestamp'>>) => {
        set((state) => ({
          history: state.history.map((entry) =>
            entry.id === id ? { ...entry, ...updates } : entry
          ),
        }))
      },

      deleteEntry: (id: string) => {
        set((state) => ({
          history: state.history.filter((entry) => entry.id !== id),
        }))
      },

      clearHistory: () => {
        set({ history: [] })
      },

      getEntry: (id: string) => {
        return get().history.find((entry) => entry.id === id)
      },
    }),
    {
      name: STORE_CONFIG.STORAGE.NAME,

      // Custom serialization to handle Date objects
      partialize: (state: HistoryStore): PersistedState => ({
        history: state.history.map(serializeHistoryEntry),
      }),

      // Custom deserialization to convert strings back to Date objects
      merge: (persistedState: unknown, currentState: HistoryStore): HistoryStore => {
        if (!isPersistedState(persistedState)) {
          return currentState
        }

        try {
          return {
            ...currentState,
            history: persistedState.history.map(deserializeHistoryEntry),
          }
        } catch (error) {
          console.error('Failed to deserialize history store:', error)
          return currentState
        }
      },
    }
  )
)

// ============================================================================
// Type Guard
// ============================================================================

function isPersistedState(value: unknown): value is PersistedState {
  if (!value || typeof value !== 'object') return false
  const obj = value as Record<string, unknown>

  if (!Array.isArray(obj.history)) return false

  // Validate each entry has required fields
  return obj.history.every((entry) => {
    if (!entry || typeof entry !== 'object') return false
    const e = entry as Record<string, unknown>

    // Validate date strings can be parsed
    const timestamp = typeof e.timestamp === 'string' ? new Date(e.timestamp) : null
    if (!timestamp || Number.isNaN(timestamp.getTime())) return false

    return (
      typeof e.id === 'string' &&
      typeof e.timestamp === 'string' &&
      e.input !== undefined &&
      typeof e.input === 'object'
    )
  })
}
