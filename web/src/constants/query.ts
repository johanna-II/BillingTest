/**
 * React Query Configuration Constants
 * Centralized configuration for all React Query hooks
 */

// ============================================================================
// Configuration Shapes
// ============================================================================

type BillingQueryConfigShape = {
  readonly RETRY: {
    readonly MAX_RETRIES: number
    readonly INITIAL_DELAY_MS: number
    readonly MAX_DELAY_MS: number
    readonly BACKOFF_MULTIPLIER: number
  }
  readonly CACHE_KEY: {
    readonly PREFIX: string
  }
}

type PaymentQueryConfigShape = {
  readonly RETRY: {
    readonly MAX_RETRIES: number // Standardized naming (was MAX_ATTEMPTS)
  }
  readonly CACHE_KEY: {
    readonly PREFIX: string
  }
}

type QueryClientConfigShape = {
  readonly QUERIES: {
    readonly STALE_TIME_MS: number
    readonly REFETCH_ON_WINDOW_FOCUS: boolean
    readonly RETRY_ATTEMPTS: number
    readonly RETRY_DELAY_MS: number
  }
  readonly MUTATIONS: {
    readonly RETRY_ATTEMPTS: number
  }
  readonly CACHE: {
    readonly GC_TIME_MS: number
  }
}

// ============================================================================
// Billing Calculation Query Config
// ============================================================================

/**
 * Billing Query Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 */
export const BILLING_QUERY_CONFIG = {
  RETRY: {
    MAX_RETRIES: 2,
    INITIAL_DELAY_MS: 1000,
    MAX_DELAY_MS: 30000,
    BACKOFF_MULTIPLIER: 2,
  },
  CACHE_KEY: {
    PREFIX: 'billing',
  },
} as const satisfies BillingQueryConfigShape

export type BillingQueryConfigType = typeof BILLING_QUERY_CONFIG

// ============================================================================
// Payment Processing Query Config
// ============================================================================

/**
 * Payment Query Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 *
 * Note: MAX_RETRIES standardized across all query configs for consistency
 */
export const PAYMENT_QUERY_CONFIG = {
  RETRY: {
    MAX_RETRIES: 0, // Payments should not be retried automatically
  },
  CACHE_KEY: {
    PREFIX: 'payment',
  },
} as const satisfies PaymentQueryConfigShape

export type PaymentQueryConfigType = typeof PAYMENT_QUERY_CONFIG

// ============================================================================
// Global Query Client Config
// ============================================================================

/**
 * Query Client Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 */
export const QUERY_CLIENT_CONFIG = {
  QUERIES: {
    STALE_TIME_MS: 60 * 1000, // 1 minute
    REFETCH_ON_WINDOW_FOCUS: false,
    RETRY_ATTEMPTS: 1,
    RETRY_DELAY_MS: 1000,
  },
  MUTATIONS: {
    RETRY_ATTEMPTS: 0,
  },
  CACHE: {
    GC_TIME_MS: 5 * 60 * 1000, // 5 minutes
  },
} as const satisfies QueryClientConfigShape

export type QueryClientConfigType = typeof QUERY_CLIENT_CONFIG

// ============================================================================
// Query Key Factories
// ============================================================================

/**
 * Centralized query key patterns for cache invalidation
 * Ensures consistency across hooks and prevents key mismatches
 */
export const BILLING_QUERY_KEYS = {
  byStatement: (id: string) => ['billing', id] as const,
  statements: (id: string) => ['billing', 'statements', id] as const,
  groups: (id: string) => ['billing', 'groups', id] as const,
} as const
