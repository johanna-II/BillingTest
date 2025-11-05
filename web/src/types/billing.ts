/**
 * Billing Domain Types
 * Fully type-safe with enums, readonly modifiers, and branded types
 */

// ============================================================================
// Enums - Type Safety
// ============================================================================

export enum CounterType {
  DELTA = 'DELTA',
  GAUGE = 'GAUGE',
  CUMULATIVE = 'CUMULATIVE',
}

export enum CreditType {
  FREE = 'FREE',
  PAID = 'PAID',
  PROMOTIONAL = 'PROMOTIONAL',
}

export enum AdjustmentType {
  DISCOUNT = 'DISCOUNT',
  SURCHARGE = 'SURCHARGE',
}

export enum AdjustmentLevel {
  BILLING_GROUP = 'BILLING_GROUP',
  PROJECT = 'PROJECT',
}

export enum AdjustmentMethod {
  FIXED = 'FIXED',
  RATE = 'RATE',
}

export enum BillingStatus {
  PENDING = 'PENDING',
  PAID = 'PAID',
  OVERDUE = 'OVERDUE',
  CANCELLED = 'CANCELLED',
}

export enum PaymentStatus {
  SUCCESS = 'SUCCESS',
  FAILED = 'FAILED',
  PENDING = 'PENDING',
}

export enum PaymentMethod {
  CREDIT_CARD = 'CREDIT_CARD',
  BANK_TRANSFER = 'BANK_TRANSFER',
  DEBIT_CARD = 'DEBIT_CARD',
  WIRE_TRANSFER = 'WIRE_TRANSFER',
  MOCK = 'MOCK',
}

export enum Currency {
  KRW = 'KRW',
  USD = 'USD',
  EUR = 'EUR',
  JPY = 'JPY',
}

// ============================================================================
// Input Types
// ============================================================================

export interface BillingInput {
  readonly targetDate: Date
  readonly uuid: string
  readonly billingGroupId: string
  readonly usage: ReadonlyArray<UsageInput>
  readonly credits: ReadonlyArray<CreditInput>
  readonly adjustments: ReadonlyArray<AdjustmentInput>
  readonly unpaidAmount?: number
  readonly isOverdue?: boolean
}

export interface UsageInput {
  readonly id: string
  readonly counterName: string
  readonly counterType: CounterType
  readonly counterUnit: string
  readonly counterVolume: number
  readonly resourceId: string
  readonly resourceName?: string
  readonly appKey: string
  readonly projectId?: string
}

export interface CreditInput {
  readonly type: CreditType
  readonly amount: number
  readonly name: string
  readonly expirationDate?: Date
  readonly campaignId?: string
}

export interface AdjustmentInput {
  readonly type: AdjustmentType
  readonly level: AdjustmentLevel
  readonly method: AdjustmentMethod
  readonly value: number
  readonly description: string
  readonly targetProjectId?: string
}

// ============================================================================
// Output Types
// ============================================================================

export interface BillingStatement {
  readonly statementId: string
  readonly uuid: string
  readonly billingGroupId: string
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
  readonly dueDate?: Date
  readonly createdAt?: Date
}

export interface LineItem {
  readonly id: string
  readonly counterName: string
  readonly counterType: CounterType
  readonly unit: string
  readonly quantity: number
  readonly unitPrice: number
  readonly amount: number
  readonly resourceId: string
  readonly resourceName?: string
  readonly projectId?: string
  readonly appKey: string
}

export interface AppliedCredit {
  readonly creditId: string
  readonly type: CreditType
  readonly amountApplied: number
  readonly remainingBalance: number
  readonly campaignId?: string
  readonly campaignName?: string
}

export interface AppliedAdjustment {
  readonly adjustmentId: string
  readonly type: AdjustmentType
  readonly description: string
  readonly amount: number
  readonly level: AdjustmentLevel
  readonly targetId?: string
}

export interface PaymentResult {
  readonly paymentId: string
  readonly status: PaymentStatus
  readonly amount: number
  readonly method: PaymentMethod
  readonly transactionDate: Date
  readonly errorMessage?: string
  readonly receiptUrl?: string
}

// ============================================================================
// Error Types
// ============================================================================

export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  API_ERROR = 'API_ERROR',
  CALCULATION_ERROR = 'CALCULATION_ERROR',
  PAYMENT_ERROR = 'PAYMENT_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export interface CalculationError {
  readonly code: ErrorCode
  readonly message: string
  readonly field?: string
  readonly details?: Readonly<Record<string, unknown>>
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponseHeader {
  readonly isSuccessful: boolean
  readonly resultCode: number
  readonly resultMessage: string
}

export interface ApiSuccessResponse<T> {
  readonly header: ApiResponseHeader
  readonly data: T
}

export interface ApiErrorResponse {
  readonly header: ApiResponseHeader
  readonly error?: CalculationError
}

// ============================================================================
// Type Guards
// ============================================================================

export const isCounterType = (value: unknown): value is CounterType => {
  return Object.values(CounterType).includes(value as CounterType)
}

export const isCreditType = (value: unknown): value is CreditType => {
  return Object.values(CreditType).includes(value as CreditType)
}

export const isAdjustmentType = (value: unknown): value is AdjustmentType => {
  return Object.values(AdjustmentType).includes(value as AdjustmentType)
}

export const isAdjustmentLevel = (value: unknown): value is AdjustmentLevel => {
  return Object.values(AdjustmentLevel).includes(value as AdjustmentLevel)
}

export const isAdjustmentMethod = (value: unknown): value is AdjustmentMethod => {
  return Object.values(AdjustmentMethod).includes(value as AdjustmentMethod)
}

export const isBillingStatus = (value: unknown): value is BillingStatus => {
  return Object.values(BillingStatus).includes(value as BillingStatus)
}

export const isPaymentStatus = (value: unknown): value is PaymentStatus => {
  return Object.values(PaymentStatus).includes(value as PaymentStatus)
}

export const isPaymentMethod = (value: unknown): value is PaymentMethod => {
  return Object.values(PaymentMethod).includes(value as PaymentMethod)
}

export const isCurrency = (value: unknown): value is Currency => {
  return Object.values(Currency).includes(value as Currency)
}

export const isErrorCode = (value: unknown): value is ErrorCode => {
  return Object.values(ErrorCode).includes(value as ErrorCode)
}
