/**
 * API Configuration Constants
 * Centralized API-related constants and mappings
 */

import { ErrorCode } from '@/types/billing'

// ============================================================================
// HTTP Status Codes
// ============================================================================

/**
 * HTTP Status Codes
 * Standard HTTP response status codes for error categorization
 */
export const HttpStatus = {
  // 2xx Success
  OK: 200,
  CREATED: 201,

  // 4xx Client Errors
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,

  // 5xx Server Errors
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const

// ============================================================================
// Status to Error Code Mapping
// ============================================================================

/**
 * HTTP Status to Error Code mapping type
 * Explicitly typed to prevent unsafe assumptions about unmapped status codes
 */
type StatusToErrorMap = {
  readonly [HttpStatus.BAD_REQUEST]: ErrorCode.VALIDATION_ERROR
  readonly [HttpStatus.UNPROCESSABLE_ENTITY]: ErrorCode.VALIDATION_ERROR
  readonly [HttpStatus.UNAUTHORIZED]: ErrorCode.AUTH_ERROR
  readonly [HttpStatus.FORBIDDEN]: ErrorCode.AUTH_ERROR
  readonly [HttpStatus.NOT_FOUND]: ErrorCode.API_ERROR
  readonly [HttpStatus.TOO_MANY_REQUESTS]: ErrorCode.API_ERROR
}

const STATUS_TO_ERROR_MAP: StatusToErrorMap = {
  [HttpStatus.BAD_REQUEST]: ErrorCode.VALIDATION_ERROR,
  [HttpStatus.UNPROCESSABLE_ENTITY]: ErrorCode.VALIDATION_ERROR,
  [HttpStatus.UNAUTHORIZED]: ErrorCode.AUTH_ERROR,
  [HttpStatus.FORBIDDEN]: ErrorCode.AUTH_ERROR,
  [HttpStatus.NOT_FOUND]: ErrorCode.API_ERROR,
  [HttpStatus.TOO_MANY_REQUESTS]: ErrorCode.API_ERROR,
}

/**
 * Get error code for HTTP status with safe fallback
 *
 * Uses explicit mapping for known status codes, with range-based
 * fallback for unmapped codes
 *
 * @param status - HTTP status code
 * @returns Appropriate ErrorCode, never undefined
 */
export function getErrorCodeForStatus(status: number): ErrorCode {
  // Check explicit mapping first using 'in' operator for robust property checking
  if (status in STATUS_TO_ERROR_MAP) {
    return STATUS_TO_ERROR_MAP[status as keyof StatusToErrorMap]
  }

  // Fallback for HTTP error ranges (4xx and 5xx)
  if (status >= 400 && status < 600) {
    return ErrorCode.API_ERROR
  }

  // Unknown or unexpected status code
  return ErrorCode.UNKNOWN_ERROR
}

// ============================================================================
// API Configuration
// ============================================================================

/**
 * API Configuration Shape
 * Validates structure while allowing literal type inference
 */
type APIConfigShape = {
  readonly BASE_URL: string
  readonly ENDPOINTS: {
    readonly [key: string]: string
  }
  readonly HEADERS: {
    readonly [key: string]: string
  }
  readonly LATE_FEE: {
    readonly RATE: number
  }
  readonly TIMEOUT: {
    readonly DEFAULT: number
  }
}

/**
 * Get API Base URL with environment-aware fallback
 * - Production: Requires NEXT_PUBLIC_API_URL to be set (fails fast if missing)
 * - Development: Falls back to localhost:5000 for local testing
 */
const getApiBaseUrl = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL

  // Production: Require environment variable
  if (process.env.NODE_ENV === 'production') {
    if (!envUrl) {
      const errorMessage =
        'NEXT_PUBLIC_API_URL environment variable is required in production. ' +
        'Please configure it in your deployment settings (GitHub Secrets, Vercel, etc.)'

      // Log to console for easier debugging
      console.error('❌ Configuration Error:', errorMessage)

      throw new Error(errorMessage)
    }
    return envUrl
  }

  // Development: Use env var or fallback to localhost
  if (!envUrl) {
    console.warn(
      '⚠️ NEXT_PUBLIC_API_URL not set. Using fallback: http://localhost:5000\n' +
      'For Cloudflare Workers, create web/.env.local with:\n' +
      'NEXT_PUBLIC_API_URL=https://billing-api.janetheglory.workers.dev'
    )
    return 'http://localhost:5000'
  }

  return envUrl
}

/**
 * API Base URL - Computed lazily to avoid build-time errors
 * Use API_CONFIG.BASE_URL to access
 */
let cachedBaseUrl: string | undefined

const getBaseUrl = (): string => {
  if (cachedBaseUrl) return cachedBaseUrl
  cachedBaseUrl = getApiBaseUrl()
  return cachedBaseUrl
}

/**
 * API Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 *
 * Note: BASE_URL is a getter to defer environment check until runtime
 */
export const API_CONFIG = {
  get BASE_URL(): string {
    return getBaseUrl()
  },
  ENDPOINTS: {
    CALCULATE: '/api/billing/admin/calculate',
    STATEMENTS: '/api/billing/payments',
    PAYMENT: '/api/billing/payments',
  },
  HEADERS: {
    CONTENT_TYPE: 'Content-Type',
    UUID_HEADER: 'uuid',
  },
  LATE_FEE: {
    RATE: 0.05,
  },
  TIMEOUT: {
    DEFAULT: 30000,
  },
} as const satisfies APIConfigShape

/**
 * Derive type from constant for perfect type safety
 */
export type APIConfigType = typeof API_CONFIG
