import { Hono, Context } from 'hono'
import { cors } from 'hono/cors'

// ============================================================================
// Type Definitions & Enums
// ============================================================================

enum CreditType {
  PROMOTIONAL = 'PROMOTIONAL',
  FREE = 'FREE',
  PAID = 'PAID',
}

enum AdjustmentType {
  DISCOUNT = 'DISCOUNT',
  SURCHARGE = 'SURCHARGE',
}

enum AdjustmentMethod {
  FIXED = 'FIXED',
  RATE = 'RATE',
}

enum BillingStatus {
  PENDING = 'PENDING',
  PAID = 'PAID',
  OVERDUE = 'OVERDUE',
  CANCELLED = 'CANCELLED',
}

enum PaymentStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  PENDING = 'PENDING',
}

enum PaymentMethod {
  CREDIT_CARD = 'CREDIT_CARD',
  BANK_TRANSFER = 'BANK_TRANSFER',
  DEBIT_CARD = 'DEBIT_CARD',
  WIRE_TRANSFER = 'WIRE_TRANSFER',
  MOCK = 'MOCK',
}

enum CounterType {
  DELTA = 'DELTA',
  GAUGE = 'GAUGE',
  CUMULATIVE = 'CUMULATIVE',
}

enum Currency {
  KRW = 'KRW',
  USD = 'USD',
  EUR = 'EUR',
  JPY = 'JPY',
}

// ============================================================================
// Domain Types - Fully Type Safe
// ============================================================================

interface UsageItem {
  readonly counterVolume: number
  readonly counterName: string
  readonly counterUnit: string
  readonly counterType?: CounterType
  readonly resourceId?: string
  readonly resourceName?: string
  readonly projectId?: string
  readonly appKey?: string
  readonly uuid?: string
}

interface CreditItem {
  readonly amount: number
  readonly type: CreditType
  readonly campaignId?: string
  readonly name?: string
  readonly creditCode?: string
  readonly uuid?: string
  readonly expireDate?: string
  readonly restAmount?: number
}

interface AdjustmentItem {
  readonly type: AdjustmentType
  readonly method: AdjustmentMethod
  readonly value: number
  readonly description?: string
  readonly level?: string
  readonly targetProjectId?: string
  readonly month?: string
}

interface LegacyAdjustmentItem {
  readonly adjustmentType: string
  readonly method: string
  readonly adjustmentValue: number
  readonly description?: string
  readonly level?: string
  readonly targetProjectId?: string
  readonly month?: string
}

type AdjustmentItemInput = AdjustmentItem | LegacyAdjustmentItem

interface BillingRequest {
  readonly uuid?: string
  readonly billingGroupId?: string
  readonly targetDate?: string
  readonly unpaidAmount?: number
  readonly isOverdue?: boolean
  readonly usage?: ReadonlyArray<UsageItem>
  readonly credits?: ReadonlyArray<CreditItem>
  readonly adjustments?: ReadonlyArray<AdjustmentItemInput>
}

interface PaymentRequest {
  readonly paymentGroupId?: string
  readonly amount?: number
}

interface Env {
  readonly VAT_RATE?: string
}

// ============================================================================
// Response Types - Fully Type Safe
// ============================================================================

interface ApiResponseHeader {
  readonly isSuccessful: boolean
  readonly resultCode: number
  readonly resultMessage: string
}

interface SuccessResponse<T> {
  readonly header: ApiResponseHeader
  readonly data: T
}

interface ErrorResponse {
  readonly header: ApiResponseHeader
}

interface LineItem {
  readonly id: string
  readonly counterName: string
  readonly counterType: CounterType
  readonly unit: string
  readonly quantity: number
  readonly unitPrice: number
  readonly amount: number
  readonly resourceId?: string
  readonly resourceName?: string
  readonly projectId?: string
  readonly appKey?: string
}

interface AppliedCredit {
  readonly creditId: string
  readonly type: CreditType
  readonly amountApplied: number
  readonly remainingBalance: number
  readonly campaignId?: string
  readonly campaignName?: string
}

interface AppliedAdjustment {
  readonly adjustmentId: string
  readonly type: AdjustmentType
  readonly description?: string
  readonly amount: number
  readonly level?: string
  readonly targetId?: string
}

interface BillingCalculationResult {
  readonly statementId: string
  readonly uuid?: string
  readonly billingGroupId?: string
  readonly month: string
  readonly currency: Currency
  readonly subtotal: number
  readonly billingGroupDiscount: number
  readonly adjustmentTotal: number
  readonly creditApplied: number
  readonly vat: number
  readonly unpaidAmount: number
  readonly lateFee: number
  readonly charge: number
  readonly amount: number
  readonly totalAmount: number
  readonly status: BillingStatus
  readonly lineItems: ReadonlyArray<LineItem>
  readonly appliedCredits: ReadonlyArray<AppliedCredit>
  readonly appliedAdjustments: ReadonlyArray<AppliedAdjustment>
}

interface CreditApplicationResult {
  readonly charge: number
  readonly appliedCredits: ReadonlyArray<AppliedCredit>
  readonly totalCreditsApplied: number
}

// ============================================================================
// Custom Error Classes
// ============================================================================

class ValidationError extends Error {
  public readonly name = 'ValidationError' as const

  constructor(message: string) {
    super(message)
    Object.setPrototypeOf(this, ValidationError.prototype)
  }
}

// ============================================================================
// Configuration & Constants - Type Safe
// ============================================================================

type PricingKey =
  | 'compute.c2.c8m8'
  | 'compute.g2.t4.c8m64'
  | 'storage.volume.ssd'
  | 'network.floating_ip'

const PRICING_TABLE: Record<PricingKey, number> = {
  'compute.c2.c8m8': 397,
  'compute.g2.t4.c8m64': 166.67,
  'storage.volume.ssd': 100,
  'network.floating_ip': 25,
} as const

const CONFIG = {
  VAT: {
    DEFAULT_RATE: 0.1,
  },
  LATE_FEE: {
    RATE: 0.05,
  },
  PRICING: PRICING_TABLE,
  DEFAULT_PRICE: 100,
  CORS: {
    ALLOWED_ORIGINS: [
      'http://localhost:3000',
      'http://localhost:5173',
      'https://billingtest.pages.dev',
    ] as const,
    ALLOWED_PATTERNS: [
      /^https:\/\/.*\.pages\.dev$/,
      /^https:\/\/.*\.workers\.dev$/,
    ] as const,
    DEFAULT_ORIGIN: 'https://billingtest.pages.dev' as const,
    MAX_AGE: 86400,
  },
  CURRENCY: {
    DEFAULT: Currency.KRW,
  },
  COUNTER: {
    DEFAULT_TYPE: CounterType.DELTA,
  },
  BILLING: {
    DEFAULT_DISCOUNT: 0,
  },
  ID_PREFIX: {
    STATEMENT: 'stmt-',
    PAYMENT: 'PAY-',
    PAYMENT_GROUP: 'PG-',
    LINE_ITEM: 'line-',
    ADJUSTMENT: 'adj-',
    CREDIT: 'credit-',
  },
  UUID: {
    SLICE_LENGTH: 8,
  },
} as const

// ============================================================================
// Utility Functions - Type Guards & Validators
// ============================================================================

const isValidEnum = <T extends Record<string, string>>(
  enumObj: T,
  value: unknown
): value is T[keyof T] => {
  return typeof value === 'string' && Object.values(enumObj).includes(value)
}

const assertValidEnum = <T extends Record<string, string>>(
  enumObj: T,
  value: unknown,
  fieldName: string
): asserts value is T[keyof T] => {
  if (!isValidEnum(enumObj, value)) {
    const validValues = Object.values(enumObj).join(', ')
    throw new ValidationError(
      `Invalid ${fieldName}: "${String(value)}". Must be one of: ${validValues}.`
    )
  }
}

const assertPositiveNumber = (
  value: unknown,
  fieldName: string
): asserts value is number => {
  if (value === undefined || value === null) {
    throw new ValidationError(`Missing required field: ${fieldName} must be provided.`)
  }

  if (typeof value !== 'number' || !Number.isFinite(value)) {
    const valueStr = formatValue(value)
    throw new ValidationError(
      `Invalid ${fieldName}: ${valueStr}. Must be a finite number (not NaN or Infinity).`
    )
  }

  if (value <= 0) {
    throw new ValidationError(
      `Invalid ${fieldName}: ${value}. Must be a positive number greater than 0.`
    )
  }
}

const formatValue = (value: unknown): string => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'

  // Handle primitive types that stringify well
  if (typeof value === 'string') return value
  if (typeof value === 'number') return String(value)
  if (typeof value === 'boolean') return String(value)
  if (typeof value === 'bigint') return `${value}n`

  // Handle objects and arrays with JSON.stringify
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return '[object Object]'
    }
  }

  // Handle functions and symbols
  if (typeof value === 'function') return '[function]'
  if (typeof value === 'symbol') return value.toString()

  // Fallback for any other types
  return String(value)
}

// ============================================================================
// Response Helpers - Type Safe
// ============================================================================

const createSuccessResponse = <T extends Record<string, unknown>>(
  data: T
): { readonly header: ApiResponseHeader } & T => ({
  header: {
    isSuccessful: true,
    resultCode: 0,
    resultMessage: 'SUCCESS',
  } as const,
  ...data,
})

const createErrorResponse = (message: string): ErrorResponse => ({
  header: {
    isSuccessful: false,
    resultCode: -1,
    resultMessage: message,
  },
})

// ============================================================================
// Business Logic - Service Classes (Stateless & Pure)
// ============================================================================

class PricingService {
  private constructor() {}

  static getUnitPrice(counterName: string): number {
    const price = CONFIG.PRICING[counterName as PricingKey]
    return price ?? CONFIG.DEFAULT_PRICE
  }

  static calculateAmount(counterName: string, volume: number): number {
    const unitPrice = PricingService.getUnitPrice(counterName)
    return Math.floor(volume * unitPrice)
  }

  static calculateSubtotal(usageItems: ReadonlyArray<UsageItem>): number {
    return usageItems.reduce(
      (sum, item) => sum + PricingService.calculateAmount(item.counterName, item.counterVolume),
      0
    )
  }
}

class AdjustmentService {
  private constructor() {}

  static normalize(item: AdjustmentItemInput): AdjustmentItem {
    if ('adjustmentType' in item) {
      return AdjustmentService.normalizeLegacyFormat(item)
    }
    return AdjustmentService.validateModernFormat(item)
  }

  private static normalizeLegacyFormat(item: LegacyAdjustmentItem): AdjustmentItem {
    assertValidEnum(AdjustmentType, item.adjustmentType, 'adjustmentType')
    assertValidEnum(AdjustmentMethod, item.method, 'method')
    assertPositiveNumber(item.adjustmentValue, 'adjustmentValue')

    return {
      type: item.adjustmentType,
      method: item.method,
      value: item.adjustmentValue,
      description: item.description,
      level: item.level,
      targetProjectId: item.targetProjectId,
      month: item.month,
    }
  }

  private static validateModernFormat(item: AdjustmentItem): AdjustmentItem {
    assertValidEnum(AdjustmentType, item.type, 'type')
    assertValidEnum(AdjustmentMethod, item.method, 'method')
    assertPositiveNumber(item.value, 'value')
    return item
  }

  static calculateAmount(adjustment: AdjustmentItem, subtotal: number): number {
    if (adjustment.method === AdjustmentMethod.FIXED) {
      return adjustment.value
    }
    return Math.floor(subtotal * (adjustment.value / 100))
  }

  static calculateTotal(
    adjustments: ReadonlyArray<AdjustmentItem>,
    subtotal: number
  ): number {
    return adjustments.reduce((total, adj) => {
      const amount = AdjustmentService.calculateAmount(adj, subtotal)
      return adj.type === AdjustmentType.DISCOUNT ? total - amount : total + amount
    }, 0)
  }
}

class CreditService {
  private constructor() {}

  static applyCredits(
    credits: ReadonlyArray<CreditItem>,
    chargeBeforeCredit: number
  ): CreditApplicationResult {
    const appliedCredits: AppliedCredit[] = []
    let remainingCharge = chargeBeforeCredit

    for (let idx = 0; idx < credits.length; idx++) {
      if (remainingCharge <= 0) break

      const credit = credits[idx]
      const amountApplied = Math.min(credit.amount, remainingCharge)

      appliedCredits.push({
        creditId: credit.creditCode ?? credit.uuid ?? `${CONFIG.ID_PREFIX.CREDIT}${idx}`,
        type: credit.type,
        amountApplied,
        remainingBalance: credit.amount - amountApplied,
        campaignId: credit.campaignId,
        campaignName: credit.name,
      })

      remainingCharge -= amountApplied
    }

    return {
      charge: remainingCharge,
      appliedCredits,
      totalCreditsApplied: chargeBeforeCredit - remainingCharge,
    }
  }
}

class BillingCalculator {
  constructor(private readonly vatRate: number) {}

  calculate(request: BillingRequest, uuid?: string): BillingCalculationResult {
    const usage = request.usage ?? []
    const credits = request.credits ?? []
    const adjustments = request.adjustments ?? []

    const normalizedAdjustments = adjustments.map(AdjustmentService.normalize)
    const subtotal = PricingService.calculateSubtotal(usage)
    const adjustmentTotal = AdjustmentService.calculateTotal(normalizedAdjustments, subtotal)
    const chargeBeforeCredit = Math.max(0, subtotal + adjustmentTotal)
    const creditResult = CreditService.applyCredits(credits, chargeBeforeCredit)

    const charge = creditResult.charge
    const vat = Math.floor(charge * this.vatRate)
    const unpaidAmount = request.unpaidAmount ?? 0
    const lateFee = request.isOverdue === true && unpaidAmount > 0
      ? Math.floor(unpaidAmount * CONFIG.LATE_FEE.RATE)
      : 0
    const totalAmount = charge + vat + unpaidAmount + lateFee

    return {
      statementId: `${CONFIG.ID_PREFIX.STATEMENT}${Date.now()}`,
      uuid: uuid ?? request.uuid,
      billingGroupId: request.billingGroupId,
      month: this.extractMonth(request.targetDate),
      currency: CONFIG.CURRENCY.DEFAULT,
      subtotal,
      billingGroupDiscount: CONFIG.BILLING.DEFAULT_DISCOUNT,
      adjustmentTotal,
      creditApplied: creditResult.totalCreditsApplied,
      vat,
      unpaidAmount,
      lateFee,
      charge,
      amount: totalAmount,
      totalAmount,
      status: BillingStatus.PENDING,
      lineItems: this.buildLineItems(usage),
      appliedCredits: creditResult.appliedCredits,
      appliedAdjustments: this.buildAdjustmentItems(normalizedAdjustments, subtotal),
    }
  }

  private extractMonth(targetDate?: string): string {
    const date = targetDate ? new Date(targetDate) : new Date()

    // Validate date
    if (Number.isNaN(date.getTime())) {
      throw new ValidationError(`Invalid date format: "${targetDate}"`)
    }

    // Use UTC methods to avoid timezone-related month boundary errors
    // Example: "2024-02-01" in PST (UTC-8) would become 2024-01-31 16:00 local time
    // Using UTC ensures we always get February, not January
    const year = date.getUTCFullYear()
    const month = String(date.getUTCMonth() + 1).padStart(2, '0')

    return `${year}-${month}`
  }

  private buildLineItems(usage: ReadonlyArray<UsageItem>): ReadonlyArray<LineItem> {
    return usage.map((item, idx) => ({
      id: `${CONFIG.ID_PREFIX.LINE_ITEM}${idx}`,
      counterName: item.counterName,
      counterType: item.counterType ?? CONFIG.COUNTER.DEFAULT_TYPE,
      unit: item.counterUnit,
      quantity: item.counterVolume,
      unitPrice: PricingService.getUnitPrice(item.counterName),
      amount: PricingService.calculateAmount(item.counterName, item.counterVolume),
      resourceId: item.resourceId,
      resourceName: item.resourceName,
      projectId: item.projectId,
      appKey: item.appKey,
    }))
  }

  private buildAdjustmentItems(
    adjustments: ReadonlyArray<AdjustmentItem>,
    subtotal: number
  ): ReadonlyArray<AppliedAdjustment> {
    return adjustments.map((adj, idx) => ({
      adjustmentId: `${CONFIG.ID_PREFIX.ADJUSTMENT}${idx}`,
      type: adj.type,
      description: adj.description,
      amount: AdjustmentService.calculateAmount(adj, subtotal),
      level: adj.level,
      targetId: adj.targetProjectId,
    }))
  }
}

// ============================================================================
// Middleware & CORS Configuration
// ============================================================================

const configureCors = () => {
  const isOriginAllowed = (origin: string): boolean => {
    return (
      (CONFIG.CORS.ALLOWED_ORIGINS as readonly string[]).includes(origin) ||
      CONFIG.CORS.ALLOWED_PATTERNS.some((pattern) => pattern.test(origin))
    )
  }

  return cors({
    origin: (origin) => {
      if (!origin) return '*'
      return isOriginAllowed(origin) ? origin : CONFIG.CORS.DEFAULT_ORIGIN
    },
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'uuid', 'Authorization'],
    exposeHeaders: ['Content-Length', 'X-Request-Id'],
    credentials: true,
    maxAge: CONFIG.CORS.MAX_AGE,
  })
}

// ============================================================================
// Request Handlers - Type Safe
// ============================================================================

const parseJsonBody = async <T>(c: Context): Promise<T> => {
  try {
    return await c.req.json<T>()
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error'
    throw new ValidationError(`Invalid JSON request body: ${errorMessage}`)
  }
}

const getVatRate = (env: Env): number => {
  if (!env.VAT_RATE) {
    return CONFIG.VAT.DEFAULT_RATE
  }
  const rate = Number.parseFloat(env.VAT_RATE)
  return Number.isFinite(rate) && rate >= 0 ? rate : CONFIG.VAT.DEFAULT_RATE
}

const extractUuidPrefix = (uuid: string): string => {
  return uuid.slice(0, CONFIG.UUID.SLICE_LENGTH)
}

// ============================================================================
// Application Setup
// ============================================================================

const app = new Hono<{ Bindings: Env }>()

app.use('/*', configureCors())

// ============================================================================
// Route Handlers
// ============================================================================

app.get('/health', (c) => {
  return c.json(
    createSuccessResponse({
      status: 'healthy',
      timestamp: new Date().toISOString(),
    })
  )
})

app.post('/api/billing/admin/calculate', async (c) => {
  try {
    const uuid = c.req.header('uuid')
    const vatRate = getVatRate(c.env)
    const body = await parseJsonBody<BillingRequest>(c)

    const calculator = new BillingCalculator(vatRate)
    const result = calculator.calculate(body, uuid)

    return c.json(createSuccessResponse(result))
  } catch (error) {
    const statusCode = error instanceof ValidationError ? 400 : 500
    const message = error instanceof Error ? error.message : 'Billing calculation failed'
    return c.json(createErrorResponse(message), statusCode)
  }
})

app.get('/api/billing/payments/:month/statements', async (c) => {
  try {
    const uuid = c.req.header('uuid') ?? 'default'
    const month = c.req.param('month')

    const response = createSuccessResponse({
      paymentGroupId: `${CONFIG.ID_PREFIX.PAYMENT_GROUP}${extractUuidPrefix(uuid)}`,
      paymentStatus: PaymentStatus.PENDING,
      statements: [
        {
          statementId: `${CONFIG.ID_PREFIX.STATEMENT}${month}`,
          uuid,
          month,
          currency: CONFIG.CURRENCY.DEFAULT,
          amount: 0,
          subtotal: 0,
          billingGroupDiscount: 0,
          adjustmentTotal: 0,
          creditApplied: 0,
          vat: 0,
          unpaidAmount: 0,
          lateFee: 0,
          totalAmount: 0,
          status: BillingStatus.PENDING,
          lineItems: [],
          appliedCredits: [],
          appliedAdjustments: [],
        },
      ],
    })

    return c.json(response)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to retrieve statements'
    return c.json(createErrorResponse(message), 500)
  }
})

app.post('/api/billing/payments/:month', async (c) => {
  try {
    const uuid = c.req.header('uuid') ?? 'default'
    const body = await parseJsonBody<PaymentRequest>(c)

    const response = createSuccessResponse({
      paymentId: `${CONFIG.ID_PREFIX.PAYMENT}${Date.now()}`,
      paymentGroupId: body.paymentGroupId ?? `${CONFIG.ID_PREFIX.PAYMENT_GROUP}${extractUuidPrefix(uuid)}`,
      status: PaymentStatus.SUCCESS,
      amount: body.amount ?? 0,
      method: PaymentMethod.MOCK,
      transactionDate: new Date().toISOString(),
      receiptUrl: `https://receipt.example.com/${Date.now()}`,
    })

    return c.json(response)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Payment processing failed'
    return c.json(createErrorResponse(message), 500)
  }
})

export default app
