/**
 * Billing domain types
 */

export interface BillingInput {
  /** Test target date */
  targetDate: Date
  /** UUID for the billing entity */
  uuid: string
  /** Billing group ID */
  billingGroupId: string
  /** Instance usage data */
  usage: UsageInput[]
  /** Credits to apply */
  credits: CreditInput[]
  /** Adjustments (discounts/surcharges) */
  adjustments: AdjustmentInput[]
  /** Unpaid amount from previous period */
  unpaidAmount?: number
  /** Whether there's overdue payment */
  isOverdue?: boolean
}

export interface UsageInput {
  /** Unique ID for this usage entry */
  id: string
  /** Counter name (e.g., compute.c2.c8m8) */
  counterName: string
  /** Counter type */
  counterType: 'DELTA' | 'GAUGE' | 'CUMULATIVE'
  /** Counter unit */
  counterUnit: string
  /** Usage volume */
  counterVolume: number
  /** Resource ID */
  resourceId: string
  /** Resource name */
  resourceName?: string
  /** App key */
  appKey: string
  /** Project ID */
  projectId?: string
}

export interface CreditInput {
  /** Credit type */
  type: 'FREE' | 'PAID' | 'PROMOTIONAL'
  /** Credit amount */
  amount: number
  /** Credit name/description */
  name: string
  /** Expiration date */
  expirationDate?: Date
  /** Campaign ID if applicable */
  campaignId?: string
}

export interface AdjustmentInput {
  /** Adjustment type */
  type: 'DISCOUNT' | 'SURCHARGE'
  /** Application level */
  level: 'BILLING_GROUP' | 'PROJECT'
  /** Adjustment method */
  method: 'FIXED' | 'RATE'
  /** Adjustment value */
  value: number
  /** Description */
  description: string
  /** Target project ID if project-level */
  targetProjectId?: string
}

export interface BillingStatement {
  /** Statement ID */
  statementId: string
  /** UUID */
  uuid: string
  /** Billing group ID */
  billingGroupId: string
  /** Statement month */
  month: string
  /** Total amount before adjustments */
  subtotal: number
  /** Total adjustments */
  adjustmentTotal: number
  /** Total credits applied */
  creditApplied: number
  /** Unpaid amount from previous period */
  unpaidAmount: number
  /** Late fee if applicable */
  lateFee: number
  /** Final amount to pay */
  totalAmount: number
  /** Statement status */
  status: 'PENDING' | 'PAID' | 'OVERDUE' | 'CANCELLED'
  /** Detailed line items */
  lineItems: LineItem[]
  /** Applied credits breakdown */
  appliedCredits: AppliedCredit[]
  /** Applied adjustments breakdown */
  appliedAdjustments: AppliedAdjustment[]
  /** Due date */
  dueDate: Date
  /** Creation timestamp */
  createdAt: Date
}

export interface LineItem {
  /** Line item ID */
  id: string
  /** Counter name */
  counterName: string
  /** Counter type */
  counterType: string
  /** Unit */
  unit: string
  /** Quantity */
  quantity: number
  /** Unit price */
  unitPrice: number
  /** Line total */
  amount: number
  /** Resource details */
  resourceId: string
  resourceName?: string
  /** Project info */
  projectId?: string
  appKey: string
}

export interface AppliedCredit {
  /** Credit ID */
  creditId: string
  /** Credit type */
  type: 'FREE' | 'PAID' | 'PROMOTIONAL'
  /** Amount applied */
  amountApplied: number
  /** Remaining balance */
  remainingBalance: number
  /** Campaign info */
  campaignId?: string
  campaignName?: string
}

export interface AppliedAdjustment {
  /** Adjustment ID */
  adjustmentId: string
  /** Type */
  type: 'DISCOUNT' | 'SURCHARGE'
  /** Description */
  description: string
  /** Amount */
  amount: number
  /** Application level */
  level: 'BILLING_GROUP' | 'PROJECT'
  /** Target */
  targetId?: string
}

export interface PaymentResult {
  /** Payment ID */
  paymentId: string
  /** Status */
  status: 'SUCCESS' | 'FAILED' | 'PENDING'
  /** Amount charged */
  amount: number
  /** Payment method */
  method: string
  /** Transaction timestamp */
  transactionDate: Date
  /** Error message if failed */
  errorMessage?: string
  /** Receipt URL */
  receiptUrl?: string
}

export interface CalculationError {
  /** Error code */
  code: string
  /** Error message */
  message: string
  /** Field that caused the error */
  field?: string
  /** Additional details */
  details?: Record<string, unknown>
}

