/**
 * Billing API Client
 * Type-safe HTTP client with comprehensive error handling
 */

import { ErrorCode } from '@/types/billing'
import type {
  BillingInput,
  BillingStatement,
  PaymentResult,
  ApiResponseHeader,
  CalculationError,
} from '@/types/billing'
import { API_CONFIG, getErrorCodeForStatus } from '@/constants/api'

// ============================================================================
// API Response Format Documentation
// ============================================================================
/**
 * API Endpoints Response Format:
 *
 * NEW FORMAT (recommended):
 * - /api/billing/admin/calculate → { header, data: BillingStatement }
 *
 * LEGACY FORMAT (⚠️ DEPRECATED - backwards compatible):
 * - /api/billing/payments/:month/statements → { header, ...BillingStatement }
 * - /api/billing/payments/:month → { header, ...PaymentResult }
 *
 * ⚠️ LEGACY FORMAT CONSTRAINT:
 * The response data type T must NOT contain a field named 'header'.
 * If it does, that field will be silently excluded during destructuring.
 * Current safe types: BillingStatement, PaymentResult (verified to have no 'header' field)
 *
 * The client handles both formats automatically via extractDataFromResponse()
 */

// ============================================================================
// Custom Error Classes
// ============================================================================

export class APIError extends Error {
  public readonly name = 'APIError' as const
  public readonly statusCode: number
  public readonly errorCode: ErrorCode

  constructor(message: string, statusCode: number, errorCode: ErrorCode = ErrorCode.API_ERROR) {
    super(message)
    this.statusCode = statusCode
    this.errorCode = errorCode
    Object.setPrototypeOf(this, APIError.prototype)
  }
}

export class NetworkError extends Error {
  public readonly name = 'NetworkError' as const
  public readonly errorCode: ErrorCode = ErrorCode.NETWORK_ERROR

  constructor(message: string, public readonly originalError?: unknown) {
    super(message)
    Object.setPrototypeOf(this, NetworkError.prototype)
  }
}

export class ValidationError extends Error {
  public readonly name = 'ValidationError' as const
  public readonly errorCode: ErrorCode = ErrorCode.VALIDATION_ERROR

  constructor(
    message: string,
    public readonly field?: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message)
    Object.setPrototypeOf(this, ValidationError.prototype)
  }
}

// ============================================================================
// Type Definitions
// ============================================================================

export interface PaymentRequest {
  readonly amount: number
  readonly paymentGroupId: string
}

/**
 * Payment statements envelope response
 * Wraps an array of billing statements with payment group metadata
 */
export interface PaymentStatementsEnvelope {
  readonly paymentGroupId: string
  readonly paymentStatus: string
  readonly statements: ReadonlyArray<BillingStatement>
}

/**
 * API Response format supporting both:
 * - New format: { header, data: T }
 * - Legacy format: { header, ...T } (backwards compatibility)
 */
interface ApiResponse<T> {
  readonly header: ApiResponseHeader
  readonly data?: T
}

/**
 * Legacy flat response format (backwards compatibility)
 * All fields from T are at the same level as header
 *
 * ⚠️ DEPRECATED: This format is maintained for backwards compatibility only.
 * New APIs should use the standard format: { header, data: T }
 *
 * ⚠️ CONSTRAINT: The generic type T must NOT contain a field named 'header'.
 * If T has a 'header' field, it will be excluded during destructuring and lost.
 *
 * Known safe types: BillingStatement, PaymentResult (verified to have no 'header' field)
 */
type LegacyApiResponse<T> = {
  readonly header: ApiResponseHeader
} & Partial<T>

// ============================================================================
// Runtime Validation Helpers
// ============================================================================

/**
 * Validates critical fields of a BillingStatement response
 * Lightweight validation without external libraries
 */
function validateBillingStatement(data: unknown): data is BillingStatement {
  if (!data || typeof data !== 'object') return false
  const statement = data as Partial<BillingStatement>

  return (
    typeof statement.statementId === 'string' &&
    typeof statement.month === 'string' &&
    typeof statement.totalAmount === 'number' &&
    Array.isArray(statement.lineItems)
  )
}

/**
 * Validates critical fields of a PaymentResult response
 * Note: transactionDate is validated separately for type conversion
 */
function validatePaymentResult(data: unknown): data is PaymentResult {
  if (!data || typeof data !== 'object') return false
  const result = data as Partial<PaymentResult>

  return (
    typeof result.paymentId === 'string' &&
    typeof result.status === 'string' &&
    typeof result.amount === 'number' &&
    typeof result.transactionDate === 'string' // transactionDate from backend
  )
}

// ============================================================================
// HTTP Client
// ============================================================================

class HTTPClient {
  private readonly baseUrl: string
  private readonly timeout: number

  constructor(baseUrl: string = API_CONFIG.BASE_URL, timeout: number = API_CONFIG.TIMEOUT.DEFAULT) {
    this.baseUrl = baseUrl
    this.timeout = timeout
  }

  private createAbortController(): { controller: AbortController; cleanup: () => void } {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)
    return {
      controller,
      cleanup: () => clearTimeout(timeoutId),
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorText: string
      try {
        errorText = await response.text()
      } catch (error) {
        errorText = `Unable to read error response: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
      throw new APIError(
        `HTTP ${response.status}: ${errorText}`,
        response.status,
        this.mapStatusToErrorCode(response.status)
      )
    }

    try {
      const data = await response.json()
      // Note: Type assertion here is necessary as JSON.parse returns 'any'
      // Actual runtime validation happens in extractDataFromResponse()
      // for critical response types (BillingStatement, PaymentResult)
      return data as T
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      throw new APIError(
        `Failed to parse response JSON: ${errorMessage}`,
        response.status,
        ErrorCode.API_ERROR
      )
    }
  }

  /**
   * Maps HTTP status codes to application error codes
   *
   * Uses helper function with safe fallback for unmapped codes
   *
   * @param status - HTTP response status code
   * @returns Corresponding application ErrorCode
   */
  private mapStatusToErrorCode(status: number): ErrorCode {
    return getErrorCodeForStatus(status)
  }

  async post<T>(
    endpoint: string,
    body: unknown,
    headers: Record<string, string> = {}
  ): Promise<T> {
    const { controller, cleanup } = this.createAbortController()
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          [API_CONFIG.HEADERS.CONTENT_TYPE]: 'application/json',
          ...headers,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof APIError) throw error
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout', error)
      }
      throw new NetworkError('Network request failed', error)
    } finally {
      cleanup()
    }
  }

  async get<T>(endpoint: string, headers: Record<string, string> = {}): Promise<T> {
    const { controller, cleanup } = this.createAbortController()
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers,
        signal: controller.signal,
      })

      return this.handleResponse<T>(response)
    } catch (error) {
      if (error instanceof APIError) throw error
      if (error instanceof Error && error.name === 'AbortError') {
        throw new NetworkError('Request timeout', error)
      }
      throw new NetworkError('Network request failed', error)
    } finally {
      cleanup()
    }
  }
}

// ============================================================================
// Billing API Client
// ============================================================================

export class BillingAPIClient {
  private readonly httpClient: HTTPClient

  constructor(baseUrl?: string) {
    this.httpClient = new HTTPClient(baseUrl)
  }

  async calculateBilling(request: BillingInput): Promise<BillingStatement> {
    this.validateBillingInput(request)

    const response = await this.httpClient.post<ApiResponse<BillingStatement>>(
      API_CONFIG.ENDPOINTS.CALCULATE,
      request,
      { [API_CONFIG.HEADERS.UUID_HEADER]: request.uuid }
    )

    return this.extractStatementFromResponse(response)
  }

  /**
   * Get payment statement for a specific month
   * Extracts the first statement from the envelope response
   *
   * @param uuid - User UUID
   * @param month - Billing month (e.g., '2024-11')
   * @returns Single billing statement
   */
  async getPaymentStatement(uuid: string, month: string): Promise<BillingStatement> {
    if (!uuid || !month) {
      throw new ValidationError('UUID and month are required', 'uuid,month')
    }

    const endpoint = `${API_CONFIG.ENDPOINTS.STATEMENTS}/${month}/statements`
    const response = await this.httpClient.get<ApiResponse<PaymentStatementsEnvelope>>(endpoint, {
      [API_CONFIG.HEADERS.UUID_HEADER]: uuid,
    })

    const envelope = this.extractDataFromResponse(response)

    // Validate envelope has statements array
    if (!envelope.statements || !Array.isArray(envelope.statements)) {
      throw new APIError(
        'Invalid API response: missing or invalid statements array',
        500,
        ErrorCode.API_ERROR
      )
    }

    // Validate statements array is not empty
    if (envelope.statements.length === 0) {
      throw new APIError(
        'Invalid API response: statements array is empty',
        500,
        ErrorCode.API_ERROR
      )
    }

    // Extract the first statement from the envelope
    const statement = envelope.statements[0]

    // Runtime validation for critical response type
    if (!validateBillingStatement(statement)) {
      throw new APIError(
        'Invalid BillingStatement in envelope: missing required fields',
        500,
        ErrorCode.API_ERROR
      )
    }

    return statement
  }

  async processPayment(
    uuid: string,
    month: string,
    request: PaymentRequest
  ): Promise<PaymentResult> {
    this.validatePaymentRequest(request)

    const endpoint = `${API_CONFIG.ENDPOINTS.PAYMENT}/${month}`
    const response = await this.httpClient.post<ApiResponse<PaymentResult>>(
      endpoint,
      request,
      { [API_CONFIG.HEADERS.UUID_HEADER]: uuid }
    )

    const data = this.extractDataFromResponse(response)

    // Runtime validation for critical response type
    if (!validatePaymentResult(data)) {
      throw new APIError(
        'Invalid PaymentResult response: missing required fields',
        500,
        ErrorCode.API_ERROR
      )
    }

    // Validate transactionDate is not empty
    if (!data.transactionDate) {
      throw new APIError(
        'Invalid PaymentResult response: transactionDate cannot be empty',
        500,
        ErrorCode.API_ERROR
      )
    }

    // Convert and validate transactionDate from string to Date object
    const transactionDate = new Date(data.transactionDate)
    if (Number.isNaN(transactionDate.getTime())) {
      throw new APIError(
        `Invalid PaymentResult response: transactionDate "${data.transactionDate}" is not a valid date`,
        500,
        ErrorCode.API_ERROR
      )
    }

    // Return with properly converted Date object
    return {
      ...data,
      transactionDate,
    }
  }

  // ============================================================================
  // Private Helper Methods
  // ============================================================================

  private validateBillingInput(input: BillingInput): void {
    if (!input.uuid) {
      throw new ValidationError('UUID is required', 'uuid')
    }
    if (!input.billingGroupId) {
      throw new ValidationError('Billing group ID is required', 'billingGroupId')
    }
  }

  private validatePaymentRequest(request: PaymentRequest): void {
    if (typeof request.amount !== 'number' || !Number.isFinite(request.amount) || request.amount < 0) {
      throw new ValidationError('Valid amount is required', 'amount')
    }
    if (!request.paymentGroupId) {
      throw new ValidationError('Payment group ID is required', 'paymentGroupId')
    }
  }

  private extractStatementFromResponse(
    response: ApiResponse<BillingStatement>
  ): BillingStatement {
    const baseStatement = this.extractDataFromResponse(response)

    // Runtime validation for critical response type
    if (!validateBillingStatement(baseStatement)) {
      throw new APIError(
        'Invalid BillingStatement response: missing required fields',
        500,
        ErrorCode.API_ERROR
      )
    }

    // Backend already calculates unpaidAmount, lateFee, and totalAmount
    // Return the statement as-is without recalculation to avoid double-counting
    return baseStatement
  }

  private extractDataFromResponse<T>(response: ApiResponse<T>): T {
    // Validate response has header
    if (!response.header || typeof response.header !== 'object') {
      throw new APIError(
        'Invalid API response: missing or invalid header',
        500,
        ErrorCode.API_ERROR
      )
    }

    // New format: { header, data: T }
    if ('data' in response && response.data !== undefined) {
      if (typeof response.data !== 'object' || response.data === null) {
        throw new APIError(
          'Invalid API response: data field must be an object',
          500,
          ErrorCode.API_ERROR
        )
      }
      return response.data
    }

    // Legacy format: { header, ...T } - for backwards compatibility
    // Extract all non-header fields as the data
    const originalResponse = response as unknown as Record<string, unknown>
    const { header, ...data } = response as LegacyApiResponse<T>

    // Runtime check: Warn about potential type collision in development
    if (process.env.NODE_ENV === 'development') {
      const responseKeys = Object.keys(originalResponse)
      const dataKeys = Object.keys(data)

      // Warn only if we have non-header keys in response but extracted nothing
      // This suggests a 'header' field collision (not just an empty response)
      const hasNonHeaderKeys = responseKeys.some(key => key !== 'header')
      if (hasNonHeaderKeys && dataKeys.length === 0) {
        console.warn(
          '[API Warning] Legacy response format extracted no data fields despite non-header keys present. ' +
          'If the response type T has a "header" field, it was excluded during destructuring. ' +
          'Consider migrating this endpoint to use the new format: { header, data: T }'
        )
      }
    }

    // Validate we have some data beyond just the header
    if (Object.keys(data).length === 0) {
      throw new APIError(
        'Invalid API response: no data found in response',
        500,
        ErrorCode.API_ERROR
      )
    }

    return data as T
  }
}

// ============================================================================
// Singleton Instance & Convenience Functions
// ============================================================================

export const billingAPI = new BillingAPIClient()

export const calculateBilling = async (request: BillingInput): Promise<BillingStatement> => {
  return billingAPI.calculateBilling(request)
}

/**
 * Get payment statement for a specific month
 * @param uuid - User UUID
 * @param month - Billing month (e.g., '2024-11')
 * @returns Single billing statement (first from envelope)
 */
export const getPaymentStatement = async (uuid: string, month: string): Promise<BillingStatement> => {
  return billingAPI.getPaymentStatement(uuid, month)
}

export const processPayment = async (
  uuid: string,
  month: string,
  request: PaymentRequest
): Promise<PaymentResult> => {
  return billingAPI.processPayment(uuid, month, request)
}

// ============================================================================
// Error Helper Functions
// ============================================================================

export const createCalculationError = (error: unknown): CalculationError => {
  if (error instanceof ValidationError) {
    return {
      code: error.errorCode,
      message: error.message,
      field: error.field,
      details: error.details,
    }
  }

  if (error instanceof APIError) {
    return {
      code: error.errorCode,
      message: error.message,
      details: { statusCode: error.statusCode },
    }
  }

  if (error instanceof NetworkError) {
    return {
      code: error.errorCode,
      message: error.message,
    }
  }

  if (error instanceof Error) {
    return {
      code: ErrorCode.UNKNOWN_ERROR,
      message: error.message,
    }
  }

  return {
    code: ErrorCode.UNKNOWN_ERROR,
    message: 'An unknown error occurred',
  }
}
