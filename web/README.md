# Billing Calculator - Web Application

Interactive billing calculator built with Next.js 14 and TypeScript.

## 🎯 Purpose

Full-stack billing calculator demo for portfolio showcase.

**Note:** This is a **standalone application** using Cloudflare Workers backend (`/workers/billing-api`). It does NOT connect to the Python backend in `/libs`.

## 🏗️ Architecture

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **State**: Zustand (lightweight state management)
- **Animation**: Framer Motion
- **API Client**: Custom fetch wrapper with type safety

## 🚀 Quick Start

### Prerequisites

- Node.js 20.x or later
- npm, yarn, or pnpm

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
# → http://localhost:3000

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

## 📁 Project Structure

```text
web/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx            # Home page
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles
│   │
│   ├── components/             # React components
│   │   ├── BillingInputForm.tsx
│   │   ├── StatementDisplay.tsx
│   │   ├── PaymentSection.tsx
│   │   └── sections/           # Form sections
│   │
│   ├── lib/                    # Utilities & API
│   │   ├── api/
│   │   │   └── billing-api.ts  # Type-safe API client
│   │   ├── pdf/
│   │   │   └── statementPDF.ts # PDF generation
│   │   └── queryClient.ts      # React Query config
│   │
│   ├── types/                  # TypeScript types
│   │   └── billing.ts          # Billing domain types
│   │
│   ├── stores/                 # Zustand stores
│   │   └── historyStore.ts     # Calculation history
│   │
│   ├── contexts/               # React contexts
│   │   └── BillingContext.tsx  # Billing state
│   │
│   └── hooks/                  # Custom hooks
│       ├── useBillingCalculation.ts
│       └── usePaymentProcessing.ts
│
├── public/                     # Static assets
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── tailwind.config.ts          # Tailwind config
├── next.config.js              # Next.js config
└── README.md                   # This file
```

## ✨ Features

### Billing Calculation

- **Usage Input**: Multiple resource types (compute, storage, network)
- **Credit Application**: FREE, PAID, PROMOTIONAL (sequential priority)
- **Adjustments**: Discounts and surcharges (fixed or percentage)
- **VAT Calculation**: Automatic 10% VAT
- **Late Fees**: 5% on unpaid balances

### Payment Processing

- **Mock Payments**: Test payment flow
- **Status Tracking**: SUCCESS, FAILED, PENDING
- **Unpaid Balances**: Carry-forward to next period

### History Management

- **LocalStorage Persistence**: Calculation history
- **Type-safe Serialization**: Date objects handled properly
- **Restore Previous**: Load and reuse past calculations

### PDF Export

- **Statement Generation**: Professional PDF invoices
- **i18n Support**: Multi-currency, multi-locale formatting
- **Detailed Breakdown**: Line items, adjustments, credits

## 🎨 UI/UX

### Design System

- **Colors**: Kinfolk-inspired earth tones
- **Typography**: Inter (body), Playfair Display (headings)
- **Layout**: Responsive, mobile-first
- **Interactions**: Smooth animations with Framer Motion

### Components

- **BillingInputForm**: Multi-step form with validation
- **StatementDisplay**: Breakdown of charges
- **PaymentSection**: Payment processing UI
- **HistoryPanel**: Past calculations sidebar

## 🔌 API Integration

### Backend Connection

Uses Cloudflare Workers API (`/workers/billing-api`):

```typescript
// src/lib/api/billing-api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8787'

// Type-safe API client
const statement = await calculateBilling({
  uuid: 'user-123',
  billingGroupId: 'bg-456',
  targetDate: new Date(),
  usage: [...],
  credits: [...],
  adjustments: [...]
})
```

### Response Format

```typescript
interface ApiResponse<T> {
  header: {
    isSuccessful: boolean
    resultCode: number
    resultMessage: string
  }
  data: T
}
```

Legacy format (`{ header, ...T }`) also supported for backwards compatibility.

## 🎯 Design Decisions

### Simplified Billing Model

Like the Workers API, this app uses a **simplified subset** of billing features:

**Why?**

- Easier to understand and use
- Covers most real-world scenarios
- Portfolio-friendly demonstration
- Clean, maintainable codebase

### State Management Strategy

**Global State (Zustand):**

- `historyStore`: Calculation history with localStorage

**Component State (React Context):**

- `BillingContext`: Current calculation state

**Server State (React Query):**

- API call caching and synchronization

### Type Safety

**100% TypeScript coverage:**

- All API responses validated at runtime
- Domain types shared with backend
- No `any` types allowed

## 🧪 Testing

Currently relies on manual testing.

**Future Plans:**

- **Unit Tests**: Vitest + React Testing Library
- **E2E Tests**: Playwright
- **Visual Tests**: Storybook + Chromatic

## 🎨 Code Style

```bash
# Format code
npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

**Standards:**

- Prettier for formatting
- ESLint (Next.js + TypeScript recommended)
- Strict TypeScript mode

## 📦 Dependencies

### Core

- `next`: 14.x - React framework
- `react`: 18.x - UI library
- `typescript`: 5.3.x - Type safety

### State & Data

- `zustand`: Lightweight state management
- `@tanstack/react-query`: Server state
- `jspdf`: PDF generation

### Styling

- `tailwindcss`: Utility-first CSS
- `framer-motion`: Animations

### Utilities

- `date-fns`: Date manipulation
- `zod`: Runtime validation (future)

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=https://billing-api.your-domain.workers.dev
```

### Build Optimization

```bash
# Analyze bundle size
npm run build

# Production build
npm run build && npm start
```

## 🔄 Comparison with Python Stack

| Aspect | Python Stack | This App |
|--------|-------------|----------|
| **Purpose** | API testing | User interface |
| **Backend** | External APIs | Cloudflare Workers |
| **Features** | Comprehensive | Simplified |
| **Users** | Developers | End users |

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Make changes
3. Test locally: `npm run dev`
4. Type check: `npm run type-check`
5. Lint: `npm run lint`
6. Submit PR

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zustand](https://docs.pmnd.rs/zustand/)

## 🐛 Known Issues

None currently. Report issues to the repository.

## 📄 License

MIT
