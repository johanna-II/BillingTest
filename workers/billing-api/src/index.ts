import { Hono } from 'hono'
import { cors } from 'hono/cors'

const app = new Hono()

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
    const body = await c.req.json().catch(() => ({}))

    // 간단한 빌링 계산 로직
    const { usage = [], credits = [], adjustments = [] } = body

  // 사용량 계산
  const subtotal = usage.reduce((sum: number, item: any) => {
    const quantity = item.counterVolume || 0
    const counterName = item.counterName || ''
    const counterUnit = item.counterUnit || 'HOURS'
    const amount = calculateAmount(counterName, quantity, counterUnit)
    return sum + amount
  }, 0)

  // 크레딧 적용
  const totalCredits = credits.reduce((sum: number, c: any) => sum + (c.amount || 0), 0)
  const creditApplied = Math.min(totalCredits, subtotal)

  // 조정 적용
  let adjustmentTotal = 0
  for (const adj of adjustments) {
    if (adj.type === 'DISCOUNT') {
      adjustmentTotal -= adj.method === 'FIXED' ? adj.value : subtotal * (adj.value / 100)
    } else {
      adjustmentTotal += adj.method === 'FIXED' ? adj.value : subtotal * (adj.value / 100)
    }
  }

  const charge = Math.max(0, subtotal + adjustmentTotal - creditApplied)
  const VAT_RATE = 0.1
  const vat = Math.floor(charge * VAT_RATE)
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
    creditApplied,
    vat,
    unpaidAmount: body.unpaidAmount || 0,
    lateFee: body.isOverdue ? (body.unpaidAmount || 0) * 0.05 : 0,
    charge,
    amount: totalAmount,
    totalAmount,
    status: 'PENDING',
    lineItems: usage.map((item: any, idx: number) => {
      const counterName = item.counterName || ''
      const quantity = item.counterVolume || 0
      const counterUnit = item.counterUnit || 'HOURS'
      const unitPrice = getUnitPrice(counterName)
      const amount = calculateAmount(counterName, quantity, counterUnit)

      return {
        id: `line-${idx}`,
        counterName,
        counterType: item.counterType || 'DELTA',
        unit: counterUnit,
        quantity,
        unitPrice,
        amount,
        resourceId: item.resourceId,
        resourceName: item.resourceName,
        projectId: item.projectId,
        appKey: item.appKey
      }
    }),
    appliedCredits: credits.map((c: any, idx: number) => ({
      creditId: `credit-${idx}`,
      type: c.type,
      amountApplied: Math.min(c.amount, charge),
      remainingBalance: Math.max(0, c.amount - charge),
      campaignId: c.campaignId,
      campaignName: c.name
    })),
    appliedAdjustments: adjustments.map((adj: any, idx: number) => ({
      adjustmentId: `adj-${idx}`,
      type: adj.type,
      description: adj.description,
      amount: adj.method === 'FIXED' ? adj.value : subtotal * (adj.value / 100),
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
    const body = await c.req.json().catch(() => ({}))

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

// Helper: 실제 금액 계산 (단위 변환 포함)
function calculateAmount(counterName: string, volume: number, unit: string = 'HOURS'): number {
  const unitPrice = getUnitPrice(counterName)

  // Storage는 counterVolume이 이미 GB 단위로 제공됨
  // 다른 counter들은 해당 단위(HOURS 등) 그대로 사용
  return Math.floor(volume * unitPrice)
}

export default app
