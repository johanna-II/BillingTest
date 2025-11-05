import { Hono } from 'hono'
import { cors } from 'hono/cors'

// ============================================================================
// Type Definitions - 타입 안전성 향상
// ============================================================================

interface UsageItem {
  // Required fields for type safety
  counterVolume: number
  counterName: string
  counterUnit: string
  // Optional fields
  counterType?: string
  resourceId?: string
  resourceName?: string
  projectId?: string
  appKey?: string
  uuid?: string
}

interface CreditItem {
  // Required fields for type safety
  amount: number
  type: string  // PROMOTIONAL, FREE, PAID
  // Optional fields
  campaignId?: string
  name?: string
  creditCode?: string
  uuid?: string
  expireDate?: string
  restAmount?: number
}

interface AdjustmentItem {
  // Required fields for type safety
  type: 'DISCOUNT' | 'SURCHARGE'
  method: 'FIXED' | 'RATE'
  value: number
  // Optional fields
  description?: string
  level?: string
  targetProjectId?: string
  month?: string
}

// Legacy adjustment format for backward compatibility
interface LegacyAdjustmentItem {
  adjustmentType: string
  method: 'FIXED' | 'RATE'
  adjustmentValue: number
  description?: string
  level?: string
  targetProjectId?: string
  month?: string
}

// Union type to accept either modern or legacy format
type AdjustmentItemInput = AdjustmentItem | LegacyAdjustmentItem

interface BillingRequest {
  uuid?: string
  billingGroupId?: string
  targetDate?: string
  unpaidAmount?: number
  isOverdue?: boolean
  usage?: UsageItem[]
  credits?: CreditItem[]
  adjustments?: AdjustmentItemInput[]
}

interface PaymentRequest {
  paymentGroupId?: string
  amount?: number
}

// ============================================================================
// Environment bindings
// ============================================================================

interface Env {
  VAT_RATE?: string  // Configurable VAT rate (default: 0.1 for 10%)
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_VAT_RATE = 0.1

const app = new Hono<{ Bindings: Env }>()

// CORS 설정 - 모든 도메인 허용 또는 특정 도메인만
app.use('/*', cors({
  origin: (origin) => {
    // 로컬 개발 또는 Cloudflare Pages/Workers 도메인 허용
    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:5173',
      'https://billingtest.pages.dev',
      /^https:\/\/.*\.pages\.dev$/,  // 모든 .pages.dev 서브도메인
      /^https:\/\/.*\.workers\.dev$/  // 모든 .workers.dev 서브도메인
    ]

    if (!origin) return '*' // non-browser requests

    // 정규식 또는 문자열 매칭
    const isAllowed = allowedOrigins.some(allowed => {
      if (typeof allowed === 'string') return allowed === origin
      return allowed.test(origin)
    })

    return isAllowed ? origin : 'https://billingtest.pages.dev'
  },
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'uuid', 'Authorization'],
  exposeHeaders: ['Content-Length', 'X-Request-Id'],
  credentials: true,
  maxAge: 86400, // 24시간 캐시
}))

// Health check
app.get('/health', (c) => {
  return c.json({
    header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
    status: 'healthy',
    timestamp: new Date().toISOString()
  })
})

// Calculate billing endpoint
app.post('/api/billing/admin/calculate', async (c) => {
  try {
    const uuid = c.req.header('uuid')

    // Get configurable VAT rate from environment or use default
    const vatRate = c.env.VAT_RATE ? Number.parseFloat(c.env.VAT_RATE) : DEFAULT_VAT_RATE

    // Parse request body - don't hide JSON errors
    let body: BillingRequest
    try {
      body = await c.req.json<BillingRequest>()
    } catch (err) {
      console.error('Failed to parse billing request JSON:', err)
      return c.json({
        header: {
          isSuccessful: false,
          resultCode: -1,
          resultMessage: `Invalid JSON request body: ${err instanceof Error ? err.message : 'Unknown error'}`
        }
      }, 400)
    }

    const { usage = [], credits = [], adjustments = [] } = body

    // Normalize adjustments (convert legacy format and validate)
    let normalizedAdjustments: AdjustmentItem[]
    try {
      normalizedAdjustments = adjustments.map(normalizeAdjustmentItem)
    } catch (err) {
      console.error('Invalid adjustment item:', err)
      return c.json({
        header: {
          isSuccessful: false,
          resultCode: -1,
          resultMessage: err instanceof Error ? err.message : 'Invalid adjustment data'
        }
      }, 400)
    }

    // 사용량 계산
    const subtotal = usage.reduce((sum: number, item: UsageItem) => {
      const amount = calculateAmount(item.counterName, item.counterVolume)
      return sum + amount
    }, 0)

    // 조정 적용
    const adjustmentTotal = calculateAdjustmentTotal(normalizedAdjustments, subtotal)

    // 크레딧 적용 전 금액
    const chargeBeforeCredit = Math.max(0, subtotal + adjustmentTotal)

    // 크레딧 순차 적용 (PROMOTIONAL → FREE → PAID 우선순위)
    let remainingCharge = chargeBeforeCredit
    const appliedCreditsList: Array<{
      creditId: string
      type: string
      amountApplied: number
      remainingBalance: number
      campaignId?: string
      campaignName?: string
    }> = []

    for (let idx = 0; idx < credits.length; idx++) {
      const credit = credits[idx]
      const amountApplied = Math.min(credit.amount, remainingCharge)

      remainingCharge -= amountApplied

      appliedCreditsList.push({
        creditId: credit.creditCode || credit.uuid || `credit-${idx}`,
        type: credit.type,
        amountApplied,
        remainingBalance: credit.amount - amountApplied,
        campaignId: credit.campaignId,
        campaignName: credit.name
      })

      // No more charge to apply credits to
      if (remainingCharge <= 0) break
    }

    // 최종 금액 계산
    const charge = remainingCharge
    const totalCreditsApplied = chargeBeforeCredit - charge
    const vat = Math.floor(charge * vatRate)
    const totalAmount = charge + vat

  return c.json({
    header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
    statementId: `stmt-${Date.now()}`,
    uuid: uuid || body.uuid,
    billingGroupId: body.billingGroupId,
    month: body.targetDate?.slice(0, 7) || new Date().toISOString().slice(0, 7),
    currency: 'KRW',
    subtotal,
    billingGroupDiscount: 0,
    adjustmentTotal,
    creditApplied: totalCreditsApplied,
    vat,
    unpaidAmount: body.unpaidAmount || 0,
    lateFee: body.isOverdue ? (body.unpaidAmount || 0) * 0.05 : 0,
    charge,
    amount: totalAmount,
    totalAmount,
    status: 'PENDING',
    lineItems: usage.map((item: UsageItem, idx: number) => ({
        id: `line-${idx}`,
        counterName: item.counterName,
        counterType: item.counterType || 'DELTA',
        unit: item.counterUnit,
        quantity: item.counterVolume,
        unitPrice: getUnitPrice(item.counterName),
        amount: calculateAmount(item.counterName, item.counterVolume),
        resourceId: item.resourceId,
        resourceName: item.resourceName,
        projectId: item.projectId,
        appKey: item.appKey
      })),
    appliedCredits: appliedCreditsList,
    appliedAdjustments: normalizedAdjustments.map((adj: AdjustmentItem, idx: number) => ({
      adjustmentId: `adj-${idx}`,
      type: adj.type,
      description: adj.description,
      amount: calculateAdjustmentAmount(adj, subtotal),
      level: adj.level,
      targetId: adj.targetProjectId
    }))
  })
  } catch (error) {
    console.error('Calculate billing error:', error)
    return c.json({
      header: {
        isSuccessful: false,
        resultCode: -1,
        resultMessage: error instanceof Error ? error.message : 'Calculation failed'
      }
    }, 500)
  }
})

// Get payment statements
app.get('/api/billing/payments/:month/statements', async (c) => {
  try {
    const uuid = c.req.header('uuid')
    const month = c.req.param('month')

    // 간단한 mock 데이터
    return c.json({
      header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
      paymentGroupId: `PG-${uuid?.slice(0, 8) || 'default'}`,
      paymentStatus: 'READY',
      statements: [{
        statementId: `stmt-${month}`,
        uuid: uuid || 'default',
        month,
        currency: 'KRW',
        amount: 0,
        subtotal: 0,
        billingGroupDiscount: 0,
        adjustmentTotal: 0,
        creditApplied: 0,
        vat: 0,
        unpaidAmount: 0,
        lateFee: 0,
        totalAmount: 0,
        status: 'READY',
        lineItems: [],
        appliedCredits: [],
        appliedAdjustments: []
      }]
    })
  } catch (error) {
    console.error('Get statements error:', error)
    return c.json({
      header: {
        isSuccessful: false,
        resultCode: -1,
        resultMessage: error instanceof Error ? error.message : 'Failed to get statements'
      }
    }, 500)
  }
})

// Process payment
app.post('/api/billing/payments/:month', async (c) => {
  try {
    const uuid = c.req.header('uuid')

    // Parse request body - don't hide JSON errors
    let body: PaymentRequest
    try {
      body = await c.req.json<PaymentRequest>()
    } catch (err) {
      console.error('Failed to parse payment request JSON:', err)
      return c.json({
        header: {
          isSuccessful: false,
          resultCode: -1,
          resultMessage: `Invalid JSON request body: ${err instanceof Error ? err.message : 'Unknown error'}`
        }
      }, 400)
    }

    return c.json({
      header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
      paymentId: `PAY-${Date.now()}`,
      paymentGroupId: body.paymentGroupId || `PG-${uuid?.slice(0, 8) || 'default'}`,
      status: 'SUCCESS',
      amount: body.amount || 0,
      method: 'MOCK',
      transactionDate: new Date().toISOString(),
      receiptUrl: `https://receipt.example.com/${Date.now()}`
    })
  } catch (error) {
    console.error('Payment processing error:', error)
    return c.json({
      header: {
        isSuccessful: false,
        resultCode: -1,
        resultMessage: error instanceof Error ? error.message : 'Payment processing failed'
      }
    }, 500)
  }
})

// Helper: 단가 계산 (단위당 가격)
function getUnitPrice(counterName: string): number {
  const prices: Record<string, number> = {
    'compute.c2.c8m8': 397,          // 397원/시간
    'compute.g2.t4.c8m64': 166.67,   // 166.67원/시간
    'storage.volume.ssd': 100,        // 100원/GB/월
    'network.floating_ip': 25         // 25원/시간
  }
  return prices[counterName] || 100
}

// Helper: Validate adjustment type with assertion signature
function validateAdjustmentType(value: string): asserts value is 'DISCOUNT' | 'SURCHARGE' {
  if (value !== 'DISCOUNT' && value !== 'SURCHARGE') {
    throw new Error(
      `Invalid adjustment type: "${value}". Must be "DISCOUNT" or "SURCHARGE".`
    )
  }
}

// Helper: Validate adjustment method with assertion signature
function validateAdjustmentMethod(value: string): asserts value is 'FIXED' | 'RATE' {
  if (value !== 'FIXED' && value !== 'RATE') {
    throw new Error(
      `Invalid adjustment method: "${value}". Must be "FIXED" or "RATE".`
    )
  }
}

// Helper: Normalize adjustment item with runtime validation
function normalizeAdjustmentItem(item: AdjustmentItemInput): AdjustmentItem {
  // Check if this is a legacy format (has adjustmentType)
  if ('adjustmentType' in item) {
    // Validate adjustmentType using helper with assertion signature
    validateAdjustmentType(item.adjustmentType)

    // Validate method using helper with assertion signature
    validateAdjustmentMethod(item.method)

    // Validate adjustmentValue is present and a finite number
    if (item.adjustmentValue === undefined || item.adjustmentValue === null) {
      throw new Error(
        `Missing required field: adjustmentValue must be provided in legacy format.`
      )
    }

    if (typeof item.adjustmentValue !== 'number' || !Number.isFinite(item.adjustmentValue)) {
      throw new TypeError(
        `Invalid adjustmentValue: "${item.adjustmentValue}". Must be a finite number (not NaN or Infinity).`
      )
    }

    const normalized: AdjustmentItem = {
      type: item.adjustmentType,
      method: item.method,
      value: item.adjustmentValue,
    }

    // Copy optional fields
    if (item.description) normalized.description = item.description
    if (item.level) normalized.level = item.level
    if (item.targetProjectId) normalized.targetProjectId = item.targetProjectId
    if (item.month) normalized.month = item.month

    return normalized
  }

  // Already modern format - validate type and method fields
  validateAdjustmentType(item.type)
  validateAdjustmentMethod(item.method)

  // Validate value is present and a finite number
  if (item.value === undefined || item.value === null) {
    throw new Error(
      `Missing required field: value must be provided.`
    )
  }

  if (typeof item.value !== 'number' || !Number.isFinite(item.value)) {
    throw new TypeError(
      `Invalid value: "${item.value}". Must be a finite number (not NaN or Infinity).`
    )
  }

  return item
}

// Helper: 조정 금액 계산
function calculateAdjustmentAmount(adj: AdjustmentItem, subtotal: number): number {
  if (adj.method === 'FIXED') {
    return adj.value
  }
  // RATE
  return Math.floor(subtotal * (adj.value / 100))
}

// Helper: 조정 합계 계산
function calculateAdjustmentTotal(adjustments: AdjustmentItem[], subtotal: number): number {
  let total = 0

  for (const adj of adjustments) {
    const amount = calculateAdjustmentAmount(adj, subtotal)

    if (adj.type === 'DISCOUNT') {
      total -= amount
    } else {  // SURCHARGE
      total += amount
    }
  }

  return total
}

// Helper: 실제 금액 계산
function calculateAmount(counterName: string, volume: number): number {
  const unitPrice = getUnitPrice(counterName)

  // All volumes are in their standard units:
  // - Compute: hours
  // - Storage: GB (already converted)
  // - Network: hours
  return Math.floor(volume * unitPrice)
}

export default app
