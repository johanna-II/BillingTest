/**
 * Billing Context - Centralized state management for billing calculator
 * Follows: Context API for state management, avoiding prop drilling
 */

'use client'

import React, { createContext, useContext, useReducer, useCallback, useMemo } from 'react'
import type { BillingInput, BillingStatement, PaymentResult, CalculationError } from '@/types/billing'

// State shape
interface BillingState {
  billingInput: BillingInput | null
  calculatedStatement: BillingStatement | null
  paymentResult: PaymentResult | null
  isCalculating: boolean
  isProcessingPayment: boolean
  error: CalculationError | null
}

// Actions
type BillingAction =
  | { type: 'SET_BILLING_INPUT'; payload: BillingInput }
  | { type: 'SET_CALCULATED_STATEMENT'; payload: BillingStatement }
  | { type: 'SET_PAYMENT_RESULT'; payload: PaymentResult }
  | { type: 'SET_CALCULATING'; payload: boolean }
  | { type: 'SET_PROCESSING_PAYMENT'; payload: boolean }
  | { type: 'SET_ERROR'; payload: CalculationError | null }
  | { type: 'RESET' }

// Context value shape
interface BillingContextValue {
  state: BillingState
  actions: {
    setBillingInput: (input: BillingInput) => void
    setCalculatedStatement: (statement: BillingStatement) => void
    setPaymentResult: (result: PaymentResult) => void
    setCalculating: (isCalculating: boolean) => void
    setProcessingPayment: (isProcessing: boolean) => void
    setError: (error: CalculationError | null) => void
    reset: () => void
  }
}

// Initial state
const initialState: BillingState = {
  billingInput: null,
  calculatedStatement: null,
  paymentResult: null,
  isCalculating: false,
  isProcessingPayment: false,
  error: null,
}

// Reducer
const billingReducer = (state: BillingState, action: BillingAction): BillingState => {
  switch (action.type) {
    case 'SET_BILLING_INPUT':
      return { ...state, billingInput: action.payload, error: null }

    case 'SET_CALCULATED_STATEMENT':
      return { ...state, calculatedStatement: action.payload, error: null }

    case 'SET_PAYMENT_RESULT':
      return { ...state, paymentResult: action.payload }

    case 'SET_CALCULATING':
      return { ...state, isCalculating: action.payload }

    case 'SET_PROCESSING_PAYMENT':
      return { ...state, isProcessingPayment: action.payload }

    case 'SET_ERROR':
      return { ...state, error: action.payload, isCalculating: false, isProcessingPayment: false }

    case 'RESET':
      return initialState

    default:
      return state
  }
}

// Create context
const BillingContext = createContext<BillingContextValue | undefined>(undefined)

// Provider props
interface BillingProviderProps {
  children: React.ReactNode
}

// Provider component
export const BillingProvider: React.FC<BillingProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(billingReducer, initialState)

  // Memoized actions
  const actions = useMemo(
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
  const contextValue = useMemo(
    () => ({
      state,
      actions,
    }),
    [state, actions]
  )

  return (
    <BillingContext.Provider value={contextValue}>
      {children}
    </BillingContext.Provider>
  )
}

// Custom hook for using billing context
export const useBilling = (): BillingContextValue => {
  const context = useContext(BillingContext)

  if (!context) {
    throw new Error('useBilling must be used within BillingProvider')
  }

  return context
}

// Selector hooks for optimized re-renders
export const useBillingInput = (): BillingInput | null => {
  const { state } = useBilling()
  return state.billingInput
}

export const useCalculatedStatement = (): BillingStatement | null => {
  const { state } = useBilling()
  return state.calculatedStatement
}

export const usePaymentResult = (): PaymentResult | null => {
  const { state } = useBilling()
  return state.paymentResult
}

export const useBillingError = (): CalculationError | null => {
  const { state } = useBilling()
  return state.error
}

export const useBillingLoading = (): { isCalculating: boolean; isProcessingPayment: boolean } => {
  const { state } = useBilling()
  return {
    isCalculating: state.isCalculating,
    isProcessingPayment: state.isProcessingPayment,
  }
}
