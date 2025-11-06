/**
 * Home Page - Billing Calculator
 * KINFOLK inspired minimal design
 */

'use client'

import React, { useState } from 'react'
import BillingInputForm from '@/components/BillingInputForm'
import StatementDisplay from '@/components/StatementDisplay'
import PaymentSection from '@/components/PaymentSection'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import HistoryPanel from '@/components/HistoryPanel'
import { useBilling } from '@/contexts/BillingContext'
import { useHistoryStore } from '@/stores/historyStore'

export default function HomePage(): JSX.Element {
  const { state, actions } = useBilling()
  const { getEntry, addEntry } = useHistoryStore()
  const [activeSection, setActiveSection] = useState<'input' | 'statement' | 'payment'>('input')

  // Track last saved entry to prevent duplicates
  const lastSavedRef = React.useRef<string | undefined>(undefined)

  const handleLoadHistoryEntry = (entryId: string): void => {
    const entry = getEntry(entryId)
    if (entry) {
      actions.setBillingInput(entry.input)
      if (entry.statement) {
        actions.setCalculatedStatement(entry.statement)
        setActiveSection('statement')
      } else {
        setActiveSection('input')
      }
    }
  }

  // Save to history when calculation completes
  // History tracks calculation results only; payment state is separate
  // Deduplication prevents duplicate entries from re-renders
  React.useEffect(() => {
    if (!state.billingInput || !state.calculatedStatement) {
      return
    }

    // Create unique key for deduplication (input + statement only)
    const entryKey = JSON.stringify({
      input: state.billingInput,
      statement: state.calculatedStatement,
    })

    // Skip if already saved
    if (lastSavedRef.current === entryKey) {
      return
    }

    // Save calculation to history
    // Note: payment is included but doesn't trigger re-saves
    lastSavedRef.current = entryKey
    addEntry({
      input: state.billingInput,
      statement: state.calculatedStatement,
      payment: state.paymentResult,
    })
  }, [state.billingInput, state.calculatedStatement, addEntry, state.paymentResult])

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="kinfolk-section bg-white">
          <div className="kinfolk-container text-center">
            <h1 className="kinfolk-heading mb-4 fade-in">
              Billing Calculator
            </h1>
            <p className="kinfolk-subheading fade-in" style={{ animationDelay: '0.1s' }}>
              Calculate · Test · Verify
            </p>
            <p className="kinfolk-body max-w-2xl mx-auto fade-in" style={{ animationDelay: '0.2s' }}>
              Calculate billing with precision. Test scenarios with credits, adjustments,
              and late fees. Verify payment processing through mock APIs.
            </p>
          </div>
        </section>

        <div className="kinfolk-divider" />

        {/* Progress Indicator */}
        <section className="kinfolk-container">
          <div className="flex items-center justify-center space-x-2 md:space-x-4 mb-12">
            <StepIndicator
              number={1}
              label="Input"
              active={activeSection === 'input'}
              completed={!!state.billingInput}
              onClick={() => setActiveSection('input')}
            />
            <div className="w-8 h-px bg-kinfolk-gray-300" />
            <StepIndicator
              number={2}
              label="Statement"
              active={activeSection === 'statement'}
              completed={!!state.calculatedStatement}
              onClick={() => setActiveSection('statement')}
              disabled={!state.calculatedStatement}
            />
            <div className="w-8 h-px bg-kinfolk-gray-300" />
            <StepIndicator
              number={3}
              label="Payment"
              active={activeSection === 'payment'}
              completed={!!state.paymentResult}
              onClick={() => setActiveSection('payment')}
              disabled={!state.calculatedStatement}
            />
          </div>
        </section>

        {/* Main Content */}
        <section className="kinfolk-container pb-24">
          {activeSection === 'input' && <BillingInputForm onComplete={() => setActiveSection('statement')} />}
          {activeSection === 'statement' && <StatementDisplay onProceedToPayment={() => setActiveSection('payment')} />}
          {activeSection === 'payment' && <PaymentSection onBackToInput={() => setActiveSection('input')} />}
        </section>

        {/* History Panel */}
        <HistoryPanel onLoadEntry={handleLoadHistoryEntry} />
      </main>

      <Footer />
    </div>
  )
}

// Step Indicator Component
interface StepIndicatorProps {
  readonly number: number
  readonly label: string
  readonly active: boolean
  readonly completed: boolean
  readonly disabled?: boolean
  readonly onClick: () => void
}

function StepIndicator({
  number,
  label,
  active,
  completed,
  disabled = false,
  onClick
}: StepIndicatorProps): JSX.Element {
  // Calculate step circle styles based on state
  const getStepCircleStyles = (): string => {
    if (completed) {
      return 'bg-kinfolk-gray-900 text-white'
    }
    if (active) {
      return 'border-2 border-kinfolk-gray-900 text-kinfolk-gray-900'
    }
    return 'border border-kinfolk-gray-300 text-kinfolk-gray-400'
  }

  // Calculate button styles to avoid opacity class conflicts
  const getButtonStyles = (): string => {
    if (disabled) {
      return 'opacity-30 cursor-not-allowed'
    }
    if (active) {
      return 'opacity-100 cursor-pointer hover:opacity-100'
    }
    return 'opacity-60 cursor-pointer hover:opacity-100'
  }

  const labelColor = active ? 'text-kinfolk-gray-900' : 'text-kinfolk-gray-500'

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex flex-col items-center space-y-2 transition-opacity duration-300
        ${getButtonStyles()}
      `}
    >
      <div
        className={`
          w-12 h-12 rounded-full flex items-center justify-center
          text-sm font-medium transition-colors duration-300
          ${getStepCircleStyles()}
        `}
      >
        {completed ? '✓' : number}
      </div>
      <span className={`text-xs uppercase tracking-widest ${labelColor}`}>
        {label}
      </span>
    </button>
  )
}
