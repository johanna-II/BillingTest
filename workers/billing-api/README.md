# Cloudflare Workers - Billing API

TypeScript-based serverless billing API running on Cloudflare's edge network.

## 🎯 Purpose

Standalone billing calculation API for portfolio demonstration.

**Note:** This is an **independent implementation**, separate from the Python test suite in `/libs`. It does NOT communicate with the Python backend.

## 🏗️ Architecture

- **Runtime**: Cloudflare Workers (V8 Isolates)
- **Framework**: [Hono](https://hono.dev/) - Fast, lightweight web framework
- **Language**: TypeScript 5.3
- **Deployment**: Cloudflare's global edge network

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or later
- npm or pnpm
- Cloudflare account (for deployment)

### Development

```bash
# Install dependencies
npm install

# Start local development server
npm run dev
# → http://localhost:8787

# Deploy to Cloudflare (requires login)
npm run deploy

# View logs
npm run tail
```

## 📁 Project Structure

```text
workers/billing-api/
├── src/
│   └── index.ts          # Main API implementation
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── wrangler.toml         # Cloudflare config
└── README.md             # This file
```

## 🔌 API Endpoints

### POST /api/billing/admin/calculate

Calculate billing statement with usage, credits, and adjustments.

**Request:**

```json
{
  "uuid": "user-123",
  "billingGroupId": "bg-456",
  "targetDate": "2024-11-06",
  "usage": [...],
  "credits": [...],
  "adjustments": [...]
}
```

**Response:**

```json
{
  "header": {
    "isSuccessful": true,
    "resultCode": 0,
    "resultMessage": "SUCCESS"
  },
  "data": {
    "statementId": "stmt-...",
    "totalAmount": 162500,
    "charge": 100000,
    "vat": 10000,
    ...
  }
}
```

### GET /api/billing/payments/:month/statements

Get billing statements for a specific month.

### POST /api/billing/payments/:month

Process payment for a billing statement.

## 🎨 Design Decisions

### Simplified Enums (YAGNI Principle)

This API intentionally uses a **simplified subset** of billing features:

| Enum | Values | Rationale |
|------|--------|-----------|
| **CreditType** | FREE, PAID, PROMOTIONAL | Core use cases only |
| **PaymentStatus** | SUCCESS, FAILED, PENDING | Essential states |
| **AdjustmentType** | DISCOUNT, SURCHARGE + method/level | Compositional design |

**Why simplified?**

- Easier to understand and maintain
- Covers 95% of real-world scenarios
- Demonstrates clean architecture principles
- Portfolio-friendly (not over-engineered)

### Compositional Adjustment Design

Instead of flat enums (`FIXED_DISCOUNT`, `RATE_DISCOUNT`), we use composition:

```typescript
interface AdjustmentInput {
  type: 'DISCOUNT' | 'SURCHARGE'
  method: 'FIXED' | 'RATE'
  level: 'BILLING_GROUP' | 'PROJECT'
  value: number
}
```

**Benefits:**

- More flexible (easy to add new methods/levels)
- Better type safety
- Clearer business logic
- Follows modern TypeScript patterns

## 🔗 Integration

**Frontend:** `/web` (Next.js app) calls this API  
**Python Backend:** Not connected - independent systems

## 📦 Dependencies

```json
{
  "hono": "^4.0.0",
  "chanfana": "^2.0.2"
}
```

## 🚢 Deployment

### Cloudflare Workers

```bash
# First time: Login to Cloudflare
npx wrangler login

# Deploy to production
npm run deploy

# Deploy to specific environment
npm run deploy -- --env production
```

### Environment Variables

Configure in `wrangler.toml`:

```toml
[vars]
ENVIRONMENT = "production"
```

For secrets (API keys, etc.):

```bash
npx wrangler secret put SECRET_NAME
```

## 🧪 Testing

Currently relies on manual testing and end-to-end tests from `/web`.

**Future:** Add unit tests with Vitest

## 📝 Code Style

- **Formatter**: Prettier (inherited from workspace)
- **Linter**: ESLint (TypeScript recommended rules)
- **Type checking**: `tsc --noEmit`

## 🔄 Comparison with Python Stack

| Feature | Python Stack | This (TypeScript) |
|---------|-------------|-------------------|
| Purpose | API testing | Production demo |
| CreditTypes | 7 types | 3 types |
| PaymentStatus | 9 statuses | 3 statuses |
| Adjustments | Flat enums | Compositional |
| Complexity | Comprehensive | Minimal |

Both are intentional design choices for different goals.

## 🤝 Contributing

1. Make changes in `src/index.ts`
2. Test locally: `npm run dev`
3. Check types: `npm run check` (if script exists)
4. Deploy: `npm run deploy`

## 📚 Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Hono Documentation](https://hono.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 📄 License

MIT
