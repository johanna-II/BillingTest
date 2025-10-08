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
  const uuid = c.req.header('uuid')
  const body = await c.req.json()

  // 간단한 빌링 계산 로직
  const { usage = [], credits = [], adjustments = [] } = body

  // 사용량 계산
  const subtotal = usage.reduce((sum: number, item: any) => {
    const quantity = item.counterVolume || 0
    const unitPrice = getUnitPrice(item.counterName)
    return sum + (quantity * unitPrice)
  }, 0)

  // 크레딧 적용
  const totalCredits = credits.reduce((sum: number, c: any) => sum + (c.amount || 0), 0)
  const creditApplied = Math.min(totalCredits, subtotal)

  // 조정 적용
  let adjustmentTotal = 0
  adjustments.forEach((adj: any) => {
    if (adj.type === 'DISCOUNT') {
      adjustmentTotal -= adj.method === 'FIXED' ? adj.value : subtotal * (adj.value / 100)
    } else {
      adjustmentTotal += adj.method === 'FIXED' ? adj.value : subtotal * (adj.value / 100)
    }
  })

  const charge = Math.max(0, subtotal + adjustmentTotal - creditApplied)
  const vat = Math.floor(charge * 0.1)
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
    lineItems: usage.map((item: any, idx: number) => ({
      id: `line-${idx}`,
      counterName: item.counterName,
      counterType: item.counterType || 'DELTA',
      unit: item.counterUnit || 'HOURS',
      quantity: item.counterVolume,
      unitPrice: getUnitPrice(item.counterName),
      amount: item.counterVolume * getUnitPrice(item.counterName),
      resourceId: item.resourceId,
      resourceName: item.resourceName,
      projectId: item.projectId,
      appKey: item.appKey
    })),
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
})

// Get payment statements
app.get('/api/billing/payments/:month/statements', async (c) => {
  const uuid = c.req.header('uuid')
  const month = c.param('month')

  // 간단한 mock 데이터
  return c.json({
    header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
    paymentGroupId: `PG-${uuid?.slice(0, 8)}`,
    paymentStatus: 'READY',
    statements: [{
      statementId: `stmt-${month}`,
      uuid,
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
})

// Process payment
app.post('/api/billing/payments/:month', async (c) => {
  const uuid = c.req.header('uuid')
  const month = c.param('month')
  const body = await c.req.json()

  return c.json({
    header: { isSuccessful: true, resultCode: 0, resultMessage: 'SUCCESS' },
    paymentId: `PAY-${Date.now()}`,
    paymentGroupId: body.paymentGroupId,
    status: 'SUCCESS',
    amount: body.amount,
    method: 'MOCK',
    transactionDate: new Date().toISOString(),
    receiptUrl: `https://receipt.example.com/${Date.now()}`
  })
})

// Helper: 단가 계산
function getUnitPrice(counterName: string): number {
  const prices: Record<string, number> = {
    'compute.c2.c8m8': 397,
    'compute.g2.t4.c8m64': 166.67,
    'storage.volume.ssd': 100,
    'network.floating_ip': 25
  }
  return prices[counterName] || 100
}

export default app

