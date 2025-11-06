/**
 * Billing Context - Centralized State Management
 * Type-safe React Context with reducer pattern and memoization
 */

'use client'

import React, { createContext, useContext, useReducer, useMemo } from 'react'
import type { BillingInput, BillingStatement, PaymentResult, CalculationError } from '@/types/billing'

// ============================================================================
// State Types
// ============================================================================

interface BillingState {
  readonly billingInput: BillingInput | null
  readonly calculatedStatement: BillingStatement | null
  readonly paymentResult: PaymentResult | null
  readonly isCalculating: boolean
  readonly isProcessingPayment: boolean
  readonly error: CalculationError | null
}

// ============================================================================
// Action Types
// ============================================================================

type BillingAction =
  | { readonly type: 'SET_BILLING_INPUT'; readonly payload: BillingInput }
  | { readonly type: 'SET_CALCULATED_STATEMENT'; readonly payload: BillingStatement }
  | { readonly type: 'SET_PAYMENT_RESULT'; readonly payload: PaymentResult }
  | { readonly type: 'SET_CALCULATING'; readonly payload: boolean }
  | { readonly type: 'SET_PROCESSING_PAYMENT'; readonly payload: boolean }
  | { readonly type: 'SET_ERROR'; readonly payload: CalculationError | null }
  | { readonly type: 'RESET' }

// ============================================================================
// Context Value Types
// ============================================================================

interface BillingActions {
  readonly setBillingInput: (input: BillingInput) => void
  readonly setCalculatedStatement: (statement: BillingStatement) => void
  readonly setPaymentResult: (result: PaymentResult) => void
  readonly setCalculating: (isCalculating: boolean) => void
  readonly setProcessingPayment: (isProcessing: boolean) => void
  readonly setError: (error: CalculationError | null) => void
  readonly reset: () => void
}

interface BillingContextValue {
  readonly state: BillingState
  readonly actions: BillingActions
}

// ============================================================================
// Initial State
// ============================================================================

const INITIAL_STATE: BillingState = {
  billingInput: null,
  calculatedStatement: null,
  paymentResult: null,
  isCalculating: false,
  isProcessingPayment: false,
  error: null,
}

// ============================================================================
// Reducer
// ============================================================================

const billingReducer = (state: BillingState, action: BillingAction): BillingState => {
  switch (action.type) {
    case 'SET_BILLING_INPUT':
      return {
        ...state,
        billingInput: action.payload,
        error: null,
      }

    case 'SET_CALCULATED_STATEMENT':
      return {
        ...state,
        calculatedStatement: action.payload,
        error: null,
      }

    case 'SET_PAYMENT_RESULT':
      return {
        ...state,
        paymentResult: action.payload,
      }

    case 'SET_CALCULATING':
      return {
        ...state,
        isCalculating: action.payload,
      }

    case 'SET_PROCESSING_PAYMENT':
      return {
        ...state,
        isProcessingPayment: action.payload,
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isCalculating: false,
        isProcessingPayment: false,
      }

    case 'RESET':
      return INITIAL_STATE

    default:
      return state
  }
}

// ============================================================================
// Context Creation
// ============================================================================

const BillingContext = createContext<BillingContextValue | undefined>(undefined)
BillingContext.displayName = 'BillingContext'

// ============================================================================
// Provider Component
// ============================================================================

interface BillingProviderProps {
  readonly children: React.ReactNode
}

export const BillingProvider: React.FC<BillingProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(billingReducer, INITIAL_STATE)

  // Memoized actions to prevent unnecessary re-renders
  const actions: BillingActions = useMemo(
    () => ({
      setBillingInput: (input: BillingInput) => {
        dispatch({ type: 'SET_BILLING_INPUT', payload: input })
      },

      setCalculatedStatement: (statement: BillingStatement) => {
        dispatch({ type: 'SET_CALCULATED_STATEMENT', payload: statement })
      },

      setPaymentResult: (result: PaymentResult) => {
        dispatch({ type: 'SET_PAYMENT_RESULT', payload: result })
      },

      setCalculating: (isCalculating: boolean) => {
        dispatch({ type: 'SET_CALCULATING', payload: isCalculating })
      },

      setProcessingPayment: (isProcessing: boolean) => {
        dispatch({ type: 'SET_PROCESSING_PAYMENT', payload: isProcessing })
      },

      setError: (error: CalculationError | null) => {
        dispatch({ type: 'SET_ERROR', payload: error })
      },

      reset: () => {
        dispatch({ type: 'RESET' })
      },
    }),
    []
  )

  // Memoized context value
  const contextValue: BillingContextValue = useMemo(
    () => ({
      state,
      actions,
    }),
    [state, actions]
  )

  return <BillingContext.Provider value={contextValue}>{children}</BillingContext.Provider>
}

// ============================================================================
// Custom Hooks
// ============================================================================

/**
 * Main hook to access billing context
 * @throws Error if used outside BillingProvider
 */
export const useBilling = (): BillingContextValue => {
  const context = useContext(BillingContext)

  if (context === undefined) {
    throw new Error('useBilling must be used within BillingProvider')
  }

  return context
}

/**
 * Selector hook for billing input
 */
export const useBillingInput = (): BillingInput | null => {
  const { state } = useBilling()
  return state.billingInput
}

/**
 * Selector hook for calculated statement
 */
export const useCalculatedStatement = (): BillingStatement | null => {
  const { state } = useBilling()
  return state.calculatedStatement
}

/**
 * Selector hook for payment result
 */
export const usePaymentResult = (): PaymentResult | null => {
  const { state } = useBilling()
  return state.paymentResult
}

/**
 * Selector hook for error state
 */
export const useBillingError = (): CalculationError | null => {
  const { state } = useBilling()
  return state.error
}

/**
 * Selector hook for loading states
 */
export const useBillingLoading = (): {
  readonly isCalculating: boolean
  readonly isProcessingPayment: boolean
} => {
  const { state } = useBilling()
  // Return simple object - no useMemo needed for primitive values
  return {
      isCalculating: state.isCalculating,
      isProcessingPayment: state.isProcessingPayment,
  }
}

/**
 * Selector hook for actions
 * Returns memoized actions object
 */
export const useBillingActions = (): BillingActions => {
  const { actions } = useBilling()
  return actions
}
