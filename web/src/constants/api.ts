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
 * API Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 */
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:5000',
  ENDPOINTS: {
    CALCULATE: '/api/billing/admin/calculate',
    STATEMENTS: '/api/billing/payments',
    PAYMENT: '/api/billing/payments',
  },
  HEADERS: {
    CONTENT_TYPE: 'application/json',
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
