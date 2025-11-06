/**
 * Form Default Values
 * Centralized default values for form inputs
 *
 * Note: Uses flexible types (not as const) to allow useState to work correctly
 * with setState functions that accept SetStateAction<T>
 */

// ============================================================================
// Billing Input Form Defaults
// ============================================================================

export type FormDefaultsType = {
  readonly UUID: string
  readonly BILLING_GROUP_ID: string
  readonly UNPAID_AMOUNT: number
  readonly IS_OVERDUE: boolean
}

/**
 * Billing Form Default Values
 * Flexible types to ensure compatibility with React setState
 */
export const BILLING_FORM_DEFAULTS: FormDefaultsType = {
  UUID: 'test-uuid-001',
  BILLING_GROUP_ID: 'bg-kr-test',
  UNPAID_AMOUNT: 0,
  IS_OVERDUE: false,
}
