/**
 * History Store - Zustand State Management
 * Type-safe localStorage persistence with proper serialization
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  BillingInput,
  BillingStatement,
  PaymentResult,
  CreditInput,
  UsageInput,
  AdjustmentInput,
} from '@/types/billing'
import { generateCreditId, generateUsageId, generateAdjustmentId } from '@/lib/utils/id'

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

/**
 * Serialized CreditInput type
 * Converts expirationDate from Date to string
 */
interface SerializedCreditInput extends Omit<CreditInput, 'expirationDate'> {
  readonly expirationDate?: string
}

/**
 * Serialized BillingInput type
 * Converts targetDate and credits[].expirationDate from Date to string
 * Note: usage and adjustments may be undefined in old localStorage data
 */
interface SerializedBillingInput extends Omit<BillingInput, 'targetDate' | 'credits' | 'usage' | 'adjustments'> {
  readonly targetDate: string
  readonly credits: ReadonlyArray<SerializedCreditInput>
  readonly usage?: ReadonlyArray<Partial<UsageInput>>
  readonly adjustments?: ReadonlyArray<Partial<AdjustmentInput>>
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
  readonly addEntry: (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => string
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

// ============================================================================
// Migration Helpers
// ============================================================================

/**
 * Validate and migrate UsageInput with required fields
 * Returns null if validation fails (incomplete data)
 * @public - Exported for testing and verification
 */
export const migrateUsageInput = (usage: Partial<UsageInput>): UsageInput | null => {
  // Validate all required fields are present
  if (
    typeof usage.counterName !== 'string' ||
    typeof usage.counterType !== 'string' ||
    typeof usage.counterUnit !== 'string' ||
    typeof usage.counterVolume !== 'number' ||
    typeof usage.resourceId !== 'string' ||
    typeof usage.appKey !== 'string'
  ) {
    console.warn('Skipping invalid usage item - missing required fields:', usage)
    return null
  }

  // All required fields present - safely migrate with id
  return {
    id: usage.id || generateUsageId(),
    counterName: usage.counterName,
    counterType: usage.counterType,
    counterUnit: usage.counterUnit,
    counterVolume: usage.counterVolume,
    resourceId: usage.resourceId,
    appKey: usage.appKey,
    // Optional fields
    resourceName: usage.resourceName,
    projectId: usage.projectId,
  }
}

/**
 * Validate and migrate CreditInput with required fields
 * Returns null if validation fails (incomplete data)
 * @public - Exported for testing and verification
 */
export const migrateCreditInput = (credit: Partial<CreditInput>): CreditInput | null => {
  // Validate all required fields are present
  if (
    typeof credit.type !== 'string' ||
    typeof credit.amount !== 'number' ||
    typeof credit.name !== 'string'
  ) {
    console.warn('Skipping invalid credit item - missing required fields:', credit)
    return null
  }

  // All required fields present - safely migrate with id
  return {
    id: credit.id || generateCreditId(),
    type: credit.type,
    amount: credit.amount,
    name: credit.name,
    // Optional fields
    expirationDate: credit.expirationDate,
    campaignId: credit.campaignId,
  }
}

/**
 * Validate and migrate AdjustmentInput with required fields
 * Returns null if validation fails (incomplete data)
 * @public - Exported for testing and verification
 */
export const migrateAdjustmentInput = (adjustment: Partial<AdjustmentInput>): AdjustmentInput | null => {
  // Validate all required fields are present
  if (
    typeof adjustment.type !== 'string' ||
    typeof adjustment.level !== 'string' ||
    typeof adjustment.method !== 'string' ||
    typeof adjustment.value !== 'number' ||
    typeof adjustment.description !== 'string'
  ) {
    console.warn('Skipping invalid adjustment item - missing required fields:', adjustment)
    return null
  }

  // All required fields present - safely migrate with id
  return {
    id: adjustment.id || generateAdjustmentId(),
    type: adjustment.type,
    level: adjustment.level,
    method: adjustment.method,
    value: adjustment.value,
    description: adjustment.description,
    // Optional fields
    targetProjectId: adjustment.targetProjectId,
  }
}

const serializeHistoryEntry = (entry: HistoryEntry): SerializedHistoryEntry => {
  return {
    id: entry.id,
    timestamp: entry.timestamp.toISOString(),
    input: {
      ...entry.input,
      targetDate: entry.input.targetDate.toISOString(),
      // Explicitly serialize usage array (already has id fields)
      usage: entry.input.usage,
      // Serialize credits array, converting expirationDate to string
      credits: entry.input.credits.map(credit => ({
        ...credit,
        expirationDate: credit.expirationDate ? credit.expirationDate.toISOString() : undefined,
      })),
      // Explicitly serialize adjustments array (already has id fields)
      adjustments: entry.input.adjustments,
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
      // Use entry timestamp as fallback to preserve data with meaningful date
      // This is more useful than epoch (1970-01-01) for corrupted payment data
      console.warn(
        `Invalid transactionDate in history entry ${serialized.id}: ${serialized.payment.transactionDate}. ` +
        `Using entry timestamp as fallback.`
      )
      transactionDate = timestamp
    }
  }

  return {
    id: serialized.id,
    timestamp,
    input: {
      ...serialized.input,
      targetDate,
      // Migrate usage array: validate and filter out invalid items
      usage: (serialized.input.usage || [])
        .map(migrateUsageInput)
        .filter((item): item is UsageInput => item !== null),
      // Migrate credits array: validate, deserialize dates, and filter out invalid items
      credits: serialized.input.credits
        .map((credit) => {
          return migrateCreditInput({
            ...credit,
            expirationDate: credit.expirationDate ? deserializeDate(credit.expirationDate) : undefined,
          })
        })
        .filter((item): item is CreditInput => item !== null),
      // Migrate adjustments array: validate and filter out invalid items
      adjustments: (serialized.input.adjustments || [])
        .map(migrateAdjustmentInput)
        .filter((item): item is AdjustmentInput => item !== null),
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

        // Return the ID of the newly created entry
        return newEntry.id
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
